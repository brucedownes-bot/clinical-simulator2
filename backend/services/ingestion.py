"""
PDF Ingestion Service
=====================
Handles PDF → Text → Chunks → Embeddings → Database pipeline.
"""

import logging
from typing import List, Dict, Tuple
import re
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from io import BytesIO

from utils.config import settings
from utils.embedding import create_embeddings_batch
from services.database import get_supabase_client

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a single chunk with metadata"""
    def __init__(
        self,
        content: str,
        page_number: int,
        section_header: str = "",
        chunk_type: str = "standard"
    ):
        self.content = content
        self.page_number = page_number
        self.section_header = section_header
        self.chunk_type = chunk_type


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, Dict[int, str]]:
    """Extract text from PDF file"""
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        full_text = []
        page_dict = {}
        
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                if text.strip():
                    full_text.append(text)
                    page_dict[page_num] = text
                else:
                    logger.warning(f"Page {page_num} has no extractable text")
            except Exception as e:
                logger.error(f"Failed to extract text from page {page_num}: {e}")
        
        combined_text = "\n\n".join(full_text)
        logger.info(f"Extracted {len(combined_text)} characters from {len(page_dict)} pages")
        
        return combined_text, page_dict
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def identify_chunk_type(content: str) -> str:
    """Classify chunk type based on content patterns"""
    content_lower = content.lower()
    
    # Contraindication patterns
    contraindication_keywords = [
        "contraindicated", "do not use", "should not", "must not",
        "avoid", "contraindication", "prohibited"
    ]
    if any(keyword in content_lower for keyword in contraindication_keywords):
        return "contraindication"
    
    # Exception patterns
    exception_keywords = [
        "however", "exception", "in contrast", "alternatively", "but",
        "special case", "unique scenario"
    ]
    if any(keyword in content_lower for keyword in exception_keywords):
        return "exception"
    
    # Special population patterns
    special_pop_keywords = [
        "pregnancy", "pediatric", "geriatric", "renal impairment",
        "hepatic impairment", "dialysis", "elderly", "children"
    ]
    if any(keyword in content_lower for keyword in special_pop_keywords):
        return "special_population"
    
    return "standard"


def create_smart_chunks(text: str, page_dict: Dict[int, str]) -> List[DocumentChunk]:
    """Create semantically-aware chunks using RecursiveCharacterTextSplitter"""
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        length_function=len
    )
    
    raw_chunks = splitter.split_text(text)
    logger.info(f"Created {len(raw_chunks)} raw chunks")
    
    smart_chunks = []
    
    for chunk_text in raw_chunks:
        # Find which page this chunk belongs to
        page_number = 1
        for page_num, page_text in page_dict.items():
            if chunk_text[:100] in page_text:
                page_number = page_num
                break
        
        # Classify chunk type
        chunk_type = identify_chunk_type(chunk_text)
        
        chunk = DocumentChunk(
            content=chunk_text.strip(),
            page_number=page_number,
            section_header="",
            chunk_type=chunk_type
        )
        
        smart_chunks.append(chunk)
    
    logger.info(f"Enhanced {len(smart_chunks)} chunks with metadata")
    
    return smart_chunks


async def ingest_document(
    pdf_bytes: bytes,
    title: str,
    user_id: str,
    document_type: str = "guideline",
    specialty: str = "hospitalist"
) -> int:
    """Complete ingestion pipeline: PDF → Database with embeddings"""
    
    logger.info(f"Starting ingestion for: {title}")
    
    # Step 1: Extract text
    full_text, page_dict = extract_text_from_pdf(pdf_bytes)
    
    if not full_text.strip():
        raise ValueError("No text could be extracted from PDF")
    
    # Step 2: Create chunks
    chunks = create_smart_chunks(full_text, page_dict)
    
    if not chunks:
        raise ValueError("Failed to create chunks from document")
    
    # Step 3: Generate embeddings
    chunk_texts = [chunk.content for chunk in chunks]
    embeddings = await create_embeddings_batch(chunk_texts)
    
    # Step 4: Store in database
    supabase = get_supabase_client()
    
    # Insert document
    doc_response = supabase.table("documents").insert({
        "title": title,
        "content": full_text,
        "uploaded_by": user_id,
        "document_type": document_type,
        "specialty": specialty,
        "is_active": True
    }).execute()
    
    document_id = doc_response.data[0]["id"]
    logger.info(f"Created document {document_id}: {title}")
    
    # Insert chunks
    chunk_records = []
    for chunk, embedding in zip(chunks, embeddings):
        chunk_records.append({
            "document_id": document_id,
            "content": chunk.content,
            "embedding": embedding,
            "page_number": chunk.page_number,
            "section_header": chunk.section_header,
            "chunk_type": chunk.chunk_type
        })
    
    # Batch insert
    batch_size = 500
    for i in range(0, len(chunk_records), batch_size):
        batch = chunk_records[i:i + batch_size]
        supabase.table("document_chunks").insert(batch).execute()
        logger.info(f"Inserted chunk batch {i // batch_size + 1}")
    
    logger.info(f"✓ Ingestion complete: {len(chunks)} chunks stored for document {document_id}")
    
    return document_id


def validate_pdf(pdf_bytes: bytes) -> Tuple[bool, str]:
    """Validate PDF before processing"""
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        return False, f"PDF too large: {size_mb:.1f}MB (max: {settings.MAX_UPLOAD_SIZE_MB}MB)"
    
    if not pdf_bytes.startswith(b'%PDF'):
        return False, "File is not a valid PDF"
    
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if len(reader.pages) == 0:
            return False, "PDF has no pages"
    except Exception as e:
        return False, f"Corrupted PDF: {str(e)}"
    
    return True, ""
