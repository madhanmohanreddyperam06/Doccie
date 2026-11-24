"""FastAPI Application for Autonomous AI Document & TODO Agent."""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.agent.orchestrator import AgentOrchestrator
from app.auth import get_optional_current_user, router as auth_router
from app.core.config import settings
from app.db import DocumentRecord, User, engine, get_db, init_db
from app.llm import LLMError, LLMUnavailableError, get_llm_provider
from app.models.schemas import AgentRequest, AgentResponse
from app.todos import router as todos_router

# Load environment configuration
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autonomous_ai_agent")

# Generated files directory
GENERATED_DIR = settings.GENERATED_DIR
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager initializing database tables on startup."""
    logger.info("Initializing database schemas...")
    try:
        init_db()
    except Exception as exc:
        logger.error("Failed to initialize database: %s", exc)
    yield
    logger.info("Application shutting down.")


# Initialize FastAPI application
app = FastAPI(
    title="Autonomous AI Document Agent",
    description=(
        "Full-featured backend with PostgreSQL persistence, JWT Authentication, "
        "User & TODO management, and Autonomous AI Document generation."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend and development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers
app.include_router(auth_router)
app.include_router(todos_router)


@app.get("/", tags=["General"])
def read_root() -> Dict[str, Any]:
    """Root endpoint returning service information and discovered endpoints."""
    return {
        "service": "Autonomous AI Document Agent",
        "version": settings.VERSION,
        "status": "online",
        "description": "PostgreSQL-backed TODO Management, JWT Auth & Autonomous AI Document Agent.",
        "documentation": "/docs",
        "endpoints": {
            "create_document": "POST /agent",
            "download_document": "GET /documents/{filename}",
            "health_check": "GET /health",
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "swagger_token": "POST /auth/token",
                "profile": "GET /auth/me",
            },
            "todos": {
                "list_and_filter": "GET /todos",
                "create": "POST /todos",
                "get_single": "GET /todos/{id}",
                "update": "PUT /todos/{id}",
                "delete": "DELETE /todos/{id}",
            },
        },
    }


@app.get("/health", tags=["General"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/detail", tags=["General"])
def health_detail(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check validating database connectivity and active dialect."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as err:
        db_status = f"unhealthy: {err}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "database_url": engine.url.render_as_string(hide_password=True),
        "version": settings.VERSION,
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Silence browser favicon requests."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/agent",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agent"],
    summary="Generate a professional document autonomously",
)
def run_agent(
    payload: AgentRequest,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """Accept natural-language request, autonomously plan, execute, reflect, and create DOCX."""
    load_dotenv(override=True)
    try:
        llm = get_llm_provider()
        orchestrator = AgentOrchestrator(llm=llm)
        response = orchestrator.run(payload.request)

        # Save document generation record to database if successful
        if response.status == "completed" and response.document:
            try:
                record = DocumentRecord(
                    user_id=optional_user.id if optional_user else None,
                    title=response.document.title,
                    document_type=response.document.document_type,
                    filename=response.document.filename,
                    download_url=response.document.download_url,
                    request_text=payload.request,
                    status="completed",
                    reflection_score=(
                        response.reflection.score if response.reflection else None
                    ),
                )
                db.add(record)
                db.commit()
                logger.info(
                    "Persisted document record #%d for user_id=%s",
                    record.id,
                    record.user_id,
                )
            except Exception as db_err:
                logger.warning("Failed to save document metadata in DB: %s", db_err)

        return response

    except LLMUnavailableError as err:
        logger.error("LLM Service Unavailable: %s", err)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "failed",
                "error": "LLM service unavailable. Make sure Ollama is running.",
            },
        )

    except LLMError as err:
        logger.error("LLM Execution Error: %s", err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "failed",
                "error": f"LLM Error: {err}",
            },
        )

    except Exception as err:
        logger.error("Unexpected agent error: %s", err, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "failed",
                "error": f"Internal agent execution error: {str(err)}",
            },
        )


@app.get(
    "/documents",
    tags=["Documents"],
    summary="List generated documents",
)
def list_documents(
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """List documents generated in the system. If authenticated, filters by user ownership."""
    query = select(DocumentRecord)
    if optional_user:
        query = query.where(
            (DocumentRecord.user_id == optional_user.id)
            | (DocumentRecord.user_id.is_(None))
        )
    query = query.order_by(DocumentRecord.created_at.desc())
    records = list(db.scalars(query).all())

    return [
        {
            "id": rec.id,
            "title": rec.title,
            "document_type": rec.document_type,
            "filename": rec.filename,
            "download_url": rec.download_url,
            "reflection_score": rec.reflection_score,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "user_id": rec.user_id,
        }
        for rec in records
    ]


@app.get(
    "/documents/{filename}",
    tags=["Documents"],
    summary="Download generated Microsoft Word document",
)
def download_document(filename: str):
    """Retrieve and download a generated .docx file safely."""
    # Enforce strict filename pattern to prevent path traversal
    if not re.match(r"^[a-zA-Z0-9_\-\.]+\.docx$", filename):
        logger.warning("Invalid filename requested: %s", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename format. Only alphanumeric .docx filenames are permitted.",
        )

    file_path = GENERATED_DIR / filename

    if not file_path.is_file():
        logger.warning("Document not found: %s", filename)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
