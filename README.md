# BI-Lense: AI-Driven Decision Intelligence & Decision Support Platform for SMEs

A modular AI-driven decision intelligence and decision support platform designed specifically for Small and Medium Enterprises (SMEs).

---

## 1. High-Level Architecture & Flow

```
ERP / CRM Data
      ↓
Data Ingestion & Storage
      ↓
Local LLaMA-7B Semantic Preprocessing Copilot
      ↓
Deterministic Data Cleaning & Feature Engineering
      ↓
Hybrid ML Prediction (Random Forest + XGBoost + ANN)
      ↓
Automated Ensemble Weight Optimization (Constrained Validation Loss)
      ↓
Domain Predictions (Sales, Inventory, Finance, HR)
      ↓
Business Scores (S, I, F, E) → Business Performance Score (Bp)
      ↓
SHAP Explainability Layer
      ↓
Local LLaMA-7B Explanation Layer (Natural Language Synthesis)
      ↓
Decision Support Interface & Real-time Alerts
```

---

## 2. Repository Organization

```
BI-Lense/
├── backend/                 # FastAPI Python backend modular monolith
│   ├── app/                 # Routers, Services, ML, LLM, Scoring, Database
│   ├── alembic/             # Database migrations
│   ├── tests/               # Pytest suite
│   ├── requirements.txt     # Python dependencies
│   └── pyproject.toml       # Backend package configuration
├── frontend/                # Next.js 14 App Router, TypeScript, Tailwind CSS
│   ├── app/                 # App Router pages (/dashboard, /sales, /inventory, etc.)
│   ├── components/          # Layout, KPI, Charts, Alerts, Common components
│   ├── lib/api/             # Typed API client layer connecting to backend
│   └── types/               # TypeScript domain and API schemas
├── docs/                    # System documentation (FRS, Architecture, ML, API)
├── ML-experiments/          # Offline research notebooks and training pipelines
├── models/                  # Serialized ML model binaries and pipeline artifacts
├── llama/                   # Local LLaMA runtime configurations and prompt templates
├── database/                # Database migrations and seed fixtures
├── docker/                  # Dockerfiles for backend and frontend
├── data/                    # Local storage placeholders
└── docker-compose.yml       # Local development multi-container orchestration
```

---

## 3. Quickstart & Running Locally

### Backend Setup (FastAPI)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### Frontend Setup (Next.js)

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```
- Dashboard Interface: `http://localhost:3000`

---

## 4. Environment Variables

| Variable | Location | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `backend/.env` | `postgresql://...:5432/bilense_db` | PostgreSQL connection string |
| `LLAMA_ENABLED` | `backend/.env` | `false` | Enable local LLaMA copilot/explanation |
| `LLAMA_BASE_URL` | `backend/.env` | `http://localhost:11434` | Endpoint for local LLM runtime |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | `http://localhost:8000/api/v1` | Backend API gateway |

---

## 5. Current Implementation Status

### ✅ Initialized
- **Backend Architecture**: Layered modular structure (`API → Services → ML/Domain → DB`), Alembic migrations, database models, error handlers, and 100% passing test suite.
- **Frontend Architecture**: Next.js App Router, TypeScript, Tailwind CSS, Sidebar/Header layout, domain shells (`/dashboard`, `/sales`, `/inventory`, `/finance`, `/hr`, `/crm`, `/procurement`, `/insights`, `/reports`), typed API abstraction client.
- **Project Structure**: Organized directories for `docs/`, `ML-experiments/`, `models/`, `llama/`, `database/`, and `docker/`.

### ⏳ Not Implemented Yet (Methodological Boundaries)
- Actual trained ML model weights (RF, XGBoost, ANN).
- Constrained validation-loss optimization runs on empirical datasets.
- Finalized numerical business scoring formulas ($S, I, F, E$) and calibrated $B_p$ thresholds.
- Live local LLaMA-7B runtime inference and automated downloads.
- Real-time streaming or multi-agent architectures.
