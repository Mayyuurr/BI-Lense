"""Base Machine Learning Interfaces and Data Structures.

Defines the contract for base models (Random Forest, XGBoost, and ANN).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class ModelType(str, Enum):
    """Supported base ML algorithms."""

    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    ANN = "ann"


@dataclass
class ModelPrediction:
    """Standardized output structure for a single model's prediction."""

    model_type: ModelType
    prediction: float
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseMLModel(ABC):
    """Abstract interface for all base model wrappers."""

    def __init__(self, model_type: ModelType, model_path: Optional[str] = None) -> None:
        self.model_type = model_type
        self.model_path = model_path
        self._is_loaded: bool = False

    @abstractmethod
    def load(self, path: str) -> None:
        """Loads serialized model artifact from disk."""
        pass

    @abstractmethod
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Generates predictions for the given feature matrix."""
        pass

    @property
    def is_loaded(self) -> bool:
        """Returns whether the model artifact is loaded into memory."""
        return self._is_loaded


class SklearnModelWrapper(BaseMLModel):
    """Wrapper for Scikit-Learn joblib serialized estimators."""

    def __init__(self, model_type: ModelType = ModelType.RANDOM_FOREST, is_classifier: bool = False) -> None:
        super().__init__(model_type)
        self.is_classifier = is_classifier
        self.model = None

    def load(self, path: str) -> None:
        import joblib
        self.model = joblib.load(path)
        self.model_path = path
        self._is_loaded = True

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Model artifact not loaded. Call load() first.")
        if self.is_classifier and hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(features)[:, 1]
        return self.model.predict(features)


class XGBoostModelWrapper(BaseMLModel):
    """Wrapper for XGBoost models (JSON format or joblib)."""

    def __init__(self, model_type: ModelType = ModelType.XGBOOST, is_classifier: bool = False) -> None:
        super().__init__(model_type)
        self.is_classifier = is_classifier
        self.model = None

    def load(self, path: str) -> None:
        import xgboost as xgb
        if self.is_classifier:
            self.model = xgb.XGBClassifier()
        else:
            self.model = xgb.XGBRegressor()
        self.model.load_model(path)
        self.model_path = path
        self._is_loaded = True

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Model artifact not loaded. Call load() first.")
        if self.is_classifier and hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(features)[:, 1]
        return self.model.predict(features)


class PyTorchModelWrapper(BaseMLModel):
    """Wrapper for PyTorch Neural Networks (state_dict)."""

    def __init__(self, model_instance: Any, is_classifier: bool = False) -> None:
        super().__init__(ModelType.ANN)
        self.model = model_instance
        self.is_classifier = is_classifier

    def load(self, path: str) -> None:
        import torch
        state_dict = torch.load(path, map_location="cpu")
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.model_path = path
        self._is_loaded = True

    def predict(self, features: np.ndarray) -> np.ndarray:
        import torch
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Model artifact not loaded. Call load() first.")
        self.model.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(features, dtype=torch.float32)
            preds = self.model(x_tensor).cpu().numpy()
        return preds

