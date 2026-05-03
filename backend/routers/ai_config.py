from fastapi import APIRouter, HTTPException
from typing import List

from database import get_db_connection, init_db
from models import AIConfig, AIConfigCreate

router = APIRouter(prefix="/api/ai", tags=["AI配置"])

@router.get("/config", response_model=AIConfig)
async def get_ai_config():
    """获取当前 AI 配置"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_config ORDER BY id DESC LIMIT 1")
    config = cursor.fetchone()
    conn.close()

    if not config:
        return AIConfig(
            id=0,
            name="默认配置",
            api_url="",
            api_key="",
            model_name="gpt-3.5-turbo"
        )
    return AIConfig(**dict(config))

@router.post("/config", response_model=AIConfig)
async def save_ai_config(config: AIConfigCreate):
    """保存 AI 配置"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ai_config")
    cursor.execute(
        """INSERT INTO ai_config (name, api_url, api_key, model_name)
           VALUES (?, ?, ?, ?)""",
        (config.name, config.api_url, config.api_key, config.model_name)
    )
    config_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM ai_config WHERE id = ?", (config_id,))
    saved_config = dict(cursor.fetchone())
    conn.close()

    return AIConfig(**saved_config)

@router.post("/config/test")
async def test_ai_connection(config: AIConfigCreate):
    """测试 AI 连接"""
    import aiohttp

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }

    api_url = config.api_url
    if "/v1/chat/completions" not in api_url:
        api_url = api_url.rstrip("/") + "/v1/chat/completions"

    payload = {
        "model": config.model_name,
        "messages": [
            {"role": "user", "content": "你好，请回复 OK"}
        ],
        "max_tokens": 10
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    message = result["choices"][0]["message"]
                    content = message.get("content") or message.get("reasoning_content") or str(message)
                    return {"status": "success", "message": f"连接成功，AI 回复: {content[:50]}"}
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"API 返回错误: {error_text}")
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")
