"""Prediction Management Service.

Orchestrates domain ML inference pipelines (Sales, Inventory, Finance, HR)
and records predictions with real model artifacts.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.ml.inventory import InventoryStockoutPredictor
from app.ml.sales import SalesDemandPredictor
from app.models.database_models import PredictionRecord


class PredictionService:
    """Service boundary coordinating hybrid ML model execution across domains."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self._sales_predictor: Optional[SalesDemandPredictor] = None
        self._inventory_predictor: Optional[InventoryStockoutPredictor] = None

    @property
    def sales_predictor(self) -> SalesDemandPredictor:
        if self._sales_predictor is None:
            self._sales_predictor = SalesDemandPredictor.from_registry()
        return self._sales_predictor

    @property
    def inventory_predictor(self) -> InventoryStockoutPredictor:
        if self._inventory_predictor is None:
            self._inventory_predictor = InventoryStockoutPredictor.from_registry()
        return self._inventory_predictor

    def predict_sales_demand(
        self,
        input_data: Dict[str, Any],
        target_period: str = "next_30_days",
    ) -> Dict[str, Any]:
        """Runs hybrid ensemble sales demand forecasting on input feature dictionary."""
        df = pd.DataFrame([input_data])
        sku_id = input_data.get("sku_id")
        result = self.sales_predictor.predict_next_period_demand(
            features=df,
            target_period=target_period,
            sku_id=sku_id,
        )

        output = {
            "domain": "sales",
            "sku_id": result.sku_id,
            "predicted_demand": result.predicted_demand,
            "target_period": result.target_period,
            "base_predictions": result.base_predictions,
            "ensemble_weights": result.ensemble_weights,
            "status": "success",
        }

        # Persist audit record if db session is available
        if self.db is not None:
            try:
                record = PredictionRecord(
                    domain="sales",
                    sku_id=result.sku_id,
                    prediction_value=result.predicted_demand,
                    prediction_metadata=output,
                )
                self.db.add(record)
                self.db.commit()
            except Exception as e:
                logger.warning(f"Could not persist prediction audit record: {e}")

        return output

    def predict_inventory_stockout(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Runs hybrid ensemble inventory stockout risk estimation."""
        df = pd.DataFrame([input_data])
        sku_id = input_data.get("sku_id")
        result = self.inventory_predictor.predict_stockout_probability(
            features=df,
            sku_id=sku_id,
        )

        output = {
            "domain": "inventory",
            "sku_id": result.sku_id,
            "stockout_probability": result.stockout_probability,
            "risk_level": result.risk_level,
            "base_predictions": result.base_predictions,
            "ensemble_weights": result.ensemble_weights,
            "status": "success",
        }

        # Persist audit record if db session is available
        if self.db is not None:
            try:
                record = PredictionRecord(
                    domain="inventory",
                    sku_id=result.sku_id,
                    prediction_value=result.stockout_probability,
                    prediction_metadata=output,
                )
                self.db.add(record)
                self.db.commit()
            except Exception as e:
                logger.warning(f"Could not persist prediction audit record: {e}")

        return output

    def get_domain_prediction(
        self,
        domain: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Unified router for running domain hybrid ML predictions."""
        domain_clean = domain.lower().strip()
        if domain_clean == "sales":
            return self.predict_sales_demand(input_data)
        elif domain_clean == "inventory":
            return self.predict_inventory_stockout(input_data)
        elif domain_clean in ["finance", "hr"]:
            return {
                "domain": domain_clean,
                "status": "ready_for_model_artifacts",
                "message": f"ML pipeline for {domain_clean} is scheduled for subsequent phase.",
                "features_received": list(input_data.keys()),
            }
        else:
            raise ValueError(f"Unsupported domain '{domain}'. Supported: sales, inventory, finance, hr")
