from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json

from routers import documents, questions, ai_config, practice, question_banks
from database import init_db, migrate_db
from services.ai_parser import parse_document

# 解析进度存储
parse_progress = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate_db()
    init_db()
    print("数据库初始化完成")
    yield
    print("应用关闭")

app = FastAPI(
    title="AI 刷题系统",
    description="上传文档，AI 自动解析题目",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question_banks.router)
app.include_router(documents.router)
app.include_router(questions.router)
app.include_router(ai_config.router)
app.include_router(practice.router)

@app.get("/")
async def root():
    return {"message": "AI 刷题系统 API", "version": "1.0.0"}

@app.post("/api/documents/{doc_id}/parse")
async def parse_document_endpoint(doc_id: int):
    from database import get_db_connection
    from services.ai_parser import parse_document

    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc = dict(doc)

    if doc["status"] == "processing":
        raise HTTPException(status_code=400, detail="文档正在解析中")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET status = 'processing' WHERE id = ?",
        (doc_id,)
    )
    conn.commit()
    conn.close()

    parse_progress[doc_id] = {"status": "processing", "progress": 0, "current": 0, "total": 0, "questions": 0}

    async def run_parse():
        def update_progress(doc_id, info):
            parse_progress[doc_id] = info

        try:
            result = await parse_document(
                doc["file_path"], doc_id, doc["question_bank_id"],
                update_progress
            )
            parse_progress[doc_id] = {"status": "completed", "progress": 100, "questions": result.get("total_questions", 0)}
        except Exception as e:
            parse_progress[doc_id] = {"status": "failed", "error": str(e)}

    asyncio.create_task(run_parse())

    return {"message": "解析任务已启动", "document_id": doc_id}

@app.get("/api/documents/{doc_id}/progress")
async def get_parse_progress(doc_id: int):
    async def event_stream():
        last_progress = -1
        while True:
            progress = parse_progress.get(doc_id)
            if progress:
                if last_progress != progress.get("progress"):
                    last_progress = progress.get("progress", 0)
                    yield f"data: {json.dumps(progress)}\n\n"
                if progress.get("status") in ["completed", "failed"]:
                    break
            await asyncio.sleep(1)
        yield f"data: {json.dumps({'status': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
