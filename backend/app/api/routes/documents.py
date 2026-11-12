import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.schemas.document import (
    DocumentMetadata,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentDeleteResponse
)
from backend.app.services.document_service import document_service
from backend.app.core.exceptions import DocumentAnalyzerException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a document (PDF, TXT, MD).
    Extracts text, splits into chunks, generates vector embeddings, and persists to disk.
    """
    try:
        meta = await document_service.process_uploaded_file(file)
        return DocumentUploadResponse(
            document=meta,
            message=f"Document '{meta.filename}' indexed successfully with {meta.chunk_count} chunks across {meta.page_count} pages."
        )
    except DocumentAnalyzerException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected upload failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    Get all uploaded and indexed documents.
    """
    docs = document_service.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    """
    Get metadata for a specific document by its ID.
    """
    try:
        return document_service.get_document(document_id)
    except DocumentAnalyzerException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """
    Delete a document, its associated vector store, files, and conversation history.
    """
    try:
        document_service.delete_document(document_id)
        return DocumentDeleteResponse(
            document_id=document_id,
            message=f"Document {document_id} and its vector indices were deleted successfully."
        )
    except DocumentAnalyzerException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

