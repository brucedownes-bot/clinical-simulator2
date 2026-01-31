"""
Documents Router - PDF upload and management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
import logging

from models.schemas import DocumentResponse
from routers.simulator import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("guideline"),
    specialty: str = Form("hospitalist"),
    user_id: str = Depends(get_current_user)
):
    """Upload and ingest a PDF document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=422, detail="Only PDF files are supported")
    
    # This is a stub - you'll implement full ingestion from services/ingestion.py
    return {
        "id": 1,
        "title": title,
        "document_type": document_type,
        "specialty": specialty,
        "uploaded_at": "2026-01-31T00:00:00Z",
        "chunk_count": 0,
        "user_mastery_level": 1
    }


@router.get("/")
async def list_documents(
    specialty: str = None,
    user_id: str = Depends(get_current_user)
):
    """List all documents"""
    return {
        "documents": [],
        "total": 0
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    user_id: str = Depends(get_current_user)
):
    """Get details for a specific document"""
    return {
        "id": document_id,
        "title": "Placeholder Document",
        "document_type": "guideline",
        "specialty": "hospitalist",
        "uploaded_at": "2026-01-31T00:00:00Z",
        "chunk_count": 0,
        "user_mastery_level": 1
    }
