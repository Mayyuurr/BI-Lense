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
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Generates predictions for the given feature matrix."""
        pass

    @property
    def is_loaded(self) -> bool:
        """Returns whether the model artifact is loaded into memory."""
        return self._is_loaded
