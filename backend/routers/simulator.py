"""
Simulator Router - Main endpoints for question generation and grading
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import logging

from models.schemas import QuestionGenerateRequest, QuestionResponse, AnswerSubmitRequest, GradingResponse
from services.adaptive import generate_question, get_user_current_level
from services.grader import grade_answer
from services.database import get_supabase_client

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
    try:
        current_level = await get_user_current_level(user_id, request.document_id)
        
        logger.info(f"Generating Level {current_level} question for user {user_id}")
        
        question_data = await generate_question(
            document_id=request.document_id,
            user_id=user_id,
            current_level=current_level,
            topic=request.topic
        )
        
        return QuestionResponse(**question_data)
        
    except ValueError as e:
        logger.error(f"Question generation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in question generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate question")


@router.post("/submit", response_model=GradingResponse)
async def submit_answer(
    request: AnswerSubmitRequest,
    user_id: str = Depends(get_current_user)
):
    """Submit an answer for grading"""
    try:
        grading_result = await grade_answer(
            question_id=request.question_id,
            user_id=user_id,
            user_answer=request.answer_text
        )
        
        return GradingResponse(**grading_result)
        
    except ValueError as e:
        logger.error(f"Grading error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in grading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to grade answer")


@router.get("/progress/{document_id}")
async def get_progress(
    document_id: int,
    user_id: str = Depends(get_current_user)
):
    """Get user's progress on a specific document"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('user_document_mastery').select('*').eq(
            'user_id', user_id
        ).eq('document_id', document_id).execute()
        
        if not response.data:
            return {
                "document_id": document_id,
                "current_level": 1,
                "questions_answered": 0,
                "avg_score": 0.0
            }
        
        mastery = response.data[0]
        progress_pct = min(100, (mastery['avg_score'] / 8.0) * 100)
        
        return {
            "document_id": document_id,
            "current_level": mastery['current_level'],
            "questions_answered": mastery['questions_answered'],
            "questions_correct": mastery['questions_correct'],
            "avg_score": round(mastery['avg_score'], 2),
            "progress_to_next_level": round(progress_pct, 1),
            "last_active": mastery['last_active']
        }
        
    except Exception as e:
        logger.error(f"Error fetching progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch progress")
