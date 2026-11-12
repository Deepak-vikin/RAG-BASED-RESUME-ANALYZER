import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ModelOption
)
from backend.app.services.llm_service import llm_service
from backend.app.services.document_service import document_service
from backend.app.core.exceptions import DocumentAnalyzerException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.get("/models", response_model=List[ModelOption])
async def get_available_models():
    """
    List available OpenRouter models supported for document question answering.
    """
    return llm_service.get_available_models()


@router.post("", response_model=ChatResponse)
async def chat_standard(request: ChatRequest):
    """
    Standard question answering endpoint grounded in uploaded documents.
    """
    try:
        # Retrieve history if not provided in payload
        history = request.history
        if not history and request.document_id:
            history = document_service.get_chat_history(request.document_id)

        # Call RAG LLM service
        response = await llm_service.answer_question(
            question=request.question,
            document_id=request.document_id,
            history=history,
            model=request.model
        )

        # Record conversation in history
        document_service.add_to_chat_history(request.document_id, "user", request.question)
        document_service.add_to_chat_history(request.document_id, "assistant", response.answer)

        return response
    except DocumentAnalyzerException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Real-time streaming question answering endpoint via Server-Sent Events (SSE).
    """
    try:
        history = request.history
        if not history and request.document_id:
            history = document_service.get_chat_history(request.document_id)

        # Append user question to history
        document_service.add_to_chat_history(request.document_id, "user", request.question)

        async def event_generator():
            full_assistant_reply = []
            async for chunk in llm_service.stream_answer(
                question=request.question,
                document_id=request.document_id,
                history=history,
                model=request.model
            ):
                yield chunk

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except DocumentAnalyzerException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Chat stream failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")


@router.get("/history/{document_id}", response_model=ChatHistoryResponse)
async def get_history(document_id: str):
    """
    Get conversation history for a specific document or global session.
    Use 'global' for unscoped document chats.
    """
    history = document_service.get_chat_history(document_id if document_id != "global" else None)
    return ChatHistoryResponse(document_id=document_id, history=history)


@router.delete("/history/{document_id}")
async def clear_history(document_id: str):
    """
    Clear conversation history for a document or global session.
    """
    document_service.clear_chat_history(document_id if document_id != "global" else None)
    return {"message": f"Conversation history for '{document_id}' cleared successfully."}

