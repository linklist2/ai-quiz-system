from fastapi import APIRouter, HTTPException
import random
import json
from typing import Optional

from database import get_db_connection, init_db
from models import AnswerCheckRequest, AnswerCheckResponse

router = APIRouter(prefix="/api/practice", tags=["刷题"])

@router.get("/random")
async def get_random_question(question_bank_id: Optional[int] = None):
    """获取随机题目"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if question_bank_id:
        cursor.execute(
            "SELECT * FROM questions WHERE question_bank_id = ? ORDER BY RANDOM() LIMIT 1",
            (question_bank_id,)
        )
    else:
        cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")

    question = cursor.fetchone()
    conn.close()

    if not question:
        raise HTTPException(status_code=404, detail="暂无题目")

    q = dict(question)
    if q["options"]:
        q["options"] = json.loads(q["options"])
    return q

@router.get("/count")
async def get_question_count(question_bank_id: Optional[int] = None):
    """获取题目数量"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if question_bank_id:
        cursor.execute(
            "SELECT COUNT(*) FROM questions WHERE question_bank_id = ?",
            (question_bank_id,)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM questions")

    count = cursor.fetchone()[0]
    conn.close()

    return {"count": count}

@router.post("/check", response_model=AnswerCheckResponse)
async def check_answer(request: AnswerCheckRequest):
    """检查答案"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM questions WHERE id = ?",
        (request.question_id,)
    )
    question = cursor.fetchone()
    conn.close()

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    q = dict(question)
    correct_answer = q["answer"].strip().upper()
    user_answer = request.user_answer.strip().upper()

    is_correct = correct_answer == user_answer or correct_answer in user_answer

    return AnswerCheckResponse(
        correct=is_correct,
        correct_answer=q["answer"],
        explanation=q.get("explanation")
    )
