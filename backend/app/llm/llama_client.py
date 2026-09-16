"""Local LLaMA Client Abstraction.

Provides connection handling to a locally hosted LLaMA runtime (e.g. Ollama,
vLLM, or llama.cpp server) without automatic model downloads.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.core.logging_config import logger


class BaseLLMClient(ABC):
    """Abstract base class for LLM interactions."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generates text from prompt."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Checks if the local runtime is reachable."""
        pass


class LocalLLaMAClient(BaseLLMClient):
    """HTTP client interface for interacting with local LLaMA instance."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.base_url = base_url or settings.LLAMA_BASE_URL
        self.model_name = model_name or settings.LLAMA_MODEL_NAME
        self.timeout = timeout or settings.LLAMA_TIMEOUT_SECONDS
        self.enabled = settings.LLAMA_ENABLED if enabled is None else enabled

    async def is_available(self) -> bool:
        """Pings the local LLM server endpoint to verify connectivity."""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as exc:
            logger.debug(f"Local LLaMA runtime check failed: {exc}")
            return False

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Sends a text completion request to the local LLaMA runtime.

        Falls back gracefully if the local runtime is disabled or unreachable.
        """
        if not self.enabled:
            return "[Local LLaMA runtime is disabled in configuration. Enable LLAMA_ENABLED to activate.]"

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except Exception as exc:
            logger.error(f"Error communicating with local LLaMA server: {exc}")
            return f"[LLaMA service unavailable: {str(exc)}]"
