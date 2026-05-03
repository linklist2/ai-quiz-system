from database import get_db_connection, init_db
from models import Question, QuestionCreate
import json
from typing import List, Optional


class QuestionService:
    @staticmethod
    def get_questions(
        document_id: Optional[int] = None,
        question_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Question]:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)

        if question_type:
            query += " AND question_type = ?"
            params.append(question_type)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, params)
        questions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return [Question(**q) for q in questions]

    @staticmethod
    def get_question_by_id(question_id: int) -> Optional[Question]:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()
        conn.close()

        if question:
            return Question(**dict(question))
        return None

    @staticmethod
    def create_question(question: QuestionCreate) -> Question:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO questions (document_id, question_type, content, options, answer, explanation)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
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

    @staticmethod
    def delete_question(question_id: int) -> bool:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_random_question() -> Optional[Question]:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
        question = cursor.fetchone()
        conn.close()

        if question:
            return Question(**dict(question))
        return None

    @staticmethod
    def check_answer(question_id: int, user_answer: str) -> dict:
        question = QuestionService.get_question_by_id(question_id)
        if not question:
            return None

        correct_answer = question.answer.strip().upper()
        user_answer = user_answer.strip().upper()

        is_correct = correct_answer == user_answer or correct_answer in user_answer

        return {
            "correct": is_correct,
            "correct_answer": question.answer,
            "explanation": question.explanation
        }
