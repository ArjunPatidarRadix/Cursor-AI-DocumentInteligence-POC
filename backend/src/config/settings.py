from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document Intelligence API"
    HOST: str = "0.0.0.0"
    PORT: str = "8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None

    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017/document_intelligence"
    DATABASE_NAME: str = "document_intelligence"

    # File Upload Configuration
    UPLOAD_DIR: str = "static/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Model Configuration
    CHROMA_DB_DIR: str = "chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    QA_MODEL: str = "deepset/roberta-base-squad2"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_upload_dir(self) -> Path:
        upload_dir = Path(self.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir


@lru_cache()
def get_settings():
    return Settings()
