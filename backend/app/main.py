import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import health, documents, chat
from app.core.exceptions import DocumentAnalyzerException
from app.services.embedding_service import embedding_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("document-analyzer")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready RAG Document Question Answering API powered by OpenRouter and FAISS.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
# Note: allow_credentials=True cannot be combined with allow_origins=["*"]
# When FRONTEND_ORIGIN is "*", we set allow_credentials=False
origins = settings.cors_origins
is_wildcard = "*" in origins
logger.info(f"Configured CORS origins: {origins}, wildcard={is_wildcard}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else origins,
    allow_credentials=False if is_wildcard else True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Document Analyzer Backend...")
    logger.info(f"DATA_DIR: {settings.DATA_DIR}")
    logger.info(f"OPENROUTER_MODEL: {settings.OPENROUTER_MODEL}")
    logger.info(f"OPENROUTER_API_KEY configured: {'YES' if settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY) > 10 else 'NO'}")
    # Pre-warm the embedding model on startup
    try:
        embedding_service.get_embeddings()
        logger.info("HuggingFaceEmbeddings ready.")
    except Exception as e:
        logger.warning(f"Embedding model pre-warm notice: {e}")


@app.exception_handler(DocumentAnalyzerException)
async def custom_exception_handler(request: Request, exc: DocumentAnalyzerException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }
