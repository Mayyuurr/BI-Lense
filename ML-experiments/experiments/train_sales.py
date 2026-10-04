"""Offline Training Pipeline for Sales & Demand Forecasting.

Trains:
1. Random Forest Regressor
2. XGBoost Regressor
3. PyTorch ANN (Multi-Layer Perceptron)

Optimizes ensemble weights w_RF, w_XGB, w_ANN using SciPy SLSQP:
    min MSE(w_RF * y_RF + w_XGB * y_XGB + w_ANN * y_ANN, y_true)
    subject to w_RF + w_XGB + w_ANN = 1, w_i >= 0

Saves all trained artifacts and evaluation metrics to models/artifacts/sales/.
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import xgboost as xgb

# Set deterministic random seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "ML-experiments" / "datasets" / "sales.csv"
ARTIFACTS_DIR = BASE_DIR / "models" / "artifacts" / "sales"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Feature definitions conforming to docs/DATA_DICTIONARY.md
NUMERIC_FEATURES = [
    "sales_lag_1",
    "sales_lag_7",
    "sales_lag_30",
    "rolling_avg_30",
    "discount_rate",
    "promotional_flag",
    "unit_price",
    "day_of_week",
    "month",
]
CATEGORICAL_FEATURES = ["product_category"]
TARGET_COL = "next_period_demand"


class DemandANN(nn.Module):
    """PyTorch Multi-Layer Perceptron for numerical demand regression."""

    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculates MAE, RMSE, R2, and MAPE."""
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    
    # Safe MAPE avoiding division by zero
    non_zero_mask = y_true > 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mape_percent": round(mape, 2),
    }


