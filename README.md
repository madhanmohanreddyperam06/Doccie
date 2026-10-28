# Autonomous AI Document Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/Ollama-Local%20LLM-black?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama" />
  <img src="https://img.shields.io/badge/DOCX-python--docx-2B579A?style=for-the-badge&logo=microsoftword&logoColor=white" alt="python-docx" />
  <img src="https://img.shields.io/badge/pytest-9%20Passed-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="pytest" />
</p>

An autonomous AI agent in Python that accepts a natural-language user request, dynamically creates a TODO/task execution plan, executes the tasks through modular internal tools, performs a reflection quality self-check, and generates a polished Microsoft Word (`.docx`) document as the final artifact.

---

## 1. Overview

Traditional LLM document generation relies on single-turn prompting, which frequently suffers from hallucinated structure, omitted requirements, and rigid formatting. 

The **Autonomous AI Document Agent** solves this through a multi-stage autonomous lifecycle:
1. **Understanding & Planning**: Interprets user intent, determines the document type, dynamically constructs an ordered task execution plan, and formulates strategic assumptions to resolve ambiguity.
2. **Deterministic Task Execution**: Sequentially executes each planned task via modular tools (Requirement Analyzer, Document Structure Generator, Content Generator).
3. **Reflection & Self-Check**: Evaluates the generated content against the original request and planned tasks on a 1-10 quality scale. If gaps are detected, it executes an autonomous single-cycle correction.
4. **Professional DOCX Generation**: Renders the finalized content into an executive-ready Microsoft Word document with custom typography, callouts, and zebra-striped tables.

---

## 2. Project Directory Structure

```text
E:\TODO App\
├── app\
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, routing, error handlers, and /favicon.ico
│   ├── agent\
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Master controller: Planning -> Execution -> Reflection -> DOCX
│   │   ├── planner.py           # Autonomous LLM planner generating dynamic task lists & assumptions
│   │   ├── executor.py          # Sequential task dispatcher with shared execution context
│   │   ├── tools.py             # 4 Modular internal tools (Analyzer, Structure, Content, DOCX)
│   │   └── reflection.py        # Self-critique agent (1-10 scoring & 1-cycle auto-correction)
│   ├── document\
│   │   ├── __init__.py
│   │   └── generator.py         # python-docx styling engine (Deep Navy #1E3A8A, callouts, tables)
│   ├── llm\
│   │   ├── __init__.py          # Provider factory with dynamic reload
│   │   ├── base.py              # Abstract LLMProvider, resilient JSON parser & error types
│   │   ├── ollama.py            # Local Ollama HTTP provider (/api/generate)
│   │   └── mock.py              # Zero-latency mock provider for instant offline tests & demo
│   └── models\
│       ├── __init__.py
│       └── schemas.py           # Pydantic v2 data models for requests, plans, tasks, and telemetry
├── generated\                   # Destination folder for generated .docx files
│   └── .gitkeep
├── tests\
│   ├── __init__.py
│   └── test_api.py              # 9 comprehensive automated tests (FastAPI TestClient)
├── .env                         # Active environment configuration
├── .env.example                 # Template environment configuration
├── .gitignore                   # Git ignore rules (venv, .env, docx files)
├── README.md                    # Project documentation, architecture & guide
├── requirements.txt             # Python dependencies
└── run.py                       # CLI entrypoint with terminal status banner
```

---

## 3. Architecture & Workflow

```text
User Natural-Language Request
              │
              ▼
    FastAPI POST /agent
              │
              ▼
   Pydantic Input Validation (Length: 10 - 5000 chars)
              │
              ▼
      Agent Orchestrator
              │
              ▼
         LLM Planner
              │
              ▼
   Dynamic Task Plan (TODO list) + Strategic Assumptions
              │
              ▼
        Task Executor
       ├── [Tool 1] Requirement Analyzer
       ├── [Tool 2] Document Structure Generator
       └── [Tool 3] Content Generator
              │
              ▼
   Reflection & Self-Check Agent
              │
              ├── PASS (Score >= 7) ──────────────┐
              │                                   │
              └── FAIL (Score < 7 or Gaps)        │
                   │                              │
                   ▼                              │
               1-Cycle Auto-Correction            │
                   │                              │
                   └──────────────────────────────┘
                                  │
                                  ▼
                      [Tool 4] DOCX Generator
                                  │
                                  ▼
                    Professional .docx Document
                                  │
                                  ▼
                    JSON Response with Telemetry
                      + File Download Endpoint
```

