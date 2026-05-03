import json
import asyncio
from typing import List, Dict
import re
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from database import get_db_connection, init_db
from models import QuestionResponse
from config import CHUNK_SIZE, CHUNK_OVERLAP


load_dotenv()


class LLMService:
    """大模型服务类"""

    def __init__(self):
        pass

    def get_ai_config(self) -> dict:
        """获取 AI 配置"""
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_config ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        conn.close()

        if not config:
            raise ValueError("请先配置 AI API")

        return dict(config)

    def _create_chat_model(self, config: dict) -> ChatOpenAI:
        """创建聊天模型实例"""
        api_url = config.get("api_url", "")
        api_key = config.get("api_key", "")
        model_name = config.get("model_name", "gpt-3.5-turbo")

        if "deepseek" in model_name.lower():
            load_dotenv()
            DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or api_key
            return ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=DEEPSEEK_API_KEY,
                openai_api_base="https://api.deepseek.com",
                temperature=0.3
            )
        elif api_url and api_url != "https://api.openai.com":
            return ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=api_url.rstrip("/") + "/v1",
                temperature=0.3
            )
        else:
            return ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                temperature=0.3
            )

    async def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """调用大模型"""
        config = self.get_ai_config()
        chat = self._create_chat_model(config)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chat.invoke(messages)
        )

        return response.content


llm_service = LLMService()


SYSTEM_PROMPT = """你是一个专业的题目解析专家。"""

PARSE_PROMPT = """你是一个专业的题目解析专家。请从以下文档内容中提取所有题目及其对应的答案和解析。

文档内容：
{chunk_content}

请严格按以下 JSON 格式返回，只返回 JSON，不要其他内容：
{{"questions": [
  {{"type": "choice", "content": "题目干（不含选项）", "options": ["A. 选项内容", "B. 选项内容", "C. 选项内容", "D. 选项内容"], "answer": "正确答案字母如A或ABC", "explanation": "解析内容"}},
  {{"type": "true_false", "content": "判断题题目", "options": ["A. 正确", "B. 错误"], "answer": "A或B", "explanation": "解析"}},
  {{"type": "short_answer", "content": "简答题题目", "options": null, "answer": "答案", "explanation": "解析"}},
  {{"type": "case_analysis", "content": "案例分析题题目", "options": null, "answer": "答案", "explanation": "解析"}}
]}}

重要规则：
1. 选择题的 content 只包含题目干
2. 选择题的 options 必须包含 A B C D 四个选项
3. 判断题 type 用 "true_false"
4. 答案必须是选项字母，如 A、B、C、D 或 AB、ABC 等组合
5. 只返回 JSON，不要任何解释说明文字"""


def parse_json_response(response_text: str) -> dict:
    """解析 AI 返回的 JSON"""
    try:
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group()
            try:
                result = json.loads(json_str)
                if isinstance(result, dict):
                    return result
                else:
                    return {}
            except json.JSONDecodeError:
                return fix_incomplete_json(json_str)
        else:
            return json.loads(text)
    except Exception as e:
        print(f"JSON 解析异常: {e}")
        return {}


def fix_incomplete_json(json_str: str) -> dict:
    """尝试修复不完整的 JSON"""
    if '"questions": [' in json_str:
        start = json_str.find('"questions": [')
        search_str = json_str[start + 13:]
        objects = []
        depth = 0
        current_obj = ""
        in_string = False
        escape_next = False

        for char in search_str:
            current_obj += char
            if escape_next:
                escape_next = False
                continue
            if char == '\\' and in_string:
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(current_obj.strip())
                        if obj.get("content"):
                            objects.append(obj)
                    except:
                        pass
                    current_obj = ""

        if objects:
            return {"questions": objects}

    return {"questions": []}


def parse_questions_from_response(response_text: str) -> List[QuestionResponse]:
    """解析 AI 返回的题目 JSON"""
    questions = []
    data = parse_json_response(response_text)

    if not isinstance(data, dict):
        return questions

    for q in data.get("questions", []):
        if not isinstance(q, dict):
            continue
        content = q.get("content")
        if not content:
            continue
        questions.append(QuestionResponse(
            type=q.get("type", "short_answer"),
            content=content,
            options=q.get("options"),
            answer=q.get("answer") or "未找到",
            explanation=q.get("explanation")
        ))

    return questions


async def parse_document(file_path: str, document_id: int, question_bank_id: int = None, progress_callback=None) -> dict:
    """使用 AI 解析文档"""
    from services.document_parser import chunk_document

    print(f"正在加载并分块文档: {file_path}")

    doc_chunks = chunk_document(file_path, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    print(f"文档分为 {len(doc_chunks)} 个块")

    all_questions = []

    for i, chunk in enumerate(doc_chunks):
        print(f"正在处理第 {i+1}/{len(doc_chunks)} 块...")

        if progress_callback:
            progress_callback(document_id, {
                "status": "processing",
                "progress": int((i + 1) / len(doc_chunks) * 100),
                "current": i + 1,
                "total": len(doc_chunks)
            })

        prompt = PARSE_PROMPT.replace("{chunk_content}", chunk["content"])

        try:
            response = await llm_service.call_llm(prompt, SYSTEM_PROMPT)
            questions = parse_questions_from_response(response)
            all_questions.extend(questions)
            print(f"第 {i+1} 块提取到 {len(questions)} 道题目")

        except Exception as e:
            print(f"第 {i+1} 块处理失败: {e}")
            continue

        await asyncio.sleep(1)

    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    saved_count = 0
    for q in all_questions:
        options_json = json.dumps(q.options) if q.options else None
        cursor.execute(
            """INSERT INTO questions (question_bank_id, document_id, question_type, content, options, answer, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (question_bank_id, document_id, q.type, q.content, options_json, q.answer, q.explanation)
        )
        saved_count += 1

    cursor.execute(
        "UPDATE documents SET status = 'completed', total_questions = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (saved_count, document_id)
    )

    conn.commit()
    conn.close()

    print(f"解析完成！共提取 {saved_count} 道题目")

    return {
        "total_chunks": len(doc_chunks),
        "total_questions": saved_count
    }


async def parse_document_two_pass(file_path: str, document_id: int, question_bank_id: int = None, progress_callback=None) -> dict:
    return await parse_document(file_path, document_id, question_bank_id, progress_callback)


async def parse_document_with_ai(file_path: str, document_id: int, question_bank_id: int = None, progress_callback=None) -> dict:
    return await parse_document(file_path, document_id, question_bank_id, progress_callback)


async def call_ai_api(api_url: str, api_key: str, model: str, content: str, timeout: int = 120) -> str:
    """兼容旧接口"""
    config = {"api_url": api_url, "api_key": api_key, "model_name": model}
    chat = llm_service._create_chat_model(config)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: chat.invoke([HumanMessage(content=content)])
    )
    return response.content
