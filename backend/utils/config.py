"""
Configuration Management
========================
Centralized settings using Pydantic for validation and environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""
    
    # ========== Application ==========
    APP_NAME: str = "Adaptive Clinical Decision Simulator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # ========== OpenAI ==========
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_ORG_ID: str = Field(default="org-vqF6oLvoV4GIIq4fmxwoqpHz", description="OpenAI organization ID")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="Model for question generation")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    
    # ========== Database ==========
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service role key")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anon key")
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    # ========== CORS ==========
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed frontend origins"
    )
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # ========== RAG Configuration ==========
    CHUNK_SIZE: int = Field(default=800, description="Characters per chunk")
    CHUNK_OVERLAP: int = Field(default=100, description="Overlap between chunks")
    TOP_K_RETRIEVAL: int = Field(default=3, description="Number of chunks to retrieve")
    MIN_SIMILARITY_THRESHOLD: float = Field(default=0.70, description="Minimum cosine similarity")
    
    # ========== Adaptive Logic ==========
    LEVEL_UP_THRESHOLD: float = Field(default=8.0, description="Score needed to level up")
    LEVEL_DOWN_THRESHOLD: float = Field(default=5.0, description="Score that triggers level down")
    QUESTIONS_BEFORE_LEVEL_CHANGE: int = Field(default=3, description="Questions needed before level change")
    
    # ========== Grading Weights ==========
    WEIGHT_CLINICAL_ACCURACY: float = Field(default=0.40)
    WEIGHT_RISK_ASSESSMENT: float = Field(default=0.30)
    WEIGHT_COMMUNICATION: float = Field(default=0.20)
    WEIGHT_EFFICIENCY: float = Field(default=0.10)
    
    @validator("WEIGHT_CLINICAL_ACCURACY", "WEIGHT_RISK_ASSESSMENT", "WEIGHT_COMMUNICATION", "WEIGHT_EFFICIENCY")
    def validate_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Weights must be between 0 and 1")
        return v
    
    # ========== Security ==========
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    
    # ========== File Upload ==========
    MAX_UPLOAD_SIZE_MB: int = Field(default=50)
    ALLOWED_EXTENSIONS: List[str] = Field(default=["pdf", "PDF"])
    
    # ========== Rate Limiting ==========
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_HOUR: int = Field(default=500)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    def get_openai_config(self) -> dict:
        return {
            "api_key": self.OPENAI_API_KEY,
            "organization": self.OPENAI_ORG_ID
        }


settings = Settings()


def validate_configuration():
    """Validate critical configuration values"""
    errors = []
    
    total_weight = (
        settings.WEIGHT_CLINICAL_ACCURACY +
        settings.WEIGHT_RISK_ASSESSMENT +
        settings.WEIGHT_COMMUNICATION +
        settings.WEIGHT_EFFICIENCY
    )
    if not 0.99 <= total_weight <= 1.01:
        errors.append(f"Grading weights must sum to 1.0, got {total_weight}")
    
    if not settings.OPENAI_ORG_ID.startswith("org-"):
        errors.append(f"Invalid OpenAI org ID format: {settings.OPENAI_ORG_ID}")
    
    if not settings.SUPABASE_URL.startswith("https://"):
        errors.append("SUPABASE_URL must start with https://")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


validate_configuration()
