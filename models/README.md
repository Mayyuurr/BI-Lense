# Model Artifacts Directory

This folder stores serialized machine learning model binaries and fitted pipeline transformers produced by offline experiments in `ML-experiments/`.

## Expected Artifact Format:
- `sales/`
  - `rf_model.joblib`
  - `xgb_model.json`
  - `ann_model.pt`
  - `ensemble_weights.json`
- `inventory/`
  - `rf_model.joblib`
  - `xgb_model.json`
  - `ann_model.pt`
  - `ensemble_weights.json`
- `finance/`
  - `rf_model.joblib`
  - `xgb_model.json`
  - `ann_model.pt`
  - `ensemble_weights.json`
- `hr/`
  - `rf_model.joblib`
  - `xgb_model.json`
  - `ann_model.pt`
  - `ensemble_weights.json`

> **Note:** Model weights and large binaries are ignored by git via `.gitignore`.
