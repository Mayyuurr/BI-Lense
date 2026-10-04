"""Offline Training Pipeline for Inventory Health & Stockout Probability Prediction.

Trains:
1. Random Forest Classifier
2. XGBoost Classifier
3. PyTorch Binary Classifier ANN

Optimizes ensemble weights w_RF, w_XGB, w_ANN using SciPy SLSQP minimizing Log-Loss:
    min LogLoss(w_RF * P_RF + w_XGB * P_XGB + w_ANN * P_ANN, y_true)
    subject to w_RF + w_XGB + w_ANN = 1, w_i >= 0

Saves all trained artifacts and evaluation metrics to models/artifacts/inventory/.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
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
DATA_PATH = BASE_DIR / "ML-experiments" / "datasets" / "inventory.csv"
ARTIFACTS_DIR = BASE_DIR / "models" / "artifacts" / "inventory"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Feature definitions conforming to docs/DATA_DICTIONARY.md
RAW_NUMERIC_FEATURES = [
    "current_stock",
    "reorder_level",
    "safety_stock",
    "lead_time_days",
    "historical_delivery_delay_days",
    "inventory_turnover_ratio",
    "predicted_sales_demand",
]
TARGET_COL = "stockout_before_delivery"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes domain-specific inventory ratios."""
    df_feat = df[RAW_NUMERIC_FEATURES].copy()
    
    # Expected demand during replenishment lead time + delivery delay
    lead_time_demand = (df_feat["predicted_sales_demand"] / 7.0) * (
        df_feat["lead_time_days"] + df_feat["historical_delivery_delay_days"]
    )
    
    # Ratio of current stock to required lead time replenishment volume
    df_feat["buffer_coverage_ratio"] = df_feat["current_stock"] / (lead_time_demand + 1e-4)
    
    # Ratio of safety stock buffer to total reorder threshold
    df_feat["safety_stock_ratio"] = df_feat["safety_stock"] / (df_feat["reorder_level"] + 1e-4)
    
    return df_feat


