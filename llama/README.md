# Local LLaMA-7B Integration

This directory manages configuration, prompts, and local runtime bindings for the local LLaMA-7B model.

## Two Core Roles:

### 1. Semantic Preprocessing Copilot
- Interprets unfamiliar ERP/CRM tabular column schemas.
- Maps raw headers to standard business terms.
- Infers semantic types and recommends deterministic cleaning operations.

### 2. Explanation Layer
- Ingests prediction results, SHAP feature importance attributions, and business scores.
- Translates analytical metrics into natural-language business explanations and executive briefings.

> **Methodological Boundary:** LLaMA does **NOT** compute numerical predictions, BP scores, or SHAP values.
