"""
Database Service
================
Supabase client initialization and helper functions.
"""

import logging
from supabase import create_client, Client
from typing import Optional

from utils.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    return _supabase_client


async def test_connection() -> bool:
    """Test database connection"""
    try:
        client = get_supabase_client()
        response = client.table('documents').select('id').limit(1).execute()
        logger.info("✓ Database connection test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        return False


def close_connection():
    """Close Supabase connection"""
    global _supabase_client
    _supabase_client = None
    logger.info("Supabase client closed")
