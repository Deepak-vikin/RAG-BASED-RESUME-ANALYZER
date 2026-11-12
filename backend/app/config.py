import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Document Analyzer API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "https://document-analyzer.vercel.app")
    OPENROUTER_APP_NAME: str = os.getenv("OPENROUTER_APP_NAME", "Document Analyzer RAG")

    # Storage & Persistence
    # On Render, this can point to a persistent disk mount path, e.g. /var/data
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")))
    
    # RAG Settings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "5"))
    
    # Security & Limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "30"))
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md"]
    
    # CORS
    FRONTEND_ORIGIN: str = os.getenv(
        "FRONTEND_ORIGIN", 
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    )

    @property
    def cors_origins(self) -> List[str]:
        if not self.FRONTEND_ORIGIN or self.FRONTEND_ORIGIN.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

