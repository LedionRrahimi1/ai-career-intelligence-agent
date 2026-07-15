# AI Career Intelligence Agent

Production-ready MVP of a **multi-agent** career platform: CV analysis, job matching, resume optimization, interview coaching, and personalized career roadmaps.

**CareerIQ** is not a simple chatbot — specialized agents collaborate through an orchestrator, each with input → reasoning → tools → output, plus RAG over a career knowledge base.

## Architecture

```
User
  │
React Frontend (Vite + TypeScript + Tailwind)
  │
FastAPI Backend
  │
AI Agent Orchestrator
  ├── CV Analyzer Agent
  ├── Job Matching Agent
  ├── Resume Optimization Agent
  ├── Interview Coach Agent
  └── Career Roadmap Agent
  │
Knowledge Base (RAG + embeddings)
  │
LLM (OpenAI) or Demo heuristics
```

## Features

| Agent | What it does |
|-------|----------------|
| **CV Analyzer** | PDF upload → text extraction → structured candidate profile |
| **Job Matching** | Profile + job description → match score, strengths, gaps, recommendations |
| **Resume Optimizer** | ATS-friendly bullet rewrites + keyword suggestions |
| **Interview Coach** | HR / Technical / AI Engineer simulations with scored feedback |
| **Career Roadmap** | Month-by-month plan from current skills → target role |

## Tech stack

- **Frontend:** React, TypeScript, Tailwind CSS, React Router
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite by default; PostgreSQL / Supabase via `DATABASE_URL`
- **AI:** OpenAI chat + embeddings; offline demo mode without an API key
- **Docs:** PDF parsing via `pypdf`
- **RAG:** In-memory vector retrieval over curated career knowledge

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/health

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### 3. Optional OpenAI

In `backend/.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Without a key, agents run in **demo mode** (heuristic + lexicon tools) so the full product is still demoable.

### 4. PostgreSQL / Supabase

```env
DATABASE_URL=postgresql://user:password@host:5432/career_intelligence
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/users` | Create / upsert user |
| `GET` | `/api/users/{id}/dashboard` | Dashboard insights |
| `POST` | `/api/cvs/upload` | Upload PDF + CV agent |
| `POST` | `/api/analyses/match` | Job matching agent |
| `POST` | `/api/resume/optimize` | Resume optimization agent |
| `POST` | `/api/interviews/start` | Start interview session |
| `POST` | `/api/interviews/evaluate` | Score answers |
| `POST` | `/api/roadmaps/generate` | Career roadmap agent |

## Database schema

- **users** — email, name, target role
- **cvs** — file path, extracted text, profile JSON
- **analyses** — match score, strengths, weaknesses, recommendations
- **interview_sessions** — questions, answers, feedback
- **career_roadmaps** — target role, skill gaps, monthly plan

## Project structure

```
backend/
  app/
    agents/          # CV, Job, Resume, Interview, Career + Orchestrator
    api/             # FastAPI routes
    core/            # Config + database
    models/          # SQLAlchemy models
    rag/             # Knowledge base + retrieval
    schemas/         # Pydantic contracts
    services/        # LLM, PDF parser, serialization
frontend/
  src/
    pages/           # Landing, Dashboard, CV Analyzer, Interview, Roadmap
    components/
    lib/             # API client + session
```

## Demo walkthrough

1. Open the landing page → create a workspace with your email  
2. **CV Analyzer** → upload a PDF resume  
3. Paste a job description → run Job Matching  
4. Optionally run Resume Optimizer  
5. **Interview Coach** → pick interview type → answer → get scores  
6. **Career Roadmap** → set target role → generate monthly plan  

## License

MIT — built as a portfolio-grade AI engineering project.
