"""
Pydantic Models
===============
Request/Response schemas for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    GUIDELINE = "guideline"
    PROTOCOL = "protocol"
    TEXTBOOK = "textbook"


class Specialty(str, Enum):
    HOSPITALIST = "hospitalist"
    CARDIOLOGY = "cardiology"
    ICU = "icu"


class ChunkType(str, Enum):
    STANDARD = "standard"
    EXCEPTION = "exception"
    CONTRAINDICATION = "contraindication"
    SPECIAL_POPULATION = "special_population"


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    document_type: DocumentType = DocumentType.GUIDELINE
    specialty: Specialty = Specialty.HOSPITALIST


class DocumentResponse(BaseModel):
    id: int
    title: str
    document_type: str
    specialty: str
    uploaded_at: datetime
    chunk_count: Optional[int] = None
    user_mastery_level: Optional[int] = None


class ChunkSource(BaseModel):
    chunk_id: int
    text: str
    page: int
    section: Optional[str] = None
    type: ChunkType = ChunkType.STANDARD


class QuestionGenerateRequest(BaseModel):
    document_id: int
    topic: Optional[str] = None


class QuestionResponse(BaseModel):
    question_id: str
    level: int = Field(..., ge=1, le=5)
    content: str
    sources: List[ChunkSource]
    metadata: Dict


class AnswerSubmitRequest(BaseModel):
    question_id: str
    answer_text: str = Field(..., min_length=10, max_length=2000)
    
    @validator('answer_text')
    def validate_answer(cls, v):
        if v.strip().lower() in ['i dont know', 'idk', 'skip']:
            raise ValueError('Please provide a substantive answer')
        return v.strip()


class ScoreBreakdown(BaseModel):
    clinical_accuracy: float = Field(..., ge=0, le=4)
    risk_assessment: float = Field(..., ge=0, le=3)
    communication: float = Field(..., ge=0, le=2)
    efficiency: float = Field(..., ge=0, le=1)
    total: float = Field(..., ge=0, le=10)


class LevelChange(BaseModel):
    before: int = Field(..., ge=1, le=5)
    after: int = Field(..., ge=1, le=5)
    change: int = Field(..., ge=-1, le=1)
    reason: str


class GuidelineReference(BaseModel):
    content: str
    page: int


class GradingResponse(BaseModel):
    answer_id: str
    scores: ScoreBreakdown
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    level_change: LevelChange
    guideline_references: List[GuidelineReference]


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None
