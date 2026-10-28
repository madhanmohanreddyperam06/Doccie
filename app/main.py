"""FastAPI Application for Autonomous AI Document Agent."""

import logging
import os
from pathlib import Path
import re
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.agent.orchestrator import AgentOrchestrator
from app.llm import LLMError, LLMUnavailableError, get_llm_provider
from app.models.schemas import AgentRequest, AgentResponse

# Load environment configuration
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autonomous_ai_agent")

# Initialize FastAPI application
app = FastAPI(
    title="Autonomous AI Document Agent",
    description="Autonomous AI Agent that plans, executes, self-reflects, and generates professional Word (.docx) documents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generated files directory
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", "generated"))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", tags=["General"])
def read_root() -> Dict[str, Any]:
    """Root endpoint returning basic service information."""
    return {
        "service": "Autonomous AI Document Agent",
        "version": "1.0.0",
        "status": "online",
        "description": "Autonomous planning, execution, self-check, and DOCX generation agent.",
        "documentation": "/docs",
        "endpoints": {
            "create_document": "POST /agent",
            "download_document": "GET /documents/{filename}",
            "health_check": "GET /health",
        },
    }


@app.get("/health", tags=["General"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


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
def run_agent(payload: AgentRequest) -> Any:
    """Accept natural-language request, autonomously plan, execute, reflect, and create DOCX."""
    load_dotenv(override=True)
    try:
        llm = get_llm_provider()
        orchestrator = AgentOrchestrator(llm=llm)
        response = orchestrator.run(payload.request)
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
