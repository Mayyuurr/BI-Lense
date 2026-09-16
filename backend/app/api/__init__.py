"""API Routers Package."""

from app.api.datasets import router as datasets_router
from app.api.predictions import router as predictions_router
from app.api.scores import router as scores_router
from app.api.explanations import router as explanations_router
from app.api.insights import router as insights_router

__all__ = [
    "datasets_router",
    "predictions_router",
    "scores_router",
    "explanations_router",
    "insights_router",
]
