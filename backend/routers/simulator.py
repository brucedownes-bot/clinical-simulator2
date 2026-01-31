"""
Simulator Router - Main endpoints for question generation and grading
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import logging

from models.schemas import QuestionGenerateRequest, QuestionResponse, AnswerSubmitRequest, GradingResponse

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, credentials = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        return credentials
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")


@router.post("/generate", response_model=QuestionResponse)
async def generate_adaptive_question(
    request: QuestionGenerateRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate a question adapted to user's current level"""
    # This is a stub - you'll implement the full logic from services/adaptive.py
    return {
        "question_id": "test-123",
        "level": 1,
        "content": "Placeholder question - implement adaptive.py",
        "sources": [],
        "metadata": {"status": "stub"}
    }


@router.post("/submit", response_model=GradingResponse)
async def submit_answer(
    request: AnswerSubmitRequest,
    user_id: str = Depends(get_current_user)
):
    """Submit an answer for grading"""
    # This is a stub - you'll implement the full logic from services/grader.py
    return {
        "answer_id": "test-456",
        "scores": {
            "clinical_accuracy": 3.0,
            "risk_assessment": 2.0,
            "communication": 1.5,
            "efficiency": 0.5,
            "total": 7.0
        },
        "feedback": "Placeholder feedback - implement grader.py",
        "strengths": ["Good start"],
        "areas_for_improvement": ["Add more detail"],
        "level_change": {
            "before": 1,
            "after": 1,
            "change": 0,
            "reason": "Keep practicing"
        },
        "guideline_references": []
    }


@router.get("/progress/{document_id}")
async def get_progress(
    document_id: int,
    user_id: str = Depends(get_current_user)
):
    """Get user's progress on a specific document"""
    return {
        "document_id": document_id,
        "current_level": 1,
        "questions_answered": 0,
        "avg_score": 0.0
    }
