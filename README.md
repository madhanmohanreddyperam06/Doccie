# Doccie

<div align="left">

![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-3776AB?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?style=flat-square&logo=postgresql)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat-square&logo=ollama)
![DOCX](https://img.shields.io/badge/DOCX-python--docx-2B579A?style=flat-square&logo=microsoftword)
![pytest](https://img.shields.io/badge/pytest-16%20Passed-0A9EDC?style=flat-square&logo=pytest)
![Render](https://img.shields.io/badge/Render-Cloud%20Deploy-46E3B7?style=flat-square&logo=render)

</div>

An autonomous AI document & task backend in Python that accepts a natural-language request, dynamically generates a structured execution TODO plan, runs modular internal tools, performs a scored quality self-check with autonomous self-correction, persists records in PostgreSQL (with local SQLite fallback), and exports a publication-ready Microsoft Word (`.docx`) file alongside JWT-authenticated user & TODO management APIs.

---

## 1. Overview & Autonomous Lifecycle

Single-turn LLM prompting often leads to omitted requirements, inconsistent structure, and unverified formatting. **Doccie** replaces single-shot generation with a deterministic Python orchestrator that delegates cognitive tasks to an LLM while keeping control flow, schema enforcement, quality reflection, and `.docx` rendering strictly deterministic.

### Autonomous Lifecycle Stages

| Stage | Component | Responsibility | Primary Output | Quality / Fallback Guardrail |
| :--- | :--- | :--- | :--- | :--- |
| **1. Planning** | `Planner` | Classifies document type, sets title & objective, resolves ambiguities via 3–5 assumptions, builds 4–7 ordered tasks | `PlanOutput` | Contextual fallback plan (`_create_contextual_fallback_plan`) |
| **2. Execution** | `TaskExecutor` | Dispatches each planned task sequentially to modular handlers sharing an execution context | `List[TaskResult]` | Per-task try/except isolation & fallback content synthesis |
| **3. Reflection** | `ReflectionAgent` | Audits generated content against the prompt, task plan, and assumptions on a `1–10` scale | `ReflectionResult` | Triggers 1-cycle auto-correction if `score < 7` or issues exist; heuristic fallback |
| **4. Rendering** | `DocxDocumentGenerator` | Compiles Executive Summary, Assumptions callout, sections, lists, tables, and conclusions into `.docx` | `DocumentResult` | Safe UUID-suffixed filename & strict download validation |
| **5. Persistence** | `SQLAlchemy` + `FastAPI` | Records document metadata in `documents` and manages user accounts & personal `todos` via JWT auth | HTTP JSON + DB Row | Cloud PostgreSQL retry loop + optional local SQLite fallback |

### Autonomous Document Agent Pipeline

```mermaid
flowchart TD
    A["Natural-Language Request (POST /agent)"] --> B["Pydantic Validation (10–5000 chars)"]
    B --> C["AgentOrchestrator.run()"]
    C --> D["Planner.plan(): Type, Assumptions & 4–7 Tasks"]
    D --> E["TaskExecutor.execute_plan(): Shared Context Dispatch"]

    subgraph Tools ["Modular Internal Tools"]
        direction LR
        T1["Tool 1: RequirementAnalyzerTool"]
        T2["Tool 2: DocumentStructureGeneratorTool"]
        T3["Tool 3: ContentGeneratorTool"]
    end

    E --> Tools
    Tools --> F["ReflectionAgent.evaluate() (1–10 Scale)"]
    F --> G{"passed == true? (score >= 7, no issues)"}
    G -- "No (Score < 7 or Gaps)" --> H["1-Cycle Auto-Correction: correct_content()"]
    H --> I["Tool 4: DocumentGeneratorTool (.docx)"]
    G -- "Yes" --> I
    I --> J["Save DocumentRecord (PostgreSQL / SQLite)"]
    J --> K["Return AgentResponse (Telemetry + Download URL)"]
```

---

## 2. Architecture & Module Classification

### Package & Module Classification

| Layer | Package / File | Key Symbols | Responsibility |
| :--- | :--- | :--- | :--- |
| **Entrypoint & API** | [`run.py`](run.py), [`app/main.py`](app/main.py) | `app`, `lifespan`, `run_agent`, `download_document` | Uvicorn launcher, CORS, health probes, router wiring, `/agent`, `/documents` |
| **Agent Core** | [`app/agent/`](app/agent/) | `AgentOrchestrator`, `Planner`, `TaskExecutor`, `ReflectionAgent` | End-to-end planning, sequential task execution, reflection loop, tool dispatch |
| **Agent Tools** | [`app/agent/tools.py`](app/agent/tools.py) | `RequirementAnalyzerTool`, `DocumentStructureGeneratorTool`, `ContentGeneratorTool`, `DocumentGeneratorTool` | Four `BaseTool` implementations powering requirement extraction through `.docx` export |
| **Document Engine** | [`app/document/generator.py`](app/document/generator.py) | `DocxDocumentGenerator` | Executive `.docx` renderer with Deep Navy palette, callout boxes, and zebra tables |
| **LLM Abstraction** | [`app/llm/`](app/llm/) | `LLMProvider`, `OllamaProvider`, `MockLLMProvider`, `clean_llm_json` | Provider factory, Ollama `/api/generate` client, offline mock mode, JSON sanitization |
| **Auth & Security** | [`app/auth/`](app/auth/), [`app/core/security.py`](app/core/security.py) | `router`, `get_current_active_user`, `create_access_token` | `bcrypt` hashing (12 rounds), HS256 JWT bearer tokens, OAuth2 `/auth/token` flow |
| **TODO Domain** | [`app/todos/`](app/todos/) | `router`, `TodoCreate`, `TodoUpdate`, `TodoListResponse` | Authenticated per-user CRUD, status/priority filtering, keyword search, summary stats |
| **Data & Config** | [`app/db/`](app/db/), [`app/core/config.py`](app/core/config.py), [`app/models/schemas.py`](app/models/schemas.py) | `User`, `TodoItem`, `DocumentRecord`, `Settings`, `AgentResponse` | SQLAlchemy 2.0 ORM models, resilient connection pooling, Pydantic v2 contracts |
| **Test Suite** | [`tests/`](tests/) | [`tests/test_api.py`](tests/test_api.py), [`tests/test_auth.py`](tests/test_auth.py) | 16 FastAPI `TestClient` integration tests covering Agent, Docs, Auth, and TODO CRUD |

<details>
<summary><strong>Explore Full Project Directory Structure</strong></summary>

```text
E:\TODO App\
├── app\
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, lifespan DB init, /agent, /documents, /health*
│   ├── agent\
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Master workflow controller: Plan -> Execute -> Reflect -> DOCX
│   │   ├── planner.py           # Autonomous LLM planner generating dynamic tasks & assumptions
│   │   ├── executor.py          # Sequential task dispatcher with shared context dict
│   │   ├── tools.py             # 4 modular internal tools (Analyzer, Structure, Content, DOCX)
│   │   └── reflection.py        # Self-critique agent (1–10 scoring & 1-cycle auto-correction)
│   ├── auth\
│   │   ├── __init__.py
│   │   ├── dependencies.py      # Bearer JWT dependencies (required & optional user resolution)
│   │   ├── router.py            # /auth endpoints: register, login, token, me, change-password
│   │   └── schemas.py           # Pydantic v2 user & JWT token schemas
│   ├── core\
│   │   ├── __init__.py
│   │   ├── config.py            # Environment settings, Render detection & PostgreSQL URL normalizer
│   │   └── security.py          # bcrypt password hashing & PyJWT HS256 token sign/decode
│   ├── db\
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   ├── models.py            # ORM tables: users, todos, documents
│   │   └── session.py           # Pool config, Cloud PostgreSQL retry loop & SQLite fallback
│   ├── document\
│   │   ├── __init__.py
│   │   └── generator.py         # python-docx styling engine (Deep Navy #1E3A8A, callouts, tables)
│   ├── llm\
│   │   ├── __init__.py          # get_llm_provider() factory
│   │   ├── base.py              # Abstract LLMProvider, clean_llm_json(), parse_llm_json() + retry
│   │   ├── mock.py              # Deterministic zero-latency mock provider for tests & demos
│   │   └── ollama.py            # Local Ollama HTTP REST provider (/api/generate)
│   ├── models\
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic v2 schemas for AgentRequest, PlanOutput, AgentResponse
│   └── todos\
│       ├── __init__.py
│       ├── router.py            # /todos CRUD endpoints with status, priority & search filters
│       └── schemas.py           # TodoCreate, TodoUpdate, TodoOut, TodoListResponse
├── generated\                   # Output directory for generated .docx files
│   └── .gitkeep
├── tests\
│   ├── __init__.py
│   ├── test_api.py              # 9 tests: root, health, /agent execution, validation & downloads
│   └── test_auth.py             # 7 tests: registration, JWT login, OAuth2, profile & TODO CRUD
├── .env.example                 # Environment variable template
├── .gitignore                   # Ignores venv, .env, cache files, and generated/*.docx
├── .python-version              # Pinned Render Python version (3.11.9)
├── LICENSE                      # MIT License
├── render.yaml                  # Render Blueprint IaC (Web Service + Free PostgreSQL DB)
├── requirements.txt             # Python dependencies
└── run.py                       # CLI entrypoint with startup endpoint banner
```

</details>

### Task Executor Dispatch & Internal Tool Classification

| Task Type (`type`) | Executor Handler | Invoked Tool | Shared Context Reads | Shared Context Writes |
| :--- | :--- | :--- | :--- | :--- |
| `analysis` | `_handle_analysis` | `RequirementAnalyzerTool` | `request`, `assumptions` | `requirements` |
| `assumptions` | `_handle_assumptions` | — *(Plan aggregation)* | `assumptions`, `plan` | `assumptions` |
| `structure` | `_handle_structure` | `DocumentStructureGeneratorTool` | `document_type`, `requirements`, `title` | `structure` |
| `content` | `_handle_content` | `ContentGeneratorTool` | `request`, `document_type`, `title`, `assumptions`, `requirements`, `structure` | `content` |
| `recommendations` | `_handle_recommendations` | — *(Content synthesis check)* | `content` | — |
| `validation` | `_handle_validation` | — *(Structural integrity check)* | `content` | — |
| *Other / Custom* | `_handle_generic` | — *(Fallback handler)* | `task.description` | — |

### End-to-End Request, Auth & Persistence Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI (app/main.py)
    participant Auth as JWT Auth (dependencies.py)
    participant Orch as AgentOrchestrator
    participant LLM as LLMProvider (Ollama / Mock)
    participant Docx as DocxDocumentGenerator
    participant DB as SQLAlchemy (PostgreSQL / SQLite)

    Client->>API: POST /agent (optional Bearer JWT)
    API->>Auth: get_optional_current_user()
    Auth-->>API: User | None
    API->>Orch: run(payload.request)
    Orch->>LLM: Planner.plan() -> structured JSON
    LLM-->>Orch: PlanOutput (type, assumptions, tasks)
    loop For each planned task
        Orch->>LLM: Execute tool (Analyze -> Structure -> Content)
        LLM-->>Orch: Structured JSON artifact
    end
    Orch->>LLM: ReflectionAgent.evaluate()
    LLM-->>Orch: ReflectionResult (score 1–10, passed)
    opt If passed == false
        Orch->>LLM: ReflectionAgent.correct_content() [1 cycle]
        LLM-->>Orch: Enhanced GeneratedDocumentContent
    end
    Orch->>Docx: generate(content)
    Docx-->>Orch: generated/agent_document_*.docx
    Orch-->>API: AgentResponse
    API->>DB: Insert DocumentRecord (user_id, reflection_score)
    DB-->>API: Committed row
    API-->>Client: 200 OK (telemetry + download_url)
```

---

## 3. Technology Stack & DOCX Styling

### Stack Classification

| Category | Technology | Minimum / Target Spec | Purpose |
| :--- | :--- | :--- | :--- |
| **Runtime & API** | Python, FastAPI, Uvicorn | Python `3.11.9` / `3.14`, FastAPI `>=0.110.0`, Uvicorn `>=0.28.0` | Async REST framework, OpenAPI `/docs` & `/redoc`, ASGI server |
| **Validation** | Pydantic v2, `email-validator` | Pydantic `>=2.6.0`, `email-validator>=2.1.0` | Strict request/response contracts, length/regex validation, ORM serialization |
| **Database & ORM** | SQLAlchemy 2.0, `psycopg[binary]`, SQLite | SQLAlchemy `>=2.0.0`, `psycopg>=3.2.0` | Typed ORM (`Mapped`), PostgreSQL v3 pooling, local SQLite fallback |
| **Auth & Security** | PyJWT, `bcrypt`, `python-multipart` | PyJWT `>=2.8.0`, `bcrypt>=4.1.0`, `python-multipart>=0.0.9` | HS256 JWT tokens, 12-round password hashing (72-byte bounded), OAuth2 forms |
| **AI & Transport** | Ollama, `httpx`, `MockLLMProvider` | `httpx>=0.27.0`, `/api/generate` (120s timeout) | Local private LLM inference + zero-latency deterministic mock mode |
| **Document Engine** | `python-docx` | `python-docx>=1.1.0` | OOXML Word (`.docx`) assembly with custom cell shading & margins |
| **Testing & Ops** | `pytest`, `python-dotenv`, Render | `pytest>=8.0.0`, `python-dotenv>=1.0.0` | 16 automated tests, `.env` loading, Blueprint cloud IaC |

### DOCX Visual Styling Specification (`DocxDocumentGenerator`)

| Document Element | Typography & Sizing | Visual Token / Layout Rule |
| :--- | :--- | :--- |
| **Page Setup & Footer** | `Calibri` `8.5pt` footer | `1.0"` margins all around; right-aligned footer in Slate Muted (`#64748B`) |
| **Title & Subtitle** | `Calibri` `24pt` Bold / `12pt` Italic | Title in Deep Navy (`#1E3A8A`); subtitle in Royal Blue (`#2563EB`) + publish date metadata |
| **Headings (H1 / H2)** | `Calibri` `15pt` Bold / `12.5pt` Bold | H1 in Deep Navy (`#1E3A8A`); H2 in Royal Blue (`#2563EB`); `keep_with_next = True` |
| **Body & Lists** | `Calibri` `11pt` / `10.5pt` | Charcoal text (`#1F2937`), `1.15` line spacing, native `List Bullet` & `List Number` styles |
| **Assumptions Callout** | `Calibri` `10pt` | Single-cell `6.5"` shaded container (`#F1F5F9`) with internal cell padding |
| **Data Tables** | `Calibri` `10pt` Bold Header / `9.5pt` Cells | Deep Navy header (`#1E3A8A`, white text) + alternating `#F8FAFC` / `#FFFFFF` zebra rows |

---

## 4. Setup & Configuration

### Quick Setup

1. **Navigate to the project directory and set up a virtual environment:**

   <details>
   <summary><strong>OS-Specific Virtual Environment Commands (PowerShell / CMD / macOS & Linux)</strong></summary>

   **Windows (PowerShell):**
   ```powershell
   cd "E:\TODO App"
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **Windows (Command Prompt):**
   ```cmd
   cd "E:\TODO App"
   python -m venv .venv
   .venv\Scripts\activate.bat
   ```

   **macOS / Linux:**
   ```bash
   cd "TODO App"
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   </details>

2. **Install Python dependencies and initialize environment config:**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   ```

### Environment Variables Classification

| Category | Variable | Local Default (`.env.example` / Code) | Render Default (`render.yaml`) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Database** | `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/todo_db` | Linked from `todo-db` | Supports `postgres://` & `postgresql://` auto-normalization to `postgresql+psycopg://` |
| **Database** | `DB_FALLBACK_TO_SQLITE` | `true` *(when `RENDER` unset)* | `false` | Falls back to `sqlite:///./todo.db` locally if PostgreSQL is unreachable |
| **Database** | `DB_CONNECT_TIMEOUT` | `2` *(seconds)* | `15` *(seconds)* | PostgreSQL connection timeout per attempt |
| **Database** | `DB_MAX_RETRIES` | `1` *(attempt)* | `6` *(attempts)* | Connection retry count on startup |
| **Database** | `DB_RETRY_DELAY` | `1` *(second)* | `3` *(seconds)* | Wait duration between database retries |
| **Auth / JWT** | `SECRET_KEY` | Dev fallback in `config.py` | Auto-generated (`generateValue: true`) | Cryptographic key for HS256 JWT signing |
| **Auth / JWT** | `ALGORITHM` | `HS256` | `HS256` | JWT signing algorithm |
| **Auth / JWT** | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` *(24 hours)* | `1440` | JWT expiration window in minutes |
| **LLM** | `USE_MOCK_LLM` | `false` in `.env.example` (`true` for offline demo) | `true` | Enables zero-latency `MockLLMProvider` without Ollama |
| **LLM** | `LLM_PROVIDER` | `ollama` | `ollama` *(overridden by `USE_MOCK_LLM`)* | Explicit provider selector (`ollama` or `mock`) |
| **LLM** | `OLLAMA_BASE_URL` | `http://localhost:11434` | `http://localhost:11434` | Base URL for Ollama REST API |
| **LLM** | `OLLAMA_MODEL` | `llama3.2` | `llama3.2` | Target model name passed to `/api/generate` |
| **Server** | `HOST` / `PORT` | `0.0.0.0` / `8000` | `0.0.0.0` / `$PORT` | Uvicorn bind address and port |
| **Server** | `RELOAD` | `true` *(when `RENDER` unset)* | `false` | Enables Uvicorn hot reload during local development |
| **Server** | `LOG_LEVEL` | `INFO` | `INFO` | Python root logging level |
| **Storage** | `GENERATED_DIR` | `generated` | `generated` | Output directory for created `.docx` artifacts |

### Runtime Modes Comparison

| Feature / Setting | Instant Mock Mode (Local) | Local Ollama Inference | Render Cloud Production |
| :--- | :--- | :--- | :--- |
| **Config Flag** | `USE_MOCK_LLM=true` | `USE_MOCK_LLM=false` + `ollama pull llama3.2` | `RENDER` set + `USE_MOCK_LLM=true` |
| **LLM Backend** | `MockLLMProvider` (in-memory) | `OllamaProvider` (`localhost:11434`) | `MockLLMProvider` (via `render.yaml`) |
| **Response Latency** | `< 0.5s` (no GPU required) | Depends on local hardware (120s timeout) | Instantaneous cloud response |
| **Database Engine** | PostgreSQL or `todo.db` SQLite fallback | PostgreSQL or `todo.db` SQLite fallback | Managed Render PostgreSQL (`todo-db`, strict) |

---

## 5. Running Locally & Cloud Deployment

### Starting the Local Server

```bash
python run.py
```

The entrypoint prints the active service directory banner:

```text
======================================================================
Autonomous AI Document & TODO Agent Server Started
Root Endpoint:         http://127.0.0.1:8000/
Swagger Documentation: http://127.0.0.1:8000/docs
Health Check:          http://127.0.0.1:8000/health
Authentication:        http://127.0.0.1:8000/auth/register | /auth/login
TODOs API:             http://127.0.0.1:8000/todos
Listening Interface:   http://0.0.0.0:8000
======================================================================
```

> [!NOTE]
> Use `http://127.0.0.1:8000` or `http://localhost:8000` in your browser. Navigating directly to `0.0.0.0` triggers `ERR_ADDRESS_INVALID` on desktop browsers because `0.0.0.0` is a bind interface rather than a client target address.

### Interactive Browser Resources

| Resource | Local URL | Purpose |
| :--- | :--- | :--- |
| **Swagger UI** | `http://127.0.0.1:8000/docs` | Interactive API explorer, OAuth2 `Authorize` flow (`/auth/token`), and payload testing |
| **ReDoc** | `http://127.0.0.1:8000/redoc` | Clean API reference documentation |
| **Root Discovery** | `http://127.0.0.1:8000/` | Service version, status, and categorized endpoint map |
| **Liveness Probe** | `http://127.0.0.1:8000/health` | Lightweight uptime check (`{"status": "healthy"}`) |
| **DB Diagnostics** | `http://127.0.0.1:8000/health/detail` | Runs `SELECT 1` and reports connection status & masked dialect URL |

### Cloud Deployment on Render

[`render.yaml`](render.yaml) provides Infrastructure-as-Code provisioning for both the **FastAPI Web Service** (`doccie-agent`, Oregon free tier) and a **Managed PostgreSQL Database** (`todo-db`, database `todo_db`).

1. Push the repository to GitHub.
2. Open the **[Render Dashboard](https://dashboard.render.com/)** → **New +** → **Blueprint** and connect the repository.
3. Review the auto-provisioned resources from `render.yaml` (`todo-db` + `doccie-agent` with auto-generated `SECRET_KEY` and `DB_FALLBACK_TO_SQLITE="false"`).
4. Click **Apply**. On first startup, `lifespan` executes `init_db()` to create `users`, `todos`, and `documents` tables automatically.

<details>
<summary><strong>Manual Render Setup Instructions (Without Blueprint)</strong></summary>

1. **Provision PostgreSQL**: In Render, choose **New +** → **PostgreSQL** (`Name: todo-db`, `Database: todo_db`) and copy the **Internal Database URL**.
2. **Create Web Service**: Choose **New +** → **Web Service**, connect your repository, and apply:
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
   - **Environment Variables**: `DATABASE_URL` *(Internal URL)*, `SECRET_KEY` *(random)*, `DB_FALLBACK_TO_SQLITE=false`, `DB_CONNECT_TIMEOUT=15`, `DB_MAX_RETRIES=6`, `DB_RETRY_DELAY=3`, `USE_MOCK_LLM=true`, `PYTHON_VERSION=3.11.9`, `GENERATED_DIR=generated`, `LOG_LEVEL=INFO`.

</details>

### Runtime Database & LLM Routing Topology

```mermaid
flowchart LR
    Boot["App Startup / Request"] --> DBCheck{"DB Engine Init (app/db/session.py)"}
    DBCheck -- "Connects (Retries: 1 local / 6 Render)" --> PG[("PostgreSQL (psycopg v3 Pool)")]
    DBCheck -- "Unreachable + DB_FALLBACK_TO_SQLITE=true" --> SQLite[("Local SQLite (sqlite:///./todo.db)")]
    DBCheck -- "Unreachable + DB_FALLBACK_TO_SQLITE=false" --> FailDB["Raise Startup Error (Prevents Data Loss)"]

    Boot --> LLMCheck{"LLM Factory (app/llm/__init__.py)"}
    LLMCheck -- "USE_MOCK_LLM=true or LLM_PROVIDER=mock" --> Mock["MockLLMProvider (Instant Deterministic JSON)"]
    LLMCheck -- "Default (false)" --> Ollama["OllamaProvider (POST /api/generate)"]
```

---

## 6. Database Schema & Domain Classifications

### Relational Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ TODOS : "owns (CASCADE DELETE)"
    USERS ||--o{ DOCUMENTS : "creates (SET NULL)"

    USERS {
        int id PK
        string email UK "max 255, indexed"
        string username UK "max 100, indexed"
        string hashed_password "bcrypt hash"
        string full_name "nullable"
        bool is_active "default true"
        bool is_superuser "true for first user"
        datetime created_at
        datetime updated_at
    }

    TODOS {
        int id PK
        int user_id FK "NOT NULL"
        string title "max 255"
        text description "nullable"
        string status "default pending"
        string priority "default medium"
        datetime due_date "nullable"
        datetime created_at
        datetime updated_at
    }

    DOCUMENTS {
        int id PK
        int user_id FK "nullable"
        string title "max 255"
        string document_type "max 100"
        string filename "max 255"
        string download_url "max 255"
        text request_text
        string status "default completed"
        int reflection_score "nullable (1-10)"
        datetime created_at
    }
```

### Domain Classifications & Validation Rules

| Domain / Model | Field | Allowed Values / Constraints | Default / Notes |
| :--- | :--- | :--- | :--- |
| **`TodoItem` Status** | `status` | `pending`, `in_progress`, `completed`, `cancelled` | `pending`; filtered via `GET /todos?status=...` |
| **`TodoItem` Priority** | `priority` | `low`, `medium`, `high` | `medium`; filtered via `GET /todos?priority=...` |
| **`AgentRequest`** | `request` | `10–5000` characters | Returns HTTP `422` if empty or `< 10` chars |
| **`UserCreate`** | `username` | `3–50` chars, regex `^[a-zA-Z0-9_-]+$` | Unique; checked alongside `email` |
| **`UserCreate` / `PasswordChange`** | `password` | `6–72` characters | Truncated to 72 UTF-8 bytes for `bcrypt` (12 rounds) |
| **`DocumentSection`** | `level` | Integer `1–3` | Controls H1 (`1`) vs H2 (`2–3`) styling in DOCX |
| **`ReflectionResult`** | `score` | Integer `1–10` | `passed=false` triggers 1 correction cycle (`score = min(score + 3, 10)`) |

---

## 7. API Reference

```mermaid
xychart-beta
    title "API Surface Distribution Across Routers (18 Endpoints)"
    x-axis ["System & Health", "Agent & Docs", "Auth", "TODOs"]
    y-axis "Endpoint Count" 0 --> 8
    bar [4, 3, 6, 5]
```

### System & Discovery Endpoints

| Method | Path | Auth | Description | Key Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Public | Service metadata, version (`1.1.0`), and endpoint directory | `200 OK` JSON |
| `GET` | `/health` | Public | Lightweight liveness probe | `200 OK` `{"status": "healthy"}` |
| `GET` | `/health/detail` | Public | Runs `SELECT 1` against active DB and masks credentials | `200 OK` (`healthy` / `degraded`) |
| `GET` | `/favicon.ico` | Public | Silences automatic browser favicon requests | `204 No Content` |

### Autonomous Document Agent & Document Endpoints

| Method | Path | Auth | Input / Query | Response & Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/agent` | Optional JWT | JSON `{"request": "..."}` (`10–5000` chars) | `200` `AgentResponse` (links `user_id` if authenticated); `422` invalid input; `503` LLM down; `500` error |
| `GET` | `/documents` | Optional JWT | — | `200` list of `DocumentRecord` sorted newest-first (filters to user's docs + public docs if logged in) |
| `GET` | `/documents/{filename}` | Public | Path param matching `^[a-zA-Z0-9_\-\.]+\.docx$` | `200` `.docx` binary attachment; `400` invalid/traversal filename; `404` missing |

### Authentication & Profile Endpoints (`/auth`)

| Method | Path | Auth | Payload / Parameters | Behavior & Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Public | `email`, `username`, `password`, optional `full_name` | `201` `UserOut` (first registered user gets `is_superuser=True`); `400` duplicate email/username |
| `POST` | `/auth/login` | Public | JSON `username_or_email`, `password` | `200` `Token` (`access_token`, `bearer`, `expires_in`, `user`); `401` invalid credentials; `400` inactive |
| `POST` | `/auth/token` | Public | OAuth2 Form (`username`, `password`) | `200` `Token` (powers Swagger UI `Authorize` button) |
| `GET` | `/auth/me` | Bearer JWT | — | `200` `UserOut`; `401` missing/invalid token |
| `PUT` | `/auth/me` | Bearer JWT | Optional `full_name`, `email` | `200` updated `UserOut`; `400` duplicate email |
| `POST` | `/auth/change-password` | Bearer JWT | `old_password`, `new_password` | `200` confirmation message; `400` wrong current password |

### TODO Task Management Endpoints (`/todos`)

| Method | Path | Auth | Query / Payload | Behavior & Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/todos` | Bearer JWT | Query: `status`, `priority`, `search` (`ilike` on title/desc) | `200` `TodoListResponse` (`items`, `total`, `completed`, `pending`) scoped to owner |
| `POST` | `/todos` | Bearer JWT | `title`, optional `description`, `priority`, `status`, `due_date` | `201` created `TodoOut` |
| `GET` | `/todos/{todo_id}` | Bearer JWT | Path: `todo_id` | `200` `TodoOut`; `404` if missing or owned by another user |
| `PUT` | `/todos/{todo_id}` | Bearer JWT | Partial `TodoUpdate` (`title`, `description`, `status`, `priority`, `due_date`) | `200` updated `TodoOut`; `404` if not found |
| `DELETE` | `/todos/{todo_id}` | Bearer JWT | Path: `todo_id` | `200` `{"message": "Todo #<id> deleted successfully."}`; `404` if not found |

<details>
<summary><strong>Sample JSON Payloads (POST /agent, Auth Login & TODO Create)</strong></summary>

**`POST /agent` Request:**
```json
{
  "request": "Create a professional project proposal for developing an AI-powered customer support chatbot for a mid-sized e-commerce company."
}
```

**`POST /agent` Response (`200 OK`):**
```json
{
  "status": "completed",
  "message": "Agent completed the request successfully.",
  "request": "Create a professional project proposal for developing an AI-powered customer support chatbot for a mid-sized e-commerce company.",
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
    }
  ],
  "assumptions": [
    "The organization maintains an existing searchable customer support knowledge base and ticketing system.",
    "Initial launch focuses on web chat widget with CRM integration.",
    "The platform will support English at launch, with multi-lingual support in subsequent releases.",
    "Target initial containment rate is 65% for tier-1 repetitive inquiries."
  ],
  "execution": [ "...same TaskResult list as plan..." ],
  "reflection": {
    "passed": true,
    "score": 9,
    "issues": [],
    "improvements": [
      "Consider including post-launch SLA monitoring metrics."
    ]
  }
}
```

**`POST /auth/login` & `POST /todos` Requests:**
```json
// POST /auth/login
{
  "username_or_email": "testuser",
  "password": "StrongPassword123!"
}

// POST /todos (Authorization: Bearer <access_token>)
{
  "title": "Configure PostgreSQL Migration",
  "description": "Verify PostgreSQL database tables and connection pool.",
  "priority": "high",
  "status": "pending"
}
```

</details>

---

## 8. Verification & Automated Testing

### Functional Verification Scenarios

| Scenario | Prompt Characteristics | Planner Classification | Autonomous Resolution Behavior |
| :--- | :--- | :--- | :--- |
| **1. Standard Proposal** | Clear domain & target (e-commerce customer support AI chatbot) | `Project Proposal` (6 tasks, 4 assumptions) | Produces 4 rich sections + SLA/timeline tables, passes reflection (`9/10`), exports `.docx` |
| **2. Ambiguous Helpdesk** | Under-specified college helpdesk with limited budget, 3-month cap & undecided stack | `Implementation Plan` (6 tasks, 4–5 assumptions) | Synthesizes open-source LLM & hybrid hosting assumptions, 12-week roadmap & budget table |

### Running the Test Suite

```bash
python -m pytest -v
```

`tests/test_api.py` automatically sets `USE_MOCK_LLM=true` so all **16 automated tests** run deterministically offline (`16 passed` across `test_api.py` and `test_auth.py`).

<details>
<summary><strong>Complete 16-Test Automated Coverage Matrix (9 API/Agent + 7 Auth/TODO)</strong></summary>

| # | Test Suite | Test Function | Target | Verified Behavior |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `test_api.py` | `test_get_root` | `GET /` | Returns `200` with service metadata and discovered endpoints |
| 2 | `test_api.py` | `test_get_health` | `GET /health` | Returns `200` and `{"status": "healthy"}` |
| 3 | `test_api.py` | `test_post_agent_empty_request_rejected` | `POST /agent` | Rejects `""` payload with HTTP `422` |
| 4 | `test_api.py` | `test_post_agent_too_short_request_rejected` | `POST /agent` | Rejects `< 10` char string (`"too short"`) with HTTP `422` |
| 5 | `test_api.py` | `test_post_agent_missing_payload_rejected` | `POST /agent` | Rejects empty JSON `{}` with HTTP `422` |
| 6 | `test_api.py` | `test_post_agent_valid_request_execution` | `POST /agent` + Download | End-to-end plan, reflection (`>= 7`), `.docx` file write & binary download |
| 7 | `test_api.py` | `test_post_agent_ambiguous_request_handles_assumptions` | `POST /agent` | Formulates `>= 3` assumptions for under-specified college helpdesk prompt |
| 8 | `test_api.py` | `test_download_document_not_found` | `GET /documents/{file}` | Returns HTTP `404` for nonexistent `.docx` file |
| 9 | `test_api.py` | `test_download_document_path_traversal_rejected` | `GET /documents/{file}` | Rejects encoded `..%2Fevil.docx` traversal with `400` or `404` |
| 10 | `test_auth.py` | `test_register_new_user` | `POST /auth/register` | Creates user, excludes `hashed_password`, handles existing test DB rows |
| 11 | `test_auth.py` | `test_register_duplicate_email_fails` | `POST /auth/register` | Rejects duplicate email registration with HTTP `400` |
| 12 | `test_auth.py` | `test_login_success_and_invalid_password` | `POST /auth/login` | Verifies login by username/email (`200`) and rejects bad password (`401`) |
| 13 | `test_auth.py` | `test_oauth2_form_login` | `POST /auth/token` | Verifies Swagger UI OAuth2 password form token issuance |
| 14 | `test_auth.py` | `test_get_current_user_profile` | `GET /auth/me` | Validates Bearer JWT authorization and user payload |
| 15 | `test_auth.py` | `test_get_profile_unauthorized` | `GET /auth/me` | Rejects unauthenticated profile access with HTTP `401` |
| 16 | `test_auth.py` | `test_todos_crud_lifecycle` | `/todos` & `/todos/{id}` | Full authenticated Create → List → Update → Get → Delete → Verify `404` flow |

</details>

---

## 9. Engineering Design & Resilience

### Reflection & Self-Check Decision Matrix

| Evaluation Condition | `passed` Flag | Orchestrator Action | Resulting Score |
| :--- | :---: | :--- | :--- |
| `score >= 7` **and** `issues == []` | `true` | Proceed directly to `DocumentGeneratorTool` (`.docx` export) | Unchanged (`7–10`) |
| `score < 7` **or** `len(issues) > 0` | `false` | Execute **1 autonomous correction cycle** via `ContentGeneratorTool` with explicit issue/improvement feedback | `min(score + 3, 10)`, `passed = true` |
| LLM JSON evaluation fails | Fallback | `_heuristic_evaluate()` checks summary length (`>= 50` chars), section count (`>= 2`), and table presence | Base `9` minus deductions (floor `1`) |

### Architectural Tradeoffs & Resilience Controls

| Area | Challenge / Dilemma | Implemented Solution | Source Reference |
| :--- | :--- | :--- | :--- |
| **Control Flow vs. Autonomy** | Pure LLM autonomy risks infinite loops or malformed structures; rigid templates cannot adapt to varied document types | Hybrid split: LLM handles cognitive synthesis (planning, assumptions, writing, critique); Python controls execution, schemas, and `.docx` rendering | [`orchestrator.py`](app/agent/orchestrator.py), [`executor.py`](app/agent/executor.py) |
| **Malformed LLM JSON** | Small local models (`llama3.2`, etc.) frequently emit Markdown fences, preamble text, trailing commas, or smart quotes | `clean_llm_json()` strips fences/preamble/trailing commas; `parse_llm_json()` normalizes quotes and retries once via `LLMProvider.generate_json()` | [`base.py`](app/llm/base.py) |
| **LLM Availability & CI** | Local Ollama pulls or GPU limits can block testing or offline evaluation | Abstract `LLMProvider` with zero-latency `MockLLMProvider` enabled via `USE_MOCK_LLM=true` | [`__init__.py`](app/llm/__init__.py), [`mock.py`](app/llm/mock.py) |
| **Cloud DB vs. Local Dev** | Cloud PostgreSQL connections can drop or cold-start, while missing local Postgres shouldn't halt local dev | Retry loop + `pool_pre_ping=True` + URL normalization (`psycopg` v3); automatic SQLite fallback locally (`RENDER` unset), strict fail on Render | [`session.py`](app/db/session.py), [`config.py`](app/core/config.py) |
| **Download Security** | Arbitrary path parameters on `/documents/{filename}` risk directory traversal | Strict regex enforcement (`^[a-zA-Z0-9_\-\.]+\.docx$`) returning HTTP `400` on invalid filenames and `404` when absent | [`main.py`](app/main.py) |

---

## 10. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

---

## Contact Information

### Madhan Mohan Reddy

- **Email**: <madhanmohanreddyperam06@gmail.com>
- **Mobile**: +91 9110395993

---
<div align="center">
© 2026 Doccie. All rights reserved.
</div>
