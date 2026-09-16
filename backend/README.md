# BI-Lense Backend: AI-Driven Decision Intelligence Platform for SMEs

A modular backend platform designed to provide automated decision intelligence, predictive analytics, domain scoring, and explainable AI insights for Small and Medium Enterprises (SMEs).

---

## High-Level System Flow

```
ERP/CRM Data
    ↓
Data Ingestion & Storage
    ↓
Local LLaMA-7B Semantic Preprocessing (Copilot)
    ↓
Deterministic Data Cleaning & Feature Engineering
    ↓
Hybrid ML Prediction (Random Forest + XGBoost + ANN)
    ↓
Automated Ensemble Weight Optimization
    ↓
Domain Predictions (Sales, Inventory, Finance, HR)
    ↓
Business Scores (S, I, F, E) → Business Performance Score (Bp)
    ↓
SHAP Explainability
    ↓
Local LLaMA-7B Explanation Layer
    ↓
Decision Support Interface & Alerts
```

---

## Module Architecture

```
backend/
├── app/
│   ├── api/                     # FastAPI endpoint routers (v1)
│   │   ├── datasets.py          # Ingestion & semantic schema analysis
│   │   ├── predictions.py       # Domain ML predictions
│   │   ├── scores.py            # Business domain scores & Bp score
│   │   ├── explanations.py      # SHAP & LLaMA narrative explanations
│   │   └── insights.py          # Actionable recommendations & restock triggers
│   ├── core/                    # Core configuration, logging, database
│   │   ├── config.py            # Pydantic settings & env management
│   │   ├── database.py          # SQLAlchemy engine, session & get_db dependency
│   │   └── logging_config.py    # Structured logging configuration
│   ├── data/                    # Data ingestion & deterministic processing
│   │   ├── ingestion/           # CSV & Database connector interfaces
│   │   ├── preprocessing/       # Rule-based cleaning & deduplication
│   │   └── feature_engineering/ # Domain feature matrix transformation pipelines
│   ├── explainability/          # Explainable AI layer
│   │   └── shap_engine.py       # TreeSHAP & Model-agnostic SHAP abstractions
│   ├── llm/                     # Local LLaMA-7B integration
│   │   ├── llama_client.py      # Local LLM runtime HTTP client abstraction
│   │   ├── semantic_copilot.py  # Schema understanding & datatype inference
│   │   └── explanation.py       # Decision narrative synthesis from predictions & SHAP
│   ├── ml/                      # Machine learning prediction layer
│   │   ├── base.py              # Base model wrappers (RF, XGBoost, ANN)
│   │   ├── ensemble/            # Constrained validation-loss weight optimizer
│   │   ├── sales/               # Next-period demand forecasting interface
│   │   ├── inventory/           # Stockout probability estimation interface
│   │   ├── finance/             # 30-day operating cash deficit estimation interface
│   │   └── hr/                  # Task delay / backlog probability interface
│   ├── models/                  # Database ORM models
│   │   └── database_models.py   # Datasets, predictions, scores, audit schemas
│   ├── recommendations/         # Decision support & rules
│   │   └── engine.py            # Recommendations & procurement restock triggers
│   ├── scoring/                 # Domain performance & Bp scoring
│   │   ├── sales_score.py       # S (Sales Score) calculator interface
│   │   ├── inventory_score.py   # I (Inventory Score) calculator interface
│   │   ├── finance_score.py     # F (Finance Score) calculator interface
│   │   ├── employee_score.py    # E (Employee Score) calculator interface
│   │   └── bp_score.py          # Composite Bp = (S + I + F + E) / 4 aggregator
│   ├── services/                # Business orchestration layer
│   └── main.py                  # FastAPI application entrypoint & healthcheck
├── alembic/                     # Database migration environment
├── tests/                       # Automated pytest suite
├── .env.example                 # Example environment variables
├── requirements.txt             # Python dependencies
└── pyproject.toml               # Project metadata & test configuration
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10 to 3.12
- PostgreSQL (optional for basic startup; healthcheck functions without DB)
- Local LLaMA runtime (e.g., Ollama / llama.cpp / vLLM) if testing LLM features

### 2. Environment Setup

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` inside the `backend` directory:

```bash
cp .env.example .env
```

Key environment configurations:
- `DATABASE_URL`: PostgreSQL connection string.
- `LLAMA_ENABLED`: Set to `true` when a local LLaMA instance is running.
- `LLAMA_BASE_URL`: Endpoint for local LLM runtime (default: `http://localhost:11434`).

---

## Running the Application

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative Documentation (ReDoc): `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

---

## Running Database Migrations

Apply Alembic migrations once PostgreSQL is running:

```bash
alembic upgrade head
```

---

## Running Automated Tests

Run the test suite using `pytest`:

```bash
pytest
```

---

## Methodological Boundaries & Intentional Scope Limits

The following components are **intentionally not implemented** in this foundation phase:
1. **No Automatic Model Downloads**: Local LLaMA is connected via an abstraction interface.
2. **No Invented Formulas or Fake Predictions**: Scoring thresholds, domain score formulas, and ML weights are not fabricated or hardcoded.
3. **No Real-Time Streaming / Microservices**: The backend is structured as a clean modular monolith suitable for research validation.
4. **No Autonomous Decision-Making**: The system generates decision support intelligence for SME managers, not autonomous actuation.
5. **Procurement Simplicity**: Uses deterministic restocking triggers rather than a separate ML model.
6. **Separation of Experiments**: Offline ML experiments remain separate from production API inference.
