from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class SourceDocument(BaseModel):
    document_id: str = Field(..., description="ID of source document")
    source: str = Field(..., description="Source filename")
    page: Optional[int] = Field(None, description="Page number (1-based if available)")
    chunk_index: Optional[int] = Field(None, description="Index of the chunk")
    content_snippet: str = Field(..., description="Excerpt from the chunk")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    document_id: Optional[str] = Field(None, description="Scope query to specific document or None for all")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns")
    model: Optional[str] = Field(None, description="Override OpenRouter model for this query")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer grounded in documents")
    sources: List[SourceDocument] = Field(default=[], description="Retrieved source chunks used")
    model_used: str = Field(..., description="Model used for generation")
    document_id: Optional[str] = Field(None, description="Target document ID if scoped")


class ChatHistoryResponse(BaseModel):
    document_id: Optional[str]
    history: List[ChatMessage]


class ModelOption(BaseModel):
    id: str
    name: str
    description: str
    context_length: int
    is_free: bool = False

