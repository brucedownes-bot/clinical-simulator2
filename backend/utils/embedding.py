"""
OpenAI Embedding Utilities
===========================
Wrapper for OpenAI embedding API with error handling.
"""

import asyncio
from typing import List
import numpy as np
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from utils.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    organization=settings.OPENAI_ORG_ID
)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
async def create_embedding(text: str) -> List[float]:
    """Create an embedding for a single text string"""
    try:
        text = text.strip().replace("\n", " ")
        
        if not text:
            raise ValueError("Cannot create embedding for empty text")
        
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Created embedding for text (length={len(text)})")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to create embedding: {e}")
        raise


async def create_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """Create embeddings for multiple texts in batches"""
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = await client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=batch
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Created embeddings for batch {i // batch_size + 1}")
            
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Failed to create batch embeddings: {e}")
            raise
    
    return all_embeddings


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return float(np.clip(similarity, 0.0, 1.0))


async def test_embedding_api():
    """Test OpenAI embedding API connection"""
    try:
        test_text = "This is a test of the OpenAI embedding API."
        embedding = await create_embedding(test_text)
        
        expected_dim = 1536
        if len(embedding) != expected_dim:
            logger.warning(f"Unexpected embedding dimension: {len(embedding)}")
        
        logger.info(f"✓ Embedding API test successful (dim={len(embedding)})")
        return True
        
    except Exception as e:
        logger.error(f"✗ Embedding API test failed: {e}")
        return False