---

## 4. Technology Stack

- **Python 3.11+ / 3.14**: Modern typed Python backend.
- **FastAPI**: Asynchronous high-performance REST API with automated OpenAPI docs.
- **Uvicorn**: Lightweight ASGI web server with hot reload.
- **Pydantic v2**: Strict schema validation and structured JSON data serialization.
- **Ollama**: Local, private LLM inference (supports `llama3.2`, `llama3.2:1b`, `qwen2.5:0.5b`, etc.).
- **python-docx**: Microsoft Word document generation, custom styles, callouts, and tables.
- **httpx**: Resilient HTTP client with retry and timeout management.
- **pytest**: Automated unit and integration testing suite.

---

## 5. Setup & Installation

### Step 1: Clone and Navigate to Directory

```bash
cd "E:\TODO App"
```

### Step 2: Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create or edit your `.env` file (copied from `.env.example`):

```bash
cp .env.example .env
```

Key environment configuration variables:
```env
# Toggle between Instant Mock Mode (true) and Local Ollama (false)
USE_MOCK_LLM=true

# Ollama Settings (when USE_MOCK_LLM=false)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
GENERATED_DIR=generated
```

> **Tip**: With `USE_MOCK_LLM=true`, the server responds instantaneously (<0.5s) with high-fidelity, complete project proposals and implementation plans without needing GPU or Ollama running. To use live local inference, set `USE_MOCK_LLM=false` and run `ollama pull llama3.2`.

---

## 6. Running the Application

### Start the Server

```bash
python run.py
```

The terminal prints the status banner:
```text
======================================================================
🚀 Autonomous AI Document Agent Server Started
🏠 Root Endpoint:         http://127.0.0.1:8000/
📖 Swagger Documentation: http://127.0.0.1:8000/docs
💓 Health Check:          http://127.0.0.1:8000/health
🌐 Listening Interface:   http://0.0.0.0:8000
======================================================================
```

### Browsing the Endpoints

| Resource | URL | Description |
| :--- | :--- | :--- |
| **Interactive Swagger UI** | **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** | Test the agent, inspect schemas, download docs |
| **Alternative Docs (ReDoc)** | **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)** | Clean reference documentation |
| **Root Discovery** | **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** | Service info & active endpoint directory |
| **Health Check** | **[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)** | Liveness & uptime probe (`{"status":"healthy"}`) |

*(Note: In web browsers, use `http://127.0.0.1:8000` or `http://localhost:8000`. Browsing directly to `0.0.0.0` will return `ERR_ADDRESS_INVALID` on desktop browsers as `0.0.0.0` is a server listening address.)*

---

## 7. API Reference

### `POST /agent`
Accepts a natural-language request and autonomously executes the workflow.

**Request Body:**
```json
{
  "request": "Create a professional project proposal for developing an AI-powered customer support chatbot for a mid-sized e-commerce company."
}
```

