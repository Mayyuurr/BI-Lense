# API Specifications & Contracts

The BI-Lense backend exposes endpoints under the `/api/v1` namespace:

## Endpoints Summary

- `GET /health`: Core health status and database connectivity indicator.
- `POST /api/v1/datasets/ingest`: Raw file ingestion, semantic schema interpretation, and deterministic cleaning.
- `POST /api/v1/predictions/run`: Domain prediction inference via hybrid base models and ensemble aggregator.
- `POST /api/v1/scores/compute`: Calculates domain performance scores (S, I, F, E) and composite Business Performance Score ($B_p$).
- `POST /api/v1/explanations/generate`: Synthesizes SHAP feature importance into natural-language executive explanations via local LLaMA-7B.
- `POST /api/v1/insights/procurement/restock-check`: Evaluates deterministic restocking-trigger logic for procurement items.
- `POST /api/v1/insights/recommendations`: Generates prioritized business intervention recommendations.
