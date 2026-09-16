"""FastAPI Application Entry Point.

Configures application middleware, routers, exception handlers, and lifecycle hooks
for the BI-Lense SME Decision Intelligence Platform.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.datasets import router as datasets_router
from app.api.predictions import router as predictions_router
from app.api.scores import router as scores_router
from app.api.explanations import router as explanations_router
from app.api.insights import router as insights_router
from app.core.config import settings
from app.core.database import check_db_connection
from app.core.logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown logging."""
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode.")
    logger.info(f"Local LLaMA runtime enabled: {settings.LLAMA_ENABLED}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")


# Initialize FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Modular AI-Driven Decision Intelligence & Decision Support Platform for SMEs",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Centralized Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled exceptions and logs them with standard error format."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
            "path": request.url.path,
        },
    )


# Core Health Check Endpoint
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Verifies API availability and reports database connectivity without crashing
    if the database is currently unreachable.
    """
    db_healthy = check_db_connection()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": "connected" if db_healthy else "unavailable",
    }


# Include Domain Routers under API_V1_STR prefix
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(predictions_router, prefix=settings.API_V1_STR)
app.include_router(scores_router, prefix=settings.API_V1_STR)
app.include_router(explanations_router, prefix=settings.API_V1_STR)
app.include_router(insights_router, prefix=settings.API_V1_STR)
