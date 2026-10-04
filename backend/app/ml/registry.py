"""In-Memory Machine Learning Model Registry.

Loads and caches trained model artifacts, preprocessors, and optimal ensemble
weights from models/artifacts/ across all business domains.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import torch
import torch.nn as nn

from app.core.logging_config import logger
from app.ml.base import (
    BaseMLModel,
    ModelType,
    PyTorchModelWrapper,
    SklearnModelWrapper,
    XGBoostModelWrapper,
)
from app.ml.ensemble import EnsembleWeights


# PyTorch ANN Architectures matching trained offline experiments
class SalesDeepDemandANN(nn.Module):
    """Deep Multi-Layer Perceptron for Sales Demand log-prediction."""

    def __init__(self, input_dim: int = 22):
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


class InventoryANN(nn.Module):
    """Multi-Layer Perceptron for Inventory Stockout binary probability."""

    def __init__(self, input_dim: int = 9):
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


class ModelRegistry:
    """Singleton registry managing in-memory cached model artifacts."""

    _instance: Optional["ModelRegistry"] = None

    def __init__(self) -> None:
        # Base paths
        # backend root -> project root -> models/artifacts
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.artifacts_dir = self.base_dir / "models" / "artifacts"

        # Domain artifact caches
        self.sales_artifacts: Dict[str, Any] = {}
        self.inventory_artifacts: Dict[str, Any] = {}

        self._is_loaded = False

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_all_artifacts()
        return cls._instance

    def load_all_artifacts(self) -> None:
        """Loads available domain model artifacts into memory."""
        self._load_sales_artifacts()
        self._load_inventory_artifacts()
        self._is_loaded = True

    def _load_sales_artifacts(self) -> None:
        sales_dir = self.artifacts_dir / "sales"
        if not sales_dir.exists():
            logger.warning(f"Sales artifacts directory not found at {sales_dir}")
            return

        try:
            logger.info("Loading Sales ML model artifacts...")
            # 1. Scikit-Learn Random Forest
            rf_wrapper = SklearnModelWrapper(ModelType.RANDOM_FOREST, is_classifier=False)
            rf_wrapper.load(str(sales_dir / "rf_model.joblib"))

            # 2. XGBoost Regressor
            xgb_wrapper = XGBoostModelWrapper(ModelType.XGBOOST, is_classifier=False)
            xgb_wrapper.load(str(sales_dir / "xgb_model.json"))

            # 3. Preprocessor
            preprocessor = joblib.load(str(sales_dir / "preprocessor.joblib"))

            # 4. PyTorch Deep ANN
            # Determine input dimension from fitted preprocessor
            input_dim = preprocessor.transform(
                pd_dummy := __import__("pandas").DataFrame([{
                    "sales_lag_1": 50.0, "sales_lag_7": 50.0, "sales_lag_30": 50.0,
                    "rolling_avg_30": 50.0, "discount_rate": 0.0, "promotional_flag": 0,
                    "unit_price": 50.0, "effective_price": 50.0, "promo_intensity": 0.0,
                    "lag1_to_rolling_ratio": 1.0, "lag7_to_rolling_ratio": 1.0, "lag30_to_rolling_ratio": 1.0,
                    "sin_dow": 0.0, "cos_dow": 1.0, "sin_month": 0.0, "cos_month": 1.0,
                    "sku_demand_velocity": 64.0, "product_category": "Hardware"
                }])
            ).shape[1]

            ann_model = SalesDeepDemandANN(input_dim=input_dim)
            ann_wrapper = PyTorchModelWrapper(ann_model, is_classifier=False)
            ann_wrapper.load(str(sales_dir / "ann_model.pt"))

            # 5. Ensemble Weights
            with open(sales_dir / "ensemble_weights.json", "r") as f:
                weights_dict = json.load(f)
                ensemble_weights = EnsembleWeights(
                    w_rf=float(weights_dict["w_rf"]),
                    w_xgb=float(weights_dict["w_xgb"]),
                    w_ann=float(weights_dict["w_ann"]),
                )

            # 6. SKU encoding map
            with open(sales_dir / "sku_encoding.json", "r") as f:
                sku_enc_data = json.load(f)

            self.sales_artifacts = {
                "rf_model": rf_wrapper,
                "xgb_model": xgb_wrapper,
                "ann_model": ann_wrapper,
                "preprocessor": preprocessor,
                "ensemble_weights": ensemble_weights,
                "sku_map": sku_enc_data.get("sku_map", {}),
                "global_mean": float(sku_enc_data.get("global_mean", 64.0)),
            }
            logger.info("Sales ML artifacts loaded successfully.")
        except Exception as e:
            logger.error(f"Failed loading Sales ML artifacts: {e}")

    def _load_inventory_artifacts(self) -> None:
        inv_dir = self.artifacts_dir / "inventory"
        if not inv_dir.exists():
            logger.warning(f"Inventory artifacts directory not found at {inv_dir}")
            return

        try:
            logger.info("Loading Inventory ML model artifacts...")
            # 1. Scikit-Learn Random Forest Classifier
            rf_wrapper = SklearnModelWrapper(ModelType.RANDOM_FOREST, is_classifier=True)
            rf_wrapper.load(str(inv_dir / "rf_model.joblib"))

            # 2. XGBoost Classifier
            xgb_wrapper = XGBoostModelWrapper(ModelType.XGBOOST, is_classifier=True)
            xgb_wrapper.load(str(inv_dir / "xgb_model.json"))

            # 3. Preprocessor (StandardScaler)
            preprocessor = joblib.load(str(inv_dir / "preprocessor.joblib"))

            # 4. PyTorch ANN Classifier
            ann_model = InventoryANN(input_dim=9)
            ann_wrapper = PyTorchModelWrapper(ann_model, is_classifier=True)
            ann_wrapper.load(str(inv_dir / "ann_model.pt"))

            # 5. Ensemble Weights
            with open(inv_dir / "ensemble_weights.json", "r") as f:
                weights_dict = json.load(f)
                ensemble_weights = EnsembleWeights(
                    w_rf=float(weights_dict["w_rf"]),
                    w_xgb=float(weights_dict["w_xgb"]),
                    w_ann=float(weights_dict["w_ann"]),
                )

            # 6. Feature names
            with open(inv_dir / "features.json", "r") as f:
                feature_names = json.load(f)

            self.inventory_artifacts = {
                "rf_model": rf_wrapper,
                "xgb_model": xgb_wrapper,
                "ann_model": ann_wrapper,
                "preprocessor": preprocessor,
                "ensemble_weights": ensemble_weights,
                "feature_names": feature_names,
            }
            logger.info("Inventory ML artifacts loaded successfully.")
        except Exception as e:
            logger.error(f"Failed loading Inventory ML artifacts: {e}")
