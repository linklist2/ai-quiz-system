from fastapi import APIRouter, HTTPException
from typing import List

from database import get_db_connection, init_db
from models import QuestionBank, QuestionBankCreate, QuestionBankWithStats

router = APIRouter(prefix="/api/question-banks", tags=["题库管理"])

@router.get("/", response_model=List[QuestionBankWithStats])
async def get_question_banks():
    """获取所有题库（带统计信息）"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM question_banks ORDER BY created_at DESC")
    banks = [dict(row) for row in cursor.fetchall()]

    result = []
    for bank in banks:
        cursor.execute("SELECT COUNT(*) FROM documents WHERE question_bank_id = ?", (bank['id'],))
        bank['document_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE question_bank_id = ?", (bank['id'],))
        bank['question_count'] = cursor.fetchone()[0]

        result.append(QuestionBankWithStats(**bank))

    conn.close()
    return result

@router.get("/{bank_id}", response_model=QuestionBankWithStats)
async def get_question_bank(bank_id: int):
    """获取单个题库"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM question_banks WHERE id = ?", (bank_id,))
    bank = cursor.fetchone()

    if not bank:
        conn.close()
        raise HTTPException(status_code=404, detail="题库不存在")

    bank = dict(bank)

    cursor.execute("SELECT COUNT(*) FROM documents WHERE question_bank_id = ?", (bank_id,))
    bank['document_count'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions WHERE question_bank_id = ?", (bank_id,))
    bank['question_count'] = cursor.fetchone()[0]

    conn.close()
    return QuestionBankWithStats(**bank)

@router.post("/", response_model=QuestionBank)
async def create_question_bank(bank: QuestionBankCreate):
    """创建题库"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO question_banks (name, description) VALUES (?, ?)",
        (bank.name, bank.description)
    )
    bank_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM question_banks WHERE id = ?", (bank_id,))
    result = dict(cursor.fetchone())
    conn.close()

    return QuestionBank(**result)

@router.put("/{bank_id}", response_model=QuestionBank)
async def update_question_bank(bank_id: int, bank: QuestionBankCreate):
    """更新题库"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM question_banks WHERE id = ?", (bank_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="题库不存在")

    cursor.execute(
        "UPDATE question_banks SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (bank.name, bank.description, bank_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM question_banks WHERE id = ?", (bank_id,))
    result = dict(cursor.fetchone())
    conn.close()

    return QuestionBank(**result)

@router.delete("/{bank_id}")
async def delete_question_bank(bank_id: int):
    """删除题库（级联删除题目）"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM question_banks WHERE id = ?", (bank_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="题库不存在")

    cursor.execute("DELETE FROM questions WHERE question_bank_id = ?", (bank_id,))
    cursor.execute("DELETE FROM question_banks WHERE id = ?", (bank_id,))
    conn.commit()
    conn.close()

    return {"message": "删除成功"}
