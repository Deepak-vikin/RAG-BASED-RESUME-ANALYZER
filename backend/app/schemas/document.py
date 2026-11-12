from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str = Field(..., description="Unique document ID (UUID)")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(default=0, description="Number of pages in the document")
    chunk_count: int = Field(default=0, description="Number of text chunks indexed")
    uploaded_at: str = Field(..., description="ISO timestamp of upload")
    status: str = Field(default="ready", description="Processing status: processing, ready, error")
    file_type: str = Field(default="pdf", description="File extension")


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int


class DocumentUploadResponse(BaseModel):
    document: DocumentMetadata
    message: str


class DocumentDeleteResponse(BaseModel):
    document_id: str
    message: str

