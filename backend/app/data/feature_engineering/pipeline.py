"""Domain-Specific Feature Engineering Pipelines.

Modular feature extraction pipelines preparing data for hybrid ML models.
"""

from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class BaseFeaturePipeline(ABC):
    """Abstract base class for domain-specific feature engineering."""

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms cleaned DataFrame into a feature matrix for ML models."""
        pass

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Returns the list of generated feature column names."""
        pass


class SalesFeaturePipeline(BaseFeaturePipeline):
    """Generates demand lag features, moving averages, and seasonality indicators."""

    def __init__(self, lag_periods: List[int] = None) -> None:
        self.lag_periods = lag_periods or [1, 7, 30]
        self._feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Placeholder for structured feature generation
        transformed = df.copy()
        self._feature_names = list(transformed.columns)
        return transformed

    def get_feature_names(self) -> List[str]:
        return self._feature_names


class InventoryFeaturePipeline(BaseFeaturePipeline):
    """Generates lead-time features, consumption rates, and buffer depletion ratios."""

    def __init__(self) -> None:
        self._feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        transformed = df.copy()
        self._feature_names = list(transformed.columns)
        return transformed

    def get_feature_names(self) -> List[str]:
        return self._feature_names


class FinanceFeaturePipeline(BaseFeaturePipeline):
    """Generates cash-flow velocity, burn rate, and working capital ratios."""

    def __init__(self) -> None:
        self._feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        transformed = df.copy()
        self._feature_names = list(transformed.columns)
        return transformed

    def get_feature_names(self) -> List[str]:
        return self._feature_names


class HRFeaturePipeline(BaseFeaturePipeline):
    """Generates task completion velocity, backlog ratios, and workload indices."""

    def __init__(self) -> None:
        self._feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        transformed = df.copy()
        self._feature_names = list(transformed.columns)
        return transformed

    def get_feature_names(self) -> List[str]:
        return self._feature_names
