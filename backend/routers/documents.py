from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import os
import shutil
from datetime import datetime

from database import get_db_connection, init_db
from models import Document, DocumentCreate

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@router.post("/", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    question_bank_id: Optional[int] = Form(None)
):
    """上传文档"""
    init_db()

    if question_bank_id is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM question_banks ORDER BY id ASC LIMIT 1")
        result = cursor.fetchone()
        if result:
            question_bank_id = result[0]
        conn.close()

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (question_bank_id, filename, file_path, status) VALUES (?, ?, ?, ?)",
        (question_bank_id, file.filename, file_path, "pending")
    )
    doc_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = dict(cursor.fetchone())
    conn.close()

    return Document(**doc)

@router.get("/", response_model=List[Document])
async def get_documents(question_bank_id: Optional[int] = None):
    """获取文档列表"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if question_bank_id:
        cursor.execute(
            "SELECT * FROM documents WHERE question_bank_id = ? ORDER BY created_at DESC",
            (question_bank_id,)
        )
    else:
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")

    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return [Document(**doc) for doc in docs]

@router.get("/{doc_id}", response_model=Document)
async def get_document(doc_id: int):
    """获取文档详情"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return Document(**dict(doc))

@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    """删除文档"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = doc["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    return {"message": "删除成功"}

@router.patch("/{doc_id}/status")
async def update_document_status(doc_id: int, status: str, total_questions: int = None):
    """更新文档状态"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if total_questions is not None:
        cursor.execute(
            "UPDATE documents SET status = ?, total_questions = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, total_questions, doc_id)
        )
    else:
        cursor.execute(
            "UPDATE documents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, doc_id)
        )

    conn.commit()
    conn.close()

    return {"message": "更新成功"}