class InventoryANN(nn.Module):
    """PyTorch Multi-Layer Perceptron for binary stockout classification."""

    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 48),
            nn.BatchNorm1d(48),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(48, 24),
            nn.ReLU(),
            nn.Linear(24, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def calculate_classification_metrics(y_true: np.ndarray, p_pred: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """Calculates Accuracy, Precision, Recall, F1, ROC-AUC, Brier Score, and Log-Loss."""
    y_pred_binary = (p_pred >= threshold).astype(int)
    
    # Safe clipping for log loss
    p_clipped = np.clip(p_pred, 1e-6, 1.0 - 1e-6)
    
    acc = float(accuracy_score(y_true, y_pred_binary))
    prec = float(precision_score(y_true, y_pred_binary, zero_division=0))
    rec = float(recall_score(y_true, y_pred_binary, zero_division=0))
    f1 = float(f1_score(y_true, y_pred_binary, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, p_pred))
    brier = float(brier_score_loss(y_true, p_pred))
    loss = float(log_loss(y_true, p_clipped))

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "log_loss": round(loss, 4),
    }


def train_ann_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.008,
) -> InventoryANN:
    """Trains PyTorch binary classification ANN with BCELoss."""
    input_dim = X_train.shape[1]
    model = InventoryANN(input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCELoss()

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


def optimize_classification_weights(
    y_val: np.ndarray,
    p_rf: np.ndarray,
    p_xgb: np.ndarray,
    p_ann: np.ndarray,
) -> Tuple[float, float, float]:
    """Optimizes w_RF, w_XGB, w_ANN using SLSQP minimizing Log-Loss on validation set."""
    preds_matrix = np.column_stack([p_rf, p_xgb, p_ann])

    def objective(w: np.ndarray) -> float:
        p_ens = np.dot(preds_matrix, w)
        p_ens_clipped = np.clip(p_ens, 1e-6, 1.0 - 1e-6)
        return float(log_loss(y_val, p_ens_clipped))

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
    print("    BI-Lense Inventory Stockout ML Training & SLSQP Optimization ", flush=True)
    print("=================================================================", flush=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Inventory dataset not found at {DATA_PATH}. Run generate_synthetic_data.py first.")

    print(f"[*] Loading dataset from {DATA_PATH.name}...", flush=True)
    df = pd.read_csv(DATA_PATH)
    print(f"[+] Loaded {len(df)} inventory audit records.", flush=True)

    # Feature engineering
    X_df = engineer_features(df)
    y = df[TARGET_COL].values
    feature_names = list(X_df.columns)

    # Train / Val / Test split (70% / 15% / 15%)
    X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
        X_df, y, test_size=0.30, random_state=SEED, stratify=y
    )
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp_raw, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
    )

    print(f"[+] Splits -> Train: {len(X_train_raw)}, Val: {len(X_val_raw)}, Test: {len(X_test_raw)}", flush=True)

    # Preprocessing
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val = scaler.transform(X_val_raw)
    X_test = scaler.transform(X_test_raw)

    # 1. Random Forest Classifier
    print("[*] Training Random Forest Classifier...", flush=True)
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=4,
        random_state=SEED,
        n_jobs=1,
    )
    rf.fit(X_train, y_train)

    # 2. XGBoost Classifier
    print("[*] Training XGBoost Classifier...", flush=True)
    xgb_model = xgb.XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=SEED,
        n_jobs=1,
    )
    xgb_model.fit(X_train, y_train)

    # 3. PyTorch ANN Classifier
    print("[*] Training PyTorch ANN Classifier...", flush=True)
    ann = train_ann_classifier(X_train, y_train, X_val, y_val, epochs=50, batch_size=32, lr=0.008)

    # Predict probabilities on Validation set for SLSQP Weight Optimization
    val_p_rf = rf.predict_proba(X_val)[:, 1]
    val_p_xgb = xgb_model.predict_proba(X_val)[:, 1]
    ann.eval()
    with torch.no_grad():
        val_p_ann = ann(torch.tensor(X_val, dtype=torch.float32)).numpy()

    print("[*] Optimizing ensemble weights using SLSQP on validation set...")
    w_rf, w_xgb, w_ann = optimize_classification_weights(y_val, val_p_rf, val_p_xgb, val_p_ann)
    print(f"[+] Optimal Ensemble Weights -> w_RF: {w_rf:.4f}, w_XGB: {w_xgb:.4f}, w_ANN: {w_ann:.4f} (Sum: {w_rf+w_xgb+w_ann:.4f})")

    # Final Evaluation on Held-Out Test Set
    print("\n[*] Evaluating models on held-out test set...")
    test_p_rf = rf.predict_proba(X_test)[:, 1]
    test_p_xgb = xgb_model.predict_proba(X_test)[:, 1]
    with torch.no_grad():
        test_p_ann = ann(torch.tensor(X_test, dtype=torch.float32)).numpy()

    test_p_ensemble = (w_rf * test_p_rf) + (w_xgb * test_p_xgb) + (w_ann * test_p_ann)

    metrics_rf = calculate_classification_metrics(y_test, test_p_rf)
    metrics_xgb = calculate_classification_metrics(y_test, test_p_xgb)
    metrics_ann = calculate_classification_metrics(y_test, test_p_ann)
    metrics_ensemble = calculate_classification_metrics(y_test, test_p_ensemble)

    all_metrics = {
        "random_forest": metrics_rf,
        "xgboost": metrics_xgb,
        "ann": metrics_ann,
        "hybrid_ensemble": metrics_ensemble,
        "features": feature_names,
        "ensemble_weights": {
            "w_rf": round(w_rf, 4),
            "w_xgb": round(w_xgb, 4),
            "w_ann": round(w_ann, 4),
        },
    }

    print("\n" + "=" * 75)
    print(f"{'Model':<18} | {'Acc':<6} | {'Prec':<6} | {'Recall':<6} | {'F1':<6} | {'AUC':<6} | {'Brier':<6}")
    print("-" * 75)
    print(f"{'Random Forest':<18} | {metrics_rf['accuracy']:<6} | {metrics_rf['precision']:<6} | {metrics_rf['recall']:<6} | {metrics_rf['f1_score']:<6} | {metrics_rf['roc_auc']:<6} | {metrics_rf['brier_score']:<6}")
    print(f"{'XGBoost':<18} | {metrics_xgb['accuracy']:<6} | {metrics_xgb['precision']:<6} | {metrics_xgb['recall']:<6} | {metrics_xgb['f1_score']:<6} | {metrics_xgb['roc_auc']:<6} | {metrics_xgb['brier_score']:<6}")
    print(f"{'PyTorch ANN':<18} | {metrics_ann['accuracy']:<6} | {metrics_ann['precision']:<6} | {metrics_ann['recall']:<6} | {metrics_ann['f1_score']:<6} | {metrics_ann['roc_auc']:<6} | {metrics_ann['brier_score']:<6}")
    print("-" * 75)
    print(f"{'Hybrid Ensemble':<18} | {metrics_ensemble['accuracy']:<6} | {metrics_ensemble['precision']:<6} | {metrics_ensemble['recall']:<6} | {metrics_ensemble['f1_score']:<6} | {metrics_ensemble['roc_auc']:<6} | {metrics_ensemble['brier_score']:<6}")
    print("=" * 75)

    # Save artifacts
    print("\n[*] Saving model artifacts to models/artifacts/inventory/...")
    joblib.dump(rf, ARTIFACTS_DIR / "rf_model.joblib")
    xgb_model.save_model(str(ARTIFACTS_DIR / "xgb_model.json"))
    torch.save(ann.state_dict(), ARTIFACTS_DIR / "ann_model.pt")
    joblib.dump(scaler, ARTIFACTS_DIR / "preprocessor.joblib")

    with open(ARTIFACTS_DIR / "features.json", "w") as f:
        json.dump(feature_names, f, indent=2)

    with open(ARTIFACTS_DIR / "ensemble_weights.json", "w") as f:
        json.dump(all_metrics["ensemble_weights"], f, indent=2)

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    print("[OK] All Inventory ML artifacts successfully exported!")
    print("=================================================================")


if __name__ == "__main__":
    main()
