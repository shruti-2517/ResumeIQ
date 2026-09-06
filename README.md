# ResumeIQ 🎯 — Autonomous Multi-Agent AI Document Intelligence Platform

**ResumeIQ** is an AI Resume Intelligence platform powered by an **Autonomous Multi-Agent System** using Google Gemini Function Calling (`google-genai` SDK), PostgreSQL `pgvector` RAG retrieval, an ATS Readability Layout Hazards Engine, Job Description Keyword Heatmaps, AI Authenticity Guardrails, Server-Sent Events (SSE) progress streaming, and a Multi-Agent Supervisor Gateway.

---

## 🌟 Architecture Highlights

### 🤖 1. Autonomous Multi-Agent System
- **Resume Auditor Agent**: Executes native function calls (`tool_check_ats_readability`, `tool_retrieve_vector_benchmarks`, `tool_extract_keyword_gaps`) to score 7 core resume dimensions, analyze document hazards, and calibrate fresher/experienced profiles.
- **Company Analyst Agent**: Performs target company intelligence analysis and computes hiring verdicts (`GO`, `HOLD`, `REWORK`) with actionable gap analysis.
- **Resume Rewriter Agent**: Executes multi-pass reflective bullet rewrites with an explicit **Authenticity Guardrail Layer** detecting metric hallucinations.
- **Career Coach Agent**: Uses live tools (`tool_search_learning_resources`, `tool_fetch_certification_paths`) to construct ordered 4-week improvement roadmaps linked directly to real courses (Coursera, Udemy) and certification milestones.
- **Multi-Agent Supervisor Gateway**: Tracks agent state transitions, execution time, total invocations, and maintains a centralized tool execution audit trail exposed via `/api/resume/{session_id}/agent/logs`.

### ⚡ 2. Vector RAG & PostgreSQL Architecture
- **Native `pgvector` Storage**: Embedded PostgreSQL vector store (`Vector(768)`) with HNSW cosine distance indexing (`0002_vector_embeddings.py`).
- **Gemini Embeddings**: Generates 768-dimensional embeddings using `text-embedding-004`.
- **Single DB Architecture**: Consolidated into PostgreSQL for atomic write transactions, snapshot history, and SQL analytics.

### 📊 3. Intelligence UI & SSE Streaming
- **ATS Health Gauge**: Displays layout parsing scores and multi-column hazard warnings (`AtsHealthCard.jsx`).
- **JD Keyword Heatmap**: Real-time visual matrix highlighting Matched 🟢, Missing 🔴, and Partial 🟡 technical skills (`JdHeatmap.jsx`).
- **Authenticity Guardrail Drawer**: Visual side-by-side diff comparing original bullet points against rewritten versions with hallucinated metric flags (`AuthenticityDiff.jsx`).
- **SSE Progress Streaming**: Real-time event broadcasting (`GET /{session_id}/analyze/stream`) with progress steps.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, React Router v6, Vanilla CSS |
| **Backend Framework** | FastAPI (Python 3.11/3.12), Uvicorn, AsyncIO, SSE Starlette |
| **AI / LLM Engine** | Google Gemini (`google-genai` SDK), Function Calling (`types.Tool`), `gemini-2.5-flash` |
| **Embeddings & RAG** | Google `text-embedding-004`, PostgreSQL `pgvector`, HNSW Cosine Index |
| **Database & ORM** | PostgreSQL 16 (`pgvector/pgvector:pg16`), SQLAlchemy (Asyncpg), Alembic |
| **Testing** | Pytest, Pytest-AnyIO, AsyncMock |

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16** with `pgvector` extension enabled (e.g., via Docker container `pgvector/pgvector:pg16`).
- **Google Gemini API Key**

---

### 1. Database Setup (PostgreSQL with pgvector)

Using Docker:
```bash
docker run -d \
  --name resumeiq-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=resumeiq \
  -p 5433:5432 \
  pgvector/pgvector:pg16
```

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment & activate
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env and set your GOOGLE_API_KEY and DATABASE_URL
# Example: DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/resumeiq

# Run Alembic Database Migrations
alembic upgrade head

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```
Backend API interactive docs: `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
# Open a new terminal in the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend Web UI: `http://localhost:5173`

---

## 🧪 Running the Backend Test Suite

The test suite covers RAG vector retrieval, ATS hazard analysis, agent function calling, stream generators, and supervisor state tracking:

```bash
cd backend
python -m pytest app/tests/
```

**Output:**
```text
collected 23 items

app\tests\test_agent_supervisor.py ....                                  [ 17%]
app\tests\test_analysis.py ...                                           [ 30%]
app\tests\test_ats.py ...                                                [ 43%]
app\tests\test_auditor_agent.py ....                                     [ 60%]
app\tests\test_coach_agent.py .....                                      [ 82%]
app\tests\test_rag.py ...                                                [ 95%]
app\tests\test_streaming.py .                                            [100%]

============================= 23 passed in 3.53s ==============================
```

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/resume/upload` | Upload resume file (`.pdf` / `.docx`) and parse text |
| `POST` | `/api/resume/{session_id}/analyze` | Trigger Autonomous Resume Auditor Agent evaluation |
| `GET` | `/api/resume/{session_id}/analyze/stream` | Stream real-time analysis execution steps via SSE |
| `POST` | `/api/resume/{session_id}/analyze/company` | Trigger Company Analyst Agent targeting specific company |
| `POST` | `/api/resume/{session_id}/rewrite` | Trigger Resume Rewriter Agent with Authenticity Guardrails |
| `POST` | `/api/resume/{session_id}/roadmap` | Trigger Career Coach Agent searching live learning resources |
| `GET` | `/api/resume/{session_id}/agent/logs` | Retrieve Multi-Agent Supervisor Gateway state & tool execution logs |
| `GET` | `/api/resume/benchmark` | SQL aggregation analytics across session analyses |
