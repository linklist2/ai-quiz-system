from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json

from database import get_db_connection, init_db
from models import Question, QuestionCreate

router = APIRouter(prefix="/api/questions", tags=["题目管理"])

@router.get("/", response_model=List[Question])
async def get_questions(
    question_bank_id: Optional[int] = None,
    document_id: Optional[int] = None,
    question_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 5000
):
    """获取题目列表"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM questions WHERE 1=1"
    params = []

    if question_bank_id:
        query += " AND question_bank_id = ?"
        params.append(question_bank_id)

    if document_id:
        query += " AND document_id = ?"
        params.append(document_id)

    if question_type:
        query += " AND question_type = ?"
        params.append(question_type)

    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor.execute(query, params)
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return [Question(**q) for q in questions]

@router.get("/count")
async def get_questions_count(
    question_bank_id: Optional[int] = None,
    document_id: Optional[int] = None,
    question_type: Optional[str] = None
):
    """获取题目数量"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM questions WHERE 1=1"
    params = []

    if question_bank_id:
        query += " AND question_bank_id = ?"
        params.append(question_bank_id)

    if document_id:
        query += " AND document_id = ?"
        params.append(document_id)

    if question_type:
        query += " AND question_type = ?"
        params.append(question_type)

    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()

    return {"count": count}

@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: int):
    """获取题目详情"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    question = cursor.fetchone()
    conn.close()

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return Question(**dict(question))

@router.post("/", response_model=Question)
async def create_question(question: QuestionCreate):
    """创建题目"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    question_bank_id = question.question_bank_id
    if question_bank_id is None and question.document_id:
        cursor.execute("SELECT question_bank_id FROM documents WHERE id = ?", (question.document_id,))
        result = cursor.fetchone()
        if result:
            question_bank_id = result[0]

    cursor.execute(
        """INSERT INTO questions (question_bank_id, document_id, question_type, content, options, answer, explanation)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            question_bank_id,
            question.document_id,
            question.question_type,
            question.content,
            question.options,
            question.answer,
            question.explanation
        )
    )
    q_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM questions WHERE id = ?", (q_id,))
    q = dict(cursor.fetchone())
    conn.close()

    return Question(**q)

@router.delete("/{question_id}")
async def delete_question(question_id: int):
    """删除题目"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="题目不存在")

    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

    return {"message": "删除成功"}

@router.put("/{question_id}", response_model=Question)
async def update_question(question_id: int, question: QuestionCreate):
    """更新题目"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="题目不存在")

    options_json = question.options
    if isinstance(options_json, list):
        options_json = json.dumps(options_json)

    cursor.execute(
        """UPDATE questions SET question_type = ?, content = ?, options = ?, answer = ?, explanation = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (question.question_type, question.content, options_json, question.answer, question.explanation, question_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    q = dict(cursor.fetchone())
    conn.close()

    return Question(**q)
