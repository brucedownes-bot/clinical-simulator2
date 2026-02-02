"""
Documents Router - PDF upload and management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
import logging

from models.schemas import DocumentResponse
from routers.simulator import get_current_user
from services.ingestion import ingest_document, validate_pdf
from services.database import get_supabase_client

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
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        # Validate PDF
        is_valid, error_msg = validate_pdf(pdf_bytes)
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_msg)
        
        logger.info(f"Uploading document: {title} ({len(pdf_bytes)} bytes)")
        
        # Ingest document
        document_id = await ingest_document(
            pdf_bytes=pdf_bytes,
            title=title,
            user_id=user_id,
            document_type=document_type,
            specialty=specialty
        )
        
        # Fetch document details
        supabase = get_supabase_client()
        doc_response = supabase.table('documents').select(
            'id, title, document_type, specialty, uploaded_at'
        ).eq('id', document_id).execute()
        
        doc = doc_response.data[0]
        
        # Count chunks
        chunk_response = supabase.table('document_chunks').select(
            'id', count='exact'
        ).eq('document_id', document_id).execute()
        
        return DocumentResponse(
            id=doc['id'],
            title=doc['title'],
            document_type=doc['document_type'],
            specialty=doc['specialty'],
            uploaded_at=doc['uploaded_at'],
            chunk_count=chunk_response.count,
            user_mastery_level=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/")
async def list_documents(user_id: str = Depends(get_current_user)):
    """List all documents"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('documents').select('*').eq('is_active', True).execute()
        return {"documents": response.data, "total": len(response.data)}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")
