# ResumeIQ — Local Setup & Quickstart Guide

Follow these instructions to run **ResumeIQ** locally.

---

## 1. Environment Setup

Copy the template config file:
```bash
cp .env.example .env
```

Set your required environment variables in `.env`:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/resumeiq`
- `GOOGLE_API_KEY=your_gemini_api_key_here`

---

## 2. PostgreSQL with pgvector Setup

Start PostgreSQL 16 with `pgvector` enabled (e.g. via Docker):
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

## 3. Backend Setup & Alembic Migrations

From the `backend/` directory:
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations (enables pgvector extension & tables)
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Interactive API docs are available at `http://localhost:8000/docs`.

---

## 4. Frontend Setup

From the `frontend/` directory in a new terminal window:
```bash
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 5. Running the Backend Test Suite

Run the full 23-test suite covering agent tools, RAG search, ATS parsing, SSE streaming, and supervisor state tracking:
```bash
cd backend
python -m pytest app/tests/
```
