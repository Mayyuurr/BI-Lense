"""Application Configuration Module.

Loads and validates environment variables using Pydantic Settings.
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings model."""

    # Application Information
    APP_NAME: str = "BI-Lense SME Decision Intelligence"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Settings
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Database Settings
    DATABASE_URL: str = "postgresql://bilense_user:bilense_password@localhost:5432/bilense_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT_SECONDS: int = 5

    # Local LLaMA Configuration (Copilot & Explanation)
    LLAMA_ENABLED: bool = False
    LLAMA_BASE_URL: str = "http://localhost:11434"
    LLAMA_MODEL_NAME: str = "llama3:8b"
    LLAMA_TIMEOUT_SECONDS: float = 30.0

    # ML Storage & Paths
    MODEL_ARTIFACTS_DIR: str = "./models/artifacts"
    DATASET_STORAGE_DIR: str = "./data/storage"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
