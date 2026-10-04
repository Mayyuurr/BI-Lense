"""Machine Learning Module for BI-Lense Platform.

Exports:
- BaseMLModel, ModelType, SklearnModelWrapper, XGBoostModelWrapper, PyTorchModelWrapper
- ModelRegistry (in-memory artifact caching singleton)
- EnsembleOptimizer, EnsembleWeights, HybridEnsemblePredictor
- SalesDemandPredictor, SalesPredictionResult
- InventoryStockoutPredictor, StockoutPredictionResult
- FinanceDeficitPredictor, CashFlowDeficitResult
- HRPredictor, HRPredictionResult
"""

from app.ml.base import (
    BaseMLModel,
    ModelPrediction,
    ModelType,
    PyTorchModelWrapper,
    SklearnModelWrapper,
    XGBoostModelWrapper,
)
from app.ml.ensemble import (
    EnsembleOptimizer,
    EnsembleWeights,
    HybridEnsemblePredictor,
)
from app.ml.finance import (
    CashFlowDeficitResult,
    FinanceDeficitPredictor,
)
from app.ml.hr import (
    HRPredictionResult,
    HRPredictor,
)
from app.ml.inventory import (
    InventoryStockoutPredictor,
    StockoutPredictionResult,
)
from app.ml.registry import ModelRegistry
from app.ml.sales import (
    SalesDemandPredictor,
    SalesPredictionResult,
)

__all__ = [
    "BaseMLModel",
    "ModelType",
    "ModelPrediction",
    "SklearnModelWrapper",
    "XGBoostModelWrapper",
    "PyTorchModelWrapper",
    "EnsembleWeights",
    "EnsembleOptimizer",
    "HybridEnsemblePredictor",
    "ModelRegistry",
    "SalesDemandPredictor",
    "SalesPredictionResult",
    "InventoryStockoutPredictor",
    "StockoutPredictionResult",
    "FinanceDeficitPredictor",
    "CashFlowDeficitResult",
    "HRPredictor",
    "HRPredictionResult",
]
