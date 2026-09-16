# ML Research Experiments & Notebooks

This directory is strictly designated for **offline research, training pipelines, and exploratory data analysis (EDA)**.

## Directory Structure
- `notebooks/`: Jupyter/IPython notebooks for EDA, feature exploration, and model prototyping.
- `datasets/`: Benchmark and synthetic SME datasets (Sales, Inventory, Finance, HR).
- `experiments/`: Training scripts, hyperparameter tuning runs, and validation loss optimization.

> **Note:** Production inference code lives in `backend/app/ml/` and only loads finalized serialized model weights from `models/artifacts/`.
