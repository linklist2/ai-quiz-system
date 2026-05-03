import sqlite3
from datetime import datetime
from config import DATABASE_URL

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # AI 配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 题库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 文档表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_bank_id INTEGER,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_questions INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_bank_id) REFERENCES question_banks(id) ON DELETE SET NULL
        )
    """)

    # 题目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_bank_id INTEGER,
            document_id INTEGER,
            question_type TEXT NOT NULL,
            content TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            explanation TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_bank_id) REFERENCES question_banks(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

def migrate_db():
    """迁移现有数据库，添加题库相关字段"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(documents)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'question_bank_id' not in columns:
        print("迁移文档表...")
        cursor.execute("ALTER TABLE documents ADD COLUMN question_bank_id INTEGER")
        cursor.execute("ALTER TABLE documents ADD COLUMN name TEXT")

    cursor.execute("PRAGMA table_info(questions)")
    q_columns = [col[1] for col in cursor.fetchall()]

    if 'question_bank_id' not in q_columns:
        print("迁移题目表...")
        cursor.execute("ALTER TABLE questions ADD COLUMN question_bank_id INTEGER")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM question_banks")
    if cursor.fetchone()[0] == 0:
        print("创建默认题库...")
        cursor.execute("INSERT INTO question_banks (name, description) VALUES (?, ?)", ("默认题库", "系统默认题库"))

    conn.commit()
    conn.close()
    print("数据库迁移完成")

if __name__ == "__main__":
    migrate_db()
    print("数据库初始化完成")
