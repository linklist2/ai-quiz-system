from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AIConfigBase(BaseModel):
    name: str
    api_url: str
    api_key: str
    model_name: str

class AIConfigCreate(AIConfigBase):
    pass

class AIConfig(AIConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionBankBase(BaseModel):
    name: str
    description: Optional[str] = None

class QuestionBankCreate(QuestionBankBase):
    pass

class QuestionBank(QuestionBankBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionBankWithStats(QuestionBank):
    document_count: int = 0
    question_count: int = 0

class DocumentBase(BaseModel):
    filename: str
    file_path: str

class DocumentCreate(DocumentBase):
    question_bank_id: Optional[int] = None

class Document(DocumentBase):
    id: int
    question_bank_id: Optional[int]
    status: str
    total_questions: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_type: str
    content: str
    options: Optional[str] = None
    answer: str
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    document_id: Optional[int] = None
    question_bank_id: Optional[int] = None

class Question(QuestionBase):
    id: int
    question_bank_id: Optional[int]
    document_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    type: str
    content: str
    options: Optional[List[str]] = None
    answer: Optional[str] = "未找到"
    explanation: Optional[str] = None

class ParseResult(BaseModel):
    questions: List[QuestionResponse]

class AnswerCheckRequest(BaseModel):
    question_id: int
    user_answer: str

class AnswerCheckResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: Optional[str] = None