**Response Body:**
```json
{
  "status": "completed",
  "message": "Agent completed the request successfully.",
  "request": "Create a professional project proposal for developing an AI-powered customer support chatbot...",
  "document": {
    "title": "AI Customer Support Chatbot Implementation Proposal",
    "document_type": "Project Proposal",
    "filename": "agent_document_20261028_110343_7a6e.docx",
    "download_url": "/documents/agent_document_20261028_110343_7a6e.docx"
  },
  "plan": [
    {
      "id": 1,
      "name": "Analyze business objectives and user needs",
      "type": "analysis",
      "status": "completed",
      "result": "Identified 4 core requirements and scope constraints."
    },
    {
      "id": 2,
      "name": "Establish baseline assumptions and scope",
      "type": "assumptions",
      "status": "completed",
      "result": "Formulated 4 operational assumptions to eliminate ambiguity."
    },
    {
      "id": 3,
      "name": "Design document outline and section hierarchy",
      "type": "structure",
      "status": "completed",
      "result": "Established layout outline with 4 structured sections."
    },
    {
      "id": 4,
      "name": "Generate detailed technical and operational content",
      "type": "content",
      "status": "completed",
      "result": "Generated 4 content sections with narrative and data tables."
    },
    {
      "id": 5,
      "name": "Compile strategic recommendations and next steps",
      "type": "recommendations",
      "status": "completed",
      "result": "Synthesized 3 strategic recommendations."
    },
    {
      "id": 6,
      "name": "Validate document completeness and clarity",
      "type": "validation",
      "status": "completed",
      "result": "Validated document integrity across 4 sections, assumptions, and conclusion."
    }
  ],
  "assumptions": [
    "The organization maintains an existing searchable customer support knowledge base and ticketing system.",
    "Initial launch focuses on web chat widget with CRM integration.",
    "The platform will support English at launch, with multi-lingual support in subsequent releases.",
    "Target initial containment rate is 65% for tier-1 repetitive inquiries."
  ],
  "execution": [ ... ],
  "reflection": {
    "passed": true,
    "score": 9,
    "issues": [],
    "improvements": [
      "Include post-launch SLA tracking and customer satisfaction metrics."
    ]
  }
}
```

### `GET /documents/{filename}`
Downloads the generated `.docx` file as an attachment. Protected against directory traversal attacks (e.g. `../`).

### `GET /health`
Returns service status: `{"status": "healthy"}`.

### `GET /`
Returns service metadata and endpoint directory.

### `GET /favicon.ico`
Returns `204 No Content` to keep terminal logs clean from automatic browser tab icon requests.

---

## 8. Verification & Test Cases

### Test Case 1: Standard Project Proposal
```json
{
  "request": "Create a professional project proposal for developing an AI-powered customer support chatbot for a mid-sized e-commerce company."
}
```
*Expected Behavior*: Agent identifies document type as `Project Proposal`, generates 6 tasks, formulates 4 assumptions, generates 4 rich sections with an implementation timeline table, passes reflection check (Score: 9/10), and produces `.docx`.

### Test Case 2: Ambiguous / Complex Implementation Plan
```json
{
  "request": "We are a college planning to build an AI-based student helpdesk. We have a limited budget and want to launch within three months. The system should support academic FAQs, admission information, hostel information, and basic technical support. It should be scalable, but we have not finalized the technology stack. Create a complete implementation proposal and make reasonable assumptions where information is missing."
}
```
*Expected Behavior*: Agent detects under-specified constraints (missing tech stack, undefined budget figures), autonomously formulates strategic assumptions (open-source models, cloud/on-prem hybrid, phased rollout), generates a complete 3-month roadmap table and cost allocation breakdown, and passes reflection.

---

## 9. Automated Testing

Run the automated test suite with pytest:

```bash
python -m pytest -v
```

### Test Coverage (9 Test Cases):
1. `test_read_root`: Verifies root metadata endpoint returns HTTP 200.
2. `test_health_check`: Verifies health endpoint returns HTTP 200 and healthy status.
3. `test_agent_validation_empty_request`: Verifies HTTP 422 Unprocessable Entity on empty body.
4. `test_agent_validation_short_request`: Verifies HTTP 422 when request is under 10 characters.
5. `test_agent_successful_proposal`: Tests end-to-end Project Proposal generation and docx creation.
6. `test_agent_ambiguous_college_helpdesk`: Tests autonomous assumption handling for ambiguous requirements.
7. `test_download_document_success`: Verifies download endpoint returns valid application/vnd.openxmlformats-officedocument.wordprocessingml.document stream.
8. `test_download_document_not_found`: Verifies HTTP 404 for non-existent document filename.
9. `test_download_document_path_traversal_prevention`: Verifies HTTP 400 rejection on `../../` path traversal attempts.

