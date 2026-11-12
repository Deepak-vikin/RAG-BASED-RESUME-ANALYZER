import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.api.routes import health, documents, chat
from backend.app.core.exceptions import DocumentAnalyzerException
from backend.app.services.embedding_service import embedding_service

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
origins = settings.cors_origins
logger.info(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)

# Mount Frontend static files if available
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
css_dir = os.path.join(frontend_dir, "css")
js_dir = os.path.join(frontend_dir, "js")

if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Document Analyzer Backend...")
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
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }
