import json
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from app.config import settings
from app.schemas.chat import ChatMessage, ChatResponse, SourceDocument, ModelOption
from app.rag.prompts import format_context_from_documents, construct_rag_messages
from app.services.retrieval_service import retrieval_service
from app.services.openrouter_client import openrouter_client

logger = logging.getLogger(__name__)

# Curated list of popular, high-performance OpenRouter models
RECOMMENDED_MODELS = [
    ModelOption(
        id="meta-llama/llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct",
        description="Meta's top open-weights model, excellent reasoning and document comprehension",
        context_length=128000,
        is_free=False
    ),
    ModelOption(
        id="meta-llama/llama-3.3-70b-instruct:free",
        name="Llama 3.3 70B (Free)",
        description="High quality free tier of Llama 3.3 70B",
        context_length=128000,
        is_free=True
    ),
    ModelOption(
        id="google/gemini-2.0-flash-001",
        name="Gemini 2.0 Flash",
        description="Extremely fast, high accuracy, multi-modal context",
        context_length=1000000,
        is_free=False
    ),
    ModelOption(
        id="anthropic/claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        description="State-of-the-art reasoning, nuanced document analysis",
        context_length=200000,
        is_free=False
    ),
    ModelOption(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        description="Fast and cost-effective OpenAI model",
        context_length=128000,
        is_free=False
    ),
    ModelOption(
        id="deepseek/deepseek-chat",
        name="DeepSeek V3",
        description="High capability open foundation model",
        context_length=64000,
        is_free=False
    )
]


class LLMService:
    def __init__(self):
        self.client = openrouter_client

    def get_available_models(self) -> List[ModelOption]:
        return RECOMMENDED_MODELS

    async def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        model: Optional[str] = None
    ) -> ChatResponse:
        """
        Executes complete RAG pipeline for standard request.
        """
        target_model = model or settings.OPENROUTER_MODEL

        # 1. Retrieve top-k relevant chunks
        chunks = retrieval_service.retrieve_relevant_chunks(
            query=question,
            document_id=document_id
        )
        sources = retrieval_service.format_sources(chunks)

        # 2. Build context and prompt
        context = format_context_from_documents(chunks)
        messages = construct_rag_messages(question=question, context=context, history=history)

        # 3. Call OpenRouter
        response = await self.client.chat_completion(
            messages=messages,
            model=target_model
        )

        return ChatResponse(
            answer=response["content"],
            sources=sources,
            model_used=target_model,
            document_id=document_id
        )

    async def stream_answer(
        self,
        question: str,
        document_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Executes RAG pipeline and yields Server-Sent Events (SSE) stream.
        Event types:
        - {"type": "sources", "sources": [...], "model": "..."}
        - {"type": "token", "content": "..."}
        - {"type": "done", "model": "..."}
        - {"type": "error", "message": "..."}
        """
        target_model = model or settings.OPENROUTER_MODEL

        try:
            # 1. Retrieve relevant chunks
            chunks = retrieval_service.retrieve_relevant_chunks(
                query=question,
                document_id=document_id
            )
            sources = retrieval_service.format_sources(chunks)

            # Send sources payload first
            sources_payload = {
                "type": "sources",
                "sources": [s.model_dump() for s in sources],
                "model": target_model,
                "document_id": document_id
            }
            yield f"data: {json.dumps(sources_payload)}\n\n"

            # 2. Build context & prompt
            context = format_context_from_documents(chunks)
            messages = construct_rag_messages(question=question, context=context, history=history)

            # 3. Stream tokens
            async for token in self.client.chat_completion_stream(messages=messages, model=target_model):
                token_payload = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_payload)}\n\n"

            # Send completion signal
            done_payload = {"type": "done", "model": target_model}
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            logger.error(f"Error in stream_answer: {e}")
            err_payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err_payload)}\n\n"


llm_service = LLMService()

