from fastapi import APIRouter
from app.config import settings
from app.services.document_service import document_service

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Render monitoring and uptime probes.
    """
    docs = document_service.list_documents()
    is_openrouter_set = bool(
        settings.OPENROUTER_API_KEY
        and not settings.OPENROUTER_API_KEY.startswith("your_")
        and len(settings.OPENROUTER_API_KEY.strip()) > 10
    )

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "openrouter_configured": is_openrouter_set,
        "default_model": settings.OPENROUTER_MODEL,
        "indexed_documents_count": len(docs)
    }

