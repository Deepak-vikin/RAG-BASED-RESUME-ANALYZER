import logging
from typing import Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """
        Returns singleton instance of HuggingFaceEmbeddings matching existing architecture.
        """
        if self._embeddings is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info("Embedding model loaded successfully.")
        return self._embeddings


embedding_service = EmbeddingService()

