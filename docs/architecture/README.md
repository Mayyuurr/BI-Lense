# System Architecture Documentation

## Core Architectural Flow

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
Automated Ensemble Weight Optimization (Constrained Validation-Loss)
      ↓
Domain Predictions (Sales, Inventory, Finance, HR)
      ↓
Business Scores (S, I, F, E) → Composite Score (Bp)
      ↓
SHAP Explainability Layer
      ↓
Local LLaMA-7B Explanation Layer (Natural Language Synthesis)
      ↓
Decision Support Interface & Alerts
```

## Architectural Decoupling
- **Frontend**: Next.js App Router, TypeScript, Tailwind CSS.
- **Backend**: FastAPI modular monolith with service boundaries.
- **ML Experimentation**: Separated in `ML-experiments/` to keep research separate from production inference artifacts.
- **LLM Runtime**: Local LLaMA abstraction for copilot preprocessing and explanation narratives (no automatic model downloads).
