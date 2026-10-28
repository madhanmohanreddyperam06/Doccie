"""Unit and API Integration Tests for Autonomous AI Document Agent."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure test mode uses Mock LLM by default to avoid Ollama dependency during unit tests
os.environ["USE_MOCK_LLM"] = "true"

from app.main import app

client = TestClient(app)


def test_get_root():
    """Test 1: GET / returns 200 with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Autonomous AI Document Agent"
    assert data["status"] == "online"
    assert "endpoints" in data


def test_get_health():
    """Test 2: GET /health returns 200 with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_post_agent_empty_request_rejected():
    """Test 3: POST /agent with empty request string fails with 422."""
    response = client.post("/agent", json={"request": ""})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_post_agent_too_short_request_rejected():
    """Test 4: POST /agent with request under 10 characters fails with 422."""
    response = client.post("/agent", json={"request": "too short"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_post_agent_missing_payload_rejected():
    """Test: POST /agent with empty body fails with 422."""
    response = client.post("/agent", json={})
    assert response.status_code == 422


def test_post_agent_valid_request_execution():
    """Test 5: POST /agent with valid request completes end-to-end workflow."""
    req_body = {
        "request": "Create a professional project proposal for an AI-powered customer support chatbot."
    }
    response = client.post("/agent", json=req_body)
    assert response.status_code == 200
    data = response.json()

    # Validate top-level response contracts
    assert data["status"] == "completed"
    assert "Agent completed" in data["message"]
    assert data["request"] == req_body["request"]

    # Validate assumptions
    assert isinstance(data["assumptions"], list)
    assert len(data["assumptions"]) > 0

    # Validate execution tasks
    assert isinstance(data["plan"], list)
    assert len(data["plan"]) >= 4
    for task in data["plan"]:
        assert task["status"] == "completed"
        assert task["name"]

    # Validate reflection
    assert data["reflection"] is not None
    assert data["reflection"]["passed"] is True
    assert data["reflection"]["score"] >= 7

    # Validate document metadata
    doc_info = data["document"]
    assert doc_info["title"]
    assert doc_info["document_type"] == "Project Proposal"
    assert doc_info["filename"].endswith(".docx")
    assert doc_info["download_url"].startswith("/documents/")

    # Validate file actually exists on filesystem
    gen_dir = Path("generated")
    file_path = gen_dir / doc_info["filename"]
    assert file_path.is_file()
    assert file_path.stat().st_size > 0

    # Test downloading the created document
    download_res = client.get(doc_info["download_url"])
    assert download_res.status_code == 200
    assert "wordprocessingml" in download_res.headers.get("content-type", "")


def test_post_agent_ambiguous_request_handles_assumptions():
    """Test: Ambiguous request autonomously formulates assumptions and completes."""
    req_body = {
        "request": "We are a college planning to build an AI student helpdesk with limited budget and 3-month launch."
    }
    response = client.post("/agent", json=req_body)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert len(data["assumptions"]) >= 3
    assert data["document"]["document_type"] in ("Implementation Plan", "Project Proposal")
    assert data["reflection"]["passed"] is True


def test_download_document_not_found():
    """Test 6: GET /documents/{filename} with non-existent file returns 404."""
    response = client.get("/documents/non_existent_document_12345.docx")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_document_path_traversal_rejected():
    """Test 7: Path traversal attempt is rejected with 400 or 404."""
    response = client.get("/documents/..%2Fevil.docx")
    assert response.status_code in (400, 404)