def train_ann(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 40,
    batch_size: int = 128,
    lr: float = 0.008,
) -> DemandANN:
    """Trains PyTorch ANN model with early stopping."""
    input_dim = X_train.shape[1]
    model = DemandANN(input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    val_x_tensor = torch.tensor(X_val, dtype=torch.float32)
    val_y_tensor = torch.tensor(y_val, dtype=torch.float32)

    best_val_loss = float("inf")
    best_weights = None

    for epoch in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_preds = model(val_x_tensor)
            val_loss = criterion(val_preds, val_y_tensor).item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_weights:
        model.load_state_dict(best_weights)

    return model


def optimize_ensemble_weights(
    y_val: np.ndarray,
    p_rf: np.ndarray,
    p_xgb: np.ndarray,
    p_ann: np.ndarray,
) -> Tuple[float, float, float]:
    """Optimizes w_RF, w_XGB, w_ANN using SLSQP constrained optimization."""
    preds_matrix = np.column_stack([p_rf, p_xgb, p_ann])

    def objective(w: np.ndarray) -> float:
        y_ens = np.dot(preds_matrix, w)
        return float(np.mean((y_val - y_ens) ** 2))

    init_w = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
    bounds = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    res = minimize(objective, init_w, method="SLSQP", bounds=bounds, constraints=constraints)

    if res.success:
        w_rf, w_xgb, w_ann = res.x
        return float(w_rf), float(w_xgb), float(w_ann)
    return 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0


def main():
    print("=================================================================", flush=True)
    print("       BI-Lense Sales & Demand ML Training & SLSQP Optimization  ", flush=True)
    print("=================================================================", flush=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Sales dataset not found at {DATA_PATH}. Run generate_synthetic_data.py first.")

    print(f"[*] Loading dataset from {DATA_PATH.name}...", flush=True)
    df = pd.read_csv(DATA_PATH)
    print(f"[+] Loaded {len(df)} records.", flush=True)

    # Split features and target
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET_COL].values

    # Train / Val / Test split (70% / 15% / 15%)
    X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=SEED
    )
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp_raw, y_temp, test_size=0.50, random_state=SEED
    )

    print(f"[+] Splits -> Train: {len(X_train_raw)}, Val: {len(X_val_raw)}, Test: {len(X_test_raw)}", flush=True)

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    print("[*] Fitting preprocessing transformers...", flush=True)
    X_train = preprocessor.fit_transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)

    # 1. Random Forest
    print("[*] Training Random Forest Regressor...", flush=True)
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=SEED,
        n_jobs=1,
    )
    rf.fit(X_train, y_train)

    # 2. XGBoost
    print("[*] Training XGBoost Regressor...", flush=True)
    xgb_model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=SEED,
        n_jobs=1,
    )
    xgb_model.fit(X_train, y_train)

    # 3. PyTorch ANN
    print("[*] Training PyTorch Multi-Layer Perceptron (ANN)...", flush=True)
    ann = train_ann(X_train, y_train, X_val, y_val, epochs=40, batch_size=128, lr=0.008)

    # Predict on Validation set for SLSQP Weight Optimization
    val_pred_rf = rf.predict(X_val)
    val_pred_xgb = xgb_model.predict(X_val)
    ann.eval()
    with torch.no_grad():
        val_pred_ann = ann(torch.tensor(X_val, dtype=torch.float32)).numpy()

    print("[*] Optimizing ensemble weights using SLSQP on validation set...")
    w_rf, w_xgb, w_ann = optimize_ensemble_weights(y_val, val_pred_rf, val_pred_xgb, val_pred_ann)
    print(f"[+] Optimal Ensemble Weights -> w_RF: {w_rf:.4f}, w_XGB: {w_xgb:.4f}, w_ANN: {w_ann:.4f} (Sum: {w_rf+w_xgb+w_ann:.4f})")

    # Final Evaluation on Held-Out Test Set
    print("\n[*] Evaluating models on held-out test set...")
    test_pred_rf = rf.predict(X_test)
    test_pred_xgb = xgb_model.predict(X_test)
    with torch.no_grad():
        test_pred_ann = ann(torch.tensor(X_test, dtype=torch.float32)).numpy()

    test_pred_ensemble = (w_rf * test_pred_rf) + (w_xgb * test_pred_xgb) + (w_ann * test_pred_ann)

    metrics_rf = calculate_metrics(y_test, test_pred_rf)
    metrics_xgb = calculate_metrics(y_test, test_pred_xgb)
    metrics_ann = calculate_metrics(y_test, test_pred_ann)
    metrics_ensemble = calculate_metrics(y_test, test_pred_ensemble)

    all_metrics = {
        "random_forest": metrics_rf,
        "xgboost": metrics_xgb,
        "ann": metrics_ann,
        "hybrid_ensemble": metrics_ensemble,
        "ensemble_weights": {
            "w_rf": round(w_rf, 4),
            "w_xgb": round(w_xgb, 4),
            "w_ann": round(w_ann, 4),
        },
    }

    print("\n" + "=" * 65)
    print(f"{'Model':<20} | {'MAE':<8} | {'RMSE':<8} | {'R2':<8} | {'MAPE (%)':<8}")
    print("-" * 65)
    print(f"{'Random Forest':<20} | {metrics_rf['mae']:<8} | {metrics_rf['rmse']:<8} | {metrics_rf['r2']:<8} | {metrics_rf['mape_percent']:<8}")
    print(f"{'XGBoost':<20} | {metrics_xgb['mae']:<8} | {metrics_xgb['rmse']:<8} | {metrics_xgb['r2']:<8} | {metrics_xgb['mape_percent']:<8}")
    print(f"{'PyTorch ANN':<20} | {metrics_ann['mae']:<8} | {metrics_ann['rmse']:<8} | {metrics_ann['r2']:<8} | {metrics_ann['mape_percent']:<8}")
    print("-" * 65)
    print(f"{'Hybrid Ensemble':<20} | {metrics_ensemble['mae']:<8} | {metrics_ensemble['rmse']:<8} | {metrics_ensemble['r2']:<8} | {metrics_ensemble['mape_percent']:<8}")
    print("=" * 65)

    # Save artifacts
    print("\n[*] Saving model artifacts to models/artifacts/sales/...")
    joblib.dump(rf, ARTIFACTS_DIR / "rf_model.joblib")
    xgb_model.save_model(str(ARTIFACTS_DIR / "xgb_model.json"))
    torch.save(ann.state_dict(), ARTIFACTS_DIR / "ann_model.pt")
    joblib.dump(preprocessor, ARTIFACTS_DIR / "preprocessor.joblib")

    with open(ARTIFACTS_DIR / "ensemble_weights.json", "w") as f:
        json.dump(all_metrics["ensemble_weights"], f, indent=2)

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    print("[OK] All Sales ML artifacts successfully exported!")
    print("=================================================================")


if __name__ == "__main__":
    main()