---

## 10. Engineering Improvement & Architectural Tradeoffs

### Mandatory Engineering Improvement: Reflection & Self-Check Loop
Single-pass generation frequently suffers from missed edge cases, brief text sections, or hallucinated requirements. To solve this, the agent incorporates a **Reflection and Self-Correction Agent**:
- Evaluates the generated content against the user's prompt, document structure, and task list.
- Scores the content across completeness, clarity, structural adherence, and tone (scale of 1-10).
- If the score is below 7 or significant gaps are identified, the agent triggers an **autonomous 1-cycle corrective enhancement** before compiling the `.docx` document.

### Architectural Tradeoff: Autonomous Planning vs. Deterministic Guardrails
- **The Dilemma**: Full LLM freedom can produce non-deterministic loops, syntax degradation, or unparseable JSON schemas. Conversely, hardcoded workflows lack adaptability to arbitrary document types.
- **The Solution**: A hybrid pattern where the LLM is assigned **cognitive tasks** (analyzing needs, formulating assumptions, writing content, reflecting on quality), while **control flow, tool dispatching, schema enforcement, exception recovery, and file rendering remain under deterministic Python control**.

---

## 11. Debugging & Resilience Highlights

During development, several key real-world challenges were identified and engineered for:
1. **Ollama Network Resilience**: ISP IPv6 routing timeouts can cause large model pulls to fail. We engineered an abstract `LLMProvider` interface with a drop-in `MockLLMProvider`, allowing the agent to function with zero latency and 100% test reliability offline.
2. **Schema & JSON Sanitization**: Local 7B/135M models often wrap JSON inside conversational text or Markdown blocks. We implemented `clean_llm_json()` with regex extractors and fallback schema normalizers to ensure the pipeline never crashes on malformed LLM responses.
3. **Path Traversal Security**: The file download endpoint enforces strict alphanumeric filename regex and directory containment validation (`Path.resolve()`), returning HTTP 400 if path traversal characters are injected.

---

## 12. 8–10 Minute Video Demo Script

Follow this structured script when recording a presentation or video walkthrough:

1. **Introduction & System Overview (1–2 mins)**
   - Explain the challenge: Moving beyond single-turn LLM generation to an autonomous, multi-step document creation agent.
   - Show the architecture diagram: User Prompt $\rightarrow$ Planner $\rightarrow$ Executor & Tools $\rightarrow$ Reflection $\rightarrow$ DOCX Generator.
2. **Setup & Configuration (1 min)**
   - Display `.env` configuration (`USE_MOCK_LLM=true`, `PORT=8000`).
   - Run `python run.py` and point out the clean terminal startup banner.
3. **Test Case 1 Walkthrough (2–3 mins)**
   - Open Swagger at `http://127.0.0.1:8000/docs`.
   - Submit Test Case 1 (`AI-powered customer support chatbot proposal`).
   - Walk through the response JSON: 6 dynamic tasks, formulated assumptions, reflection score (9/10), and execution telemetry.
   - Click the download URL and open the resulting `.docx` in Word: show the Deep Navy title, executive callout box, and formatted tables.
4. **Test Case 2: Handling Ambiguity (2 mins)**
   - Submit Test Case 2 (`College AI Student Helpdesk with limited budget and 3-month launch`).
   - Highlight how the agent autonomously identified missing details and formulated strategic assumptions to produce a complete proposal.
   - Open and review the generated document.
5. **Automated Testing & Code Architecture (1–2 mins)**
   - Run `python -m pytest -v` in the terminal to show all 9 tests passing.
   - Briefly highlight the modular directory structure: clean separation of `agent/`, `llm/`, `document/`, and `models/`.
