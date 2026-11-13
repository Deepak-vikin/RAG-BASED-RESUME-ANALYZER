import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Document Analyzer API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    OPENROUTER_SITE_URL: str = "https://document-analyzer.vercel.app"
    OPENROUTER_APP_NAME: str = "Document Analyzer RAG"

    # Storage & Persistence
    # On Render free tier, local disk is ephemeral. Documents uploaded will be lost on restart.
    # On Render paid tier with Persistent Disk mounted at /var/data, set DATA_DIR=/var/data
    DATA_DIR: str = "./data"

    # RAG Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_K: int = 5

    # Security & Limits
    MAX_UPLOAD_SIZE_MB: int = 30
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md"]

    # CORS — comma-separated list of allowed origins.
    # Set to "*" for open access (dev), or specific Vercel URL for production.
    # Example: https://your-app.vercel.app,https://your-custom-domain.com
    FRONTEND_ORIGIN: str = "*"

    @property
    def cors_origins(self) -> List[str]:
        raw = self.FRONTEND_ORIGIN.strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
