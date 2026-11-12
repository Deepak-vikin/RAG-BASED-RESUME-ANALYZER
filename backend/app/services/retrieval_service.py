import os
import shutil
import logging
from typing import List, Optional, Dict
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from backend.app.config import settings
from backend.app.services.embedding_service import embedding_service
from backend.app.schemas.chat import SourceDocument
from backend.app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self):
        self.vectorstores_dir = os.path.join(settings.DATA_DIR, "vectorstores")
        os.makedirs(self.vectorstores_dir, exist_ok=True)
        self._cache: Dict[str, FAISS] = {}

    def _get_store_path(self, document_id: str) -> str:
        return os.path.join(self.vectorstores_dir, document_id)

    def save_document_chunks(self, document_id: str, chunks: List[Document]) -> FAISS:
        """
        Embeds chunks and saves FAISS index to persistent disk storage.
        """
        try:
            embeddings = embedding_service.get_embeddings()
            vectorstore = FAISS.from_documents(chunks, embeddings)
            
            store_path = self._get_store_path(document_id)
            os.makedirs(store_path, exist_ok=True)
            vectorstore.save_local(store_path)
            
            self._cache[document_id] = vectorstore
            logger.info(f"Saved FAISS index for document {document_id} to {store_path}")
            return vectorstore
        except Exception as e:
            logger.error(f"Failed to create FAISS store for document {document_id}: {e}")
            raise VectorStoreError(f"Vector storage failed: {str(e)}")

    def get_document_store(self, document_id: str) -> Optional[FAISS]:
        """
        Loads FAISS store from cache or disk for a specific document.
        """
        if document_id in self._cache:
            return self._cache[document_id]

        store_path = self._get_store_path(document_id)
        if os.path.exists(os.path.join(store_path, "index.faiss")):
            try:
                embeddings = embedding_service.get_embeddings()
                store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
                self._cache[document_id] = store
                return store
            except Exception as e:
                logger.error(f"Failed to load FAISS store for {document_id}: {e}")
                return None
        return None

    def delete_document_store(self, document_id: str) -> bool:
        """
        Deletes FAISS store from disk and cache.
        """
        self._cache.pop(document_id, None)
        store_path = self._get_store_path(document_id)
        if os.path.exists(store_path):
            shutil.rmtree(store_path, ignore_errors=True)
            logger.info(f"Removed FAISS index for {document_id}")
            return True
        return False

    def retrieve_relevant_chunks(
        self,
        query: str,
        document_id: Optional[str] = None,
        all_document_ids: Optional[List[str]] = None,
        k: Optional[int] = None
    ) -> List[Document]:
        """
        Retrieves top-k most relevant chunks matching the query.
        If document_id is provided, retrieval is strictly scoped to that document.
        If not provided, retrieval aggregates top chunks across all available documents.
        """
        top_k = k or settings.RETRIEVAL_K

        # Case 1: Scoped to specific document
        if document_id:
            store = self.get_document_store(document_id)
            if not store:
                logger.warning(f"No vector store found for document {document_id}")
                return []
            return store.similarity_search(query, k=top_k)

        # Case 2: Query across all available documents
        candidates: List[Document] = []
        doc_ids = all_document_ids or list(self._cache.keys())
        
        # If cache empty, look at directories
        if not doc_ids and os.path.exists(self.vectorstores_dir):
            doc_ids = [d for d in os.listdir(self.vectorstores_dir) if os.path.isdir(os.path.join(self.vectorstores_dir, d))]

        for doc_id in doc_ids:
            store = self.get_document_store(doc_id)
            if store:
                results = store.similarity_search_with_score(query, k=top_k)
                for doc, score in results:
                    candidates.append((doc, score))

        # Sort by distance score ascending (lower is closer in FAISS L2)
        candidates.sort(key=lambda x: x[1])
        return [doc for doc, _ in candidates[:top_k]]

    @staticmethod
    def format_sources(docs: List[Document]) -> List[SourceDocument]:
        """
        Converts LangChain Document objects into structured SourceDocument schemas.
        """
        sources = []
        for doc in docs:
            snippet = doc.page_content.strip()
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."
            
            sources.append(
                SourceDocument(
                    document_id=doc.metadata.get("document_id", "unknown"),
                    source=doc.metadata.get("source", "Document"),
                    page=doc.metadata.get("page"),
                    chunk_index=doc.metadata.get("chunk_index"),
                    content_snippet=snippet
                )
            )
        return sources


retrieval_service = RetrievalService()

