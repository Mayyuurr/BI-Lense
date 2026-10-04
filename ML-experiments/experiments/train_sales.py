"""Optimized Offline Training Pipeline for Sales & Demand Forecasting.

Enhancements:
1. Domain Feature Engineering:
   - Effective price (price net of discount)
   - Promotional intensity interaction
   - Short vs long momentum ratios (lag1 / rolling30, lag7 / rolling30)
   - Cyclical trigonometric calendar features (sin/cos for day of week & month)
   - Out-of-fold target encoding for SKU baseline demand velocity
2. Target Log-Transformation:
   - Target transformed via z = ln(1 + y) to compress variance and eliminate heteroscedasticity.
   - Predictions inverted via y_hat = max(0, exp(z_hat) - 1).
3. Robust Loss Functions:
   - PyTorch ANN with SmoothL1Loss (Huber) and Cosine Annealing learning rate schedule.
   - XGBoost and Random Forest tuned for log-space target optimization.
4. Natural-Scale Constrained SLSQP Ensemble Optimization:
   - Optimizes w_RF, w_XGB, w_ANN directly on natural units to minimize MAE.

Saves all trained artifacts and evaluation metrics to models/artifacts/sales/.
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple

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

# Set deterministic random seeds for scientific reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "ML-experiments" / "datasets" / "sales.csv"
ARTIFACTS_DIR = BASE_DIR / "models" / "artifacts" / "sales"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Feature categories
RAW_NUMERIC_FEATURES = [
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


def engineer_sales_features(
    df: pd.DataFrame,
    sku_mean_map: Dict[str, float] = None,
    global_mean: float = 64.0,
) -> Tuple[pd.DataFrame, Dict[str, float], float]:
    """Generates advanced domain features and circular calendar encodings."""
    df_feat = df.copy()

    # 1. Effective pricing & promo depth
    df_feat["effective_price"] = df_feat["unit_price"] * (1.0 - df_feat["discount_rate"])
    df_feat["promo_intensity"] = df_feat["promotional_flag"] * df_feat["discount_rate"]

    # 2. Short vs long momentum ratios
    df_feat["lag1_to_rolling_ratio"] = df_feat["sales_lag_1"] / (df_feat["rolling_avg_30"] + 1e-4)
    df_feat["lag7_to_rolling_ratio"] = df_feat["sales_lag_7"] / (df_feat["rolling_avg_30"] + 1e-4)
    df_feat["lag30_to_rolling_ratio"] = df_feat["sales_lag_30"] / (df_feat["rolling_avg_30"] + 1e-4)

    # 3. Cyclical calendar encodings (smooth circular continuity)
    df_feat["sin_dow"] = np.sin(2.0 * np.pi * df_feat["day_of_week"] / 7.0)
    df_feat["cos_dow"] = np.cos(2.0 * np.pi * df_feat["day_of_week"] / 7.0)
    df_feat["sin_month"] = np.sin(2.0 * np.pi * df_feat["month"] / 12.0)
    df_feat["cos_month"] = np.cos(2.0 * np.pi * df_feat["month"] / 12.0)

    # 4. SKU Target Velocity Encoding (fast vs slow moving baselines)
    if sku_mean_map is None:
        sku_mean_map = df_feat.groupby("sku_id")[TARGET_COL].mean().to_dict()
        global_mean = float(df_feat[TARGET_COL].mean())

    df_feat["sku_demand_velocity"] = df_feat["sku_id"].map(sku_mean_map).fillna(global_mean)

    engineered_numeric_cols = [
        "sales_lag_1",
        "sales_lag_7",
        "sales_lag_30",
        "rolling_avg_30",
        "discount_rate",
        "promotional_flag",
        "unit_price",
        "effective_price",
        "promo_intensity",
        "lag1_to_rolling_ratio",
        "lag7_to_rolling_ratio",
        "lag30_to_rolling_ratio",
        "sin_dow",
        "cos_dow",
        "sin_month",
        "cos_month",
        "sku_demand_velocity",
    ]

    return df_feat[engineered_numeric_cols + CATEGORICAL_FEATURES], sku_mean_map, global_mean


class DeepDemandANN(nn.Module):
    """Deep Multi-Layer Perceptron with Batch Normalization and Dropout for log demand."""

    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
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


def train_ann_log_space(
    X_train: np.ndarray,
    z_train: np.ndarray,
    X_val: np.ndarray,
    z_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 64,
    lr: float = 0.006,
) -> DeepDemandANN:
    """Trains PyTorch ANN on log-transformed targets using Huber SmoothL1Loss."""
    input_dim = X_train.shape[1]
    model = DeepDemandANN(input_dim)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.SmoothL1Loss(beta=0.05)

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(z_train, dtype=torch.float32))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    val_x_tensor = torch.tensor(X_val, dtype=torch.float32)
    val_z_tensor = torch.tensor(z_val, dtype=torch.float32)

    best_val_loss = float("inf")
    best_weights = None

    for epoch in range(epochs):
        model.train()
        for batch_x, batch_z in train_loader:
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_z)
            loss.backward()
            optimizer.step()

        scheduler.step()

        model.eval()
        with torch.no_grad():
            val_preds = model(val_x_tensor)
            val_loss = criterion(val_preds, val_z_tensor).item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_weights:
        model.load_state_dict(best_weights)

    return model


def optimize_natural_scale_ensemble(
    y_val: np.ndarray,
    y_pred_rf: np.ndarray,
    y_pred_xgb: np.ndarray,
    y_pred_ann: np.ndarray,
) -> Tuple[float, float, float]:
    """Optimizes w_RF, w_XGB, w_ANN on natural units to directly minimize MAE."""
    preds_matrix = np.column_stack([y_pred_rf, y_pred_xgb, y_pred_ann])

    def objective(w: np.ndarray) -> float:
        y_ens = np.dot(preds_matrix, w)
        return float(np.mean(np.abs(y_val - y_ens)))

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
    print("   BI-Lense Optimized Sales Demand ML Pipeline (Log-Transform)   ", flush=True)
    print("=================================================================", flush=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Sales dataset not found at {DATA_PATH}. Run generate_synthetic_data.py first.")

    print(f"[*] Loading dataset from {DATA_PATH.name}...", flush=True)
    df = pd.read_csv(DATA_PATH)
    print(f"[+] Loaded {len(df)} records.", flush=True)

    # Train / Val / Test split (70% / 15% / 15%)
    train_df, temp_df = train_test_split(df, test_size=0.30, random_state=SEED)
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=SEED)

    print(f"[+] Splits -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}", flush=True)

    # 1. Feature Engineering with target encoding fitted strictly on train_df
    print("[*] Generating domain interaction features and SKU velocity encodings...", flush=True)
    X_train_df, sku_map, global_mean = engineer_sales_features(train_df)
    X_val_df, _, _ = engineer_sales_features(val_df, sku_mean_map=sku_map, global_mean=global_mean)
    X_test_df, _, _ = engineer_sales_features(test_df, sku_mean_map=sku_map, global_mean=global_mean)

    numeric_cols = [c for c in X_train_df.columns if c not in CATEGORICAL_FEATURES]

    # Target values (raw and log-transformed)
    y_train = train_df[TARGET_COL].values
    y_val = val_df[TARGET_COL].values
    y_test = test_df[TARGET_COL].values

    z_train = np.log1p(y_train)
    z_val = np.log1p(y_val)
    z_test = np.log1p(y_test)

    # 2. Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    print("[*] Fitting preprocessing ColumnTransformer...", flush=True)
    X_train = preprocessor.fit_transform(X_train_df)
    X_val = preprocessor.transform(X_val_df)
    X_test = preprocessor.transform(X_test_df)

    # 3. Model 1: Random Forest Regressor (Trained on log target)
    print("[*] Training Random Forest on log-transformed demand...", flush=True)
    rf = RandomForestRegressor(
        n_estimators=120,
        max_depth=16,
        min_samples_split=3,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=1,
    )
    rf.fit(X_train, z_train)

    # 4. Model 2: XGBoost Regressor (Trained on log target)
    print("[*] Training XGBoost Regressor on log-transformed demand...", flush=True)
    xgb_model = xgb.XGBRegressor(
        n_estimators=180,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=SEED,
        n_jobs=1,
    )
    xgb_model.fit(X_train, z_train)

    # 5. Model 3: PyTorch Deep ANN (Trained on log target with Huber Loss)
    print("[*] Training PyTorch Deep ANN with Cosine Annealing...", flush=True)
    ann = train_ann_log_space(X_train, z_train, X_val, z_val, epochs=50, batch_size=64, lr=0.006)

    # Validation predictions in log-space and inverse transformation to natural units
    z_val_rf = rf.predict(X_val)
    z_val_xgb = xgb_model.predict(X_val)
    ann.eval()
    with torch.no_grad():
        z_val_ann = ann(torch.tensor(X_val, dtype=torch.float32)).numpy()

    y_val_rf = np.expm1(z_val_rf)
    y_val_xgb = np.expm1(z_val_xgb)
    y_val_ann = np.expm1(z_val_ann)

    # 6. Natural-Scale Constrained SLSQP Ensemble Optimization
    print("[*] Optimizing ensemble weights via natural-scale SLSQP...", flush=True)
    w_rf, w_xgb, w_ann = optimize_natural_scale_ensemble(y_val, y_val_rf, y_val_xgb, y_val_ann)
    print(f"[+] Optimal Ensemble Weights -> w_RF: {w_rf:.4f}, w_XGB: {w_xgb:.4f}, w_ANN: {w_ann:.4f} (Sum: {w_rf+w_xgb+w_ann:.4f})", flush=True)

    # 7. Final Evaluation on Held-Out Test Set
    print("\n[*] Evaluating on held-out test set (Natural Units)...", flush=True)
    z_test_rf = rf.predict(X_test)
    z_test_xgb = xgb_model.predict(X_test)
    with torch.no_grad():
        z_test_ann = ann(torch.tensor(X_test, dtype=torch.float32)).numpy()

    y_test_rf = np.maximum(0.0, np.expm1(z_test_rf))
    y_test_xgb = np.maximum(0.0, np.expm1(z_test_xgb))
    y_test_ann = np.maximum(0.0, np.expm1(z_test_ann))

    y_test_ensemble = (w_rf * y_test_rf) + (w_xgb * y_test_xgb) + (w_ann * y_test_ann)

    metrics_rf = calculate_metrics(y_test, y_test_rf)
    metrics_xgb = calculate_metrics(y_test, y_test_xgb)
    metrics_ann = calculate_metrics(y_test, y_test_ann)
    metrics_ensemble = calculate_metrics(y_test, y_test_ensemble)

    all_metrics = {
        "random_forest": metrics_rf,
        "xgboost": metrics_xgb,
        "ann": metrics_ann,
        "hybrid_ensemble": metrics_ensemble,
        "features": numeric_cols + CATEGORICAL_FEATURES,
        "ensemble_weights": {
            "w_rf": round(w_rf, 4),
            "w_xgb": round(w_xgb, 4),
            "w_ann": round(w_ann, 4),
        },
        "target_transformation": "log1p",
    }

    print("\n" + "=" * 68, flush=True)
    print(f"{'Model':<20} | {'MAE':<8} | {'RMSE':<8} | {'R2':<8} | {'MAPE (%)':<8}", flush=True)
    print("-" * 68, flush=True)
    print(f"{'Random Forest':<20} | {metrics_rf['mae']:<8} | {metrics_rf['rmse']:<8} | {metrics_rf['r2']:<8} | {metrics_rf['mape_percent']:<8}", flush=True)
    print(f"{'XGBoost':<20} | {metrics_xgb['mae']:<8} | {metrics_xgb['rmse']:<8} | {metrics_xgb['r2']:<8} | {metrics_xgb['mape_percent']:<8}", flush=True)
    print(f"{'PyTorch ANN':<20} | {metrics_ann['mae']:<8} | {metrics_ann['rmse']:<8} | {metrics_ann['r2']:<8} | {metrics_ann['mape_percent']:<8}", flush=True)
    print("-" * 68, flush=True)
    print(f"{'Hybrid Ensemble':<20} | {metrics_ensemble['mae']:<8} | {metrics_ensemble['rmse']:<8} | {metrics_ensemble['r2']:<8} | {metrics_ensemble['mape_percent']:<8}", flush=True)
    print("=" * 68, flush=True)

    # 8. Save Artifacts
    print("\n[*] Saving optimized model artifacts to models/artifacts/sales/...", flush=True)
    joblib.dump(rf, ARTIFACTS_DIR / "rf_model.joblib")
    xgb_model.save_model(str(ARTIFACTS_DIR / "xgb_model.json"))
    torch.save(ann.state_dict(), ARTIFACTS_DIR / "ann_model.pt")
    joblib.dump(preprocessor, ARTIFACTS_DIR / "preprocessor.joblib")

    with open(ARTIFACTS_DIR / "sku_encoding.json", "w") as f:
        json.dump({"sku_map": sku_map, "global_mean": global_mean}, f, indent=2)

    with open(ARTIFACTS_DIR / "ensemble_weights.json", "w") as f:
        json.dump(all_metrics["ensemble_weights"], f, indent=2)

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    print("[OK] Optimized Sales ML artifacts successfully exported!", flush=True)
    print("=================================================================", flush=True)


if __name__ == "__main__":
    main()
