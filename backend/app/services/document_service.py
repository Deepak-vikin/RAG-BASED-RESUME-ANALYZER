import os
import json
import uuid
import datetime
import logging
from typing import List, Optional, Dict
from fastapi import UploadFile
from backend.app.config import settings
from backend.app.schemas.document import DocumentMetadata
from backend.app.schemas.chat import ChatMessage
from backend.app.core.security import validate_file
from backend.app.core.exceptions import DocumentNotFoundError, DocumentProcessingError
from backend.app.services.text_extraction import TextExtractor
from backend.app.rag.chunking import DocumentSplitter
from backend.app.services.retrieval_service import retrieval_service

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.uploads_dir = os.path.join(self.data_dir, "uploads")
        self.metadata_file = os.path.join(self.data_dir, "documents_meta.json")
        self.history_file = os.path.join(self.data_dir, "chat_history.json")
        
        os.makedirs(self.uploads_dir, exist_ok=True)
        self.splitter = DocumentSplitter()
        self._load_metadata()
        self._load_history()

    def _load_metadata(self):
        self.metadata: Dict[str, dict] = {}
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def _load_history(self):
        self.history: Dict[str, List[dict]] = {}
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                self.history = {}

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    async def process_uploaded_file(self, file: UploadFile) -> DocumentMetadata:
        """
        Validates, saves, extracts, splits, embeds and indexes an uploaded document.
        """
        contents = await file.read()
        file_size = len(contents)

        # Validate filename and size
        clean_name, ext = validate_file(file.filename or "uploaded_file.pdf", file_size)
        doc_id = str(uuid.uuid4())

        # Save to disk
        file_path = os.path.join(self.uploads_dir, f"{doc_id}_{clean_name}")
        with open(file_path, "wb") as f:
            f.write(contents)

        try:
            # 1. Text extraction (preserving PyPDFLoader)
            docs = TextExtractor.extract_from_file(file_path, clean_name, doc_id)
            if not docs:
                raise DocumentProcessingError(f"No extractable text found in '{clean_name}'.")

            page_count = len(docs) if ext == ".pdf" else 1

            # 2. Split into chunks (preserving RecursiveCharacterTextSplitter 800/150)
            chunks = self.splitter.split_documents(docs)
            chunk_count = len(chunks)

            # 3. Embed and build FAISS index
            retrieval_service.save_document_chunks(doc_id, chunks)

            # 4. Save metadata
            meta = {
                "id": doc_id,
                "filename": clean_name,
                "file_size": file_size,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "uploaded_at": datetime.datetime.utcnow().isoformat() + "Z",
                "status": "ready",
                "file_type": ext.lstrip("."),
                "file_path": file_path
            }
            self.metadata[doc_id] = meta
            self._save_metadata()

            logger.info(f"Successfully processed document {clean_name} ({doc_id}) with {chunk_count} chunks.")
            return DocumentMetadata(**meta)

        except Exception as e:
            # Clean up on failure
            if os.path.exists(file_path):
                os.remove(file_path)
            retrieval_service.delete_document_store(doc_id)
            logger.error(f"Failed to process document {clean_name}: {e}")
            raise DocumentProcessingError(f"Failed to process {clean_name}: {str(e)}")

    def list_documents(self) -> List[DocumentMetadata]:
        return [DocumentMetadata(**m) for m in self.metadata.values()]

    def get_document(self, document_id: str) -> DocumentMetadata:
        if document_id not in self.metadata:
            raise DocumentNotFoundError(document_id)
        return DocumentMetadata(**self.metadata[document_id])

    def delete_document(self, document_id: str) -> bool:
        if document_id not in self.metadata:
            raise DocumentNotFoundError(document_id)

        meta = self.metadata[document_id]
        file_path = meta.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")

        # Delete vector store
        retrieval_service.delete_document_store(document_id)

        # Clear history
        self.history.pop(document_id, None)
        self._save_history()

        # Remove metadata
        del self.metadata[document_id]
        self._save_metadata()

        return True

    def get_chat_history(self, document_id: Optional[str] = None) -> List[ChatMessage]:
        key = document_id or "global"
        history_list = self.history.get(key, [])
        return [ChatMessage(**item) for item in history_list]

    def add_to_chat_history(self, document_id: Optional[str], role: str, content: str):
        key = document_id or "global"
        if key not in self.history:
            self.history[key] = []
        self.history[key].append({"role": role, "content": content})
        # Keep last 50 messages
        if len(self.history[key]) > 50:
            self.history[key] = self.history[key][-50:]
        self._save_history()

    def clear_chat_history(self, document_id: Optional[str] = None) -> bool:
        key = document_id or "global"
        self.history.pop(key, None)
        self._save_history()
        return True


document_service = DocumentService()

