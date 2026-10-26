"""Local & Remote LLaMA Client Abstraction.

Provides robust connection handling to an Ollama / vLLM runtime hosted locally,
remotely over Tailscale VPN, or on an AWS instance.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.logging_config import logger


class BaseLLMClient(ABC):
    """Abstract base class for LLM interactions."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        """Generates text from prompt."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Checks if the LLM runtime is reachable."""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Performs ping and health check against the runtime endpoint."""
        pass


class LocalLLaMAClient(BaseLLMClient):
    """HTTP client interface for interacting with Ollama / OpenAI-compatible runtime.

    Works seamlessly whether the model is hosted locally, on a remote PC via Tailscale,
    or on an AWS cloud instance.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.base_url = (base_url or settings.LLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.LLAMA_MODEL_NAME
        self.timeout = timeout or settings.LLAMA_TIMEOUT_SECONDS
        self.enabled = settings.LLAMA_ENABLED if enabled is None else enabled

    async def is_available(self) -> bool:
        """Pings the LLM server endpoint to verify connectivity."""
        if not self.enabled:
            return False
        health = await self.check_health()
        return health.get("status") == "connected"

    async def check_health(self) -> Dict[str, Any]:
        """Performs ping and health check against the runtime endpoint.

        Measures network latency (useful for Tailscale / AWS diagnostics).
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "LLM narrative generation is disabled in settings (LLAMA_ENABLED=False).",
                "base_url": self.base_url,
                "model_name": self.model_name,
            }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    is_target_model_present = any(self.model_name in m for m in models)
                    return {
                        "status": "connected",
                        "base_url": self.base_url,
                        "model_name": self.model_name,
                        "model_present": is_target_model_present,
                        "latency_ms": elapsed_ms,
                        "available_models": models,
                    }
                else:
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "base_url": self.base_url,
                        "latency_ms": elapsed_ms,
                    }
        except httpx.ConnectError:
            return {
                "status": "offline",
                "message": f"Connection refused at {self.base_url}. Verify Tailscale/AWS endpoint and ensure OLLAMA_HOST=0.0.0.0 is set.",
                "base_url": self.base_url,
                "model_name": self.model_name,
            }
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "message": f"Connection to {self.base_url} timed out after 5.0 seconds.",
                "base_url": self.base_url,
                "model_name": self.model_name,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "base_url": self.base_url,
                "model_name": self.model_name,
            }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> Optional[str]:
        """Sends a text completion request to the LLaMA runtime.

        Returns None if disabled or if connection fails, allowing the
        synthesizer to fall back to deterministic executive rules.
        """
        if not self.enabled:
            logger.info("LLaMA narrative generation is disabled in settings.")
            return None

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "").strip()
                return text if text else None
        except httpx.ConnectError as exc:
            logger.warning(f"Remote LLaMA host unreachable at {self.base_url} (Tailscale/AWS may be down): {exc}")
            return None
        except httpx.TimeoutException as exc:
            logger.warning(f"LLaMA generation timed out after {self.timeout}s: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Error communicating with LLaMA runtime: {exc}")
            return None
