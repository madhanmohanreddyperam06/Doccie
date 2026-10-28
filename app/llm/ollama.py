"""Ollama LLM Provider implementation communicating with Ollama API."""

import logging
import os
from typing import Optional
import httpx

from app.llm.base import LLMError, LLMProvider, LLMUnavailableError

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Local LLM provider communicating with Ollama via HTTP REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = timeout
        self.endpoint = f"{self.base_url}/api/generate"
        logger.info(
            "Initialized OllamaProvider (Endpoint: %s, Model: %s)",
            self.endpoint,
            self.model,
        )

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama /api/generate endpoint with given prompt and optional system message."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()

        except (httpx.ConnectError, httpx.ConnectTimeout) as conn_err:
            logger.error("Cannot connect to Ollama at %s: %s", self.base_url, conn_err)
            raise LLMUnavailableError(
                f"LLM service unavailable. Make sure Ollama is running at {self.base_url}."
            ) from conn_err

        except httpx.TimeoutException as timeout_err:
            logger.error("Ollama request timed out after %s seconds: %s", self.timeout, timeout_err)
            raise LLMUnavailableError(
                f"LLM request timed out after {self.timeout}s. Ollama may be under heavy load."
            ) from timeout_err

        except httpx.HTTPStatusError as http_err:
            logger.error("Ollama HTTP status error %s: %s", http_err.response.status_code, http_err)
            if http_err.response.status_code == 404:
                raise LLMUnavailableError(
                    f"Model '{self.model}' not found in Ollama. Pull it via: ollama pull {self.model}"
                ) from http_err
            raise LLMError(f"Ollama returned HTTP error: {http_err}") from http_err

        except Exception as general_err:
            logger.error("Unexpected error calling Ollama: %s", general_err)
            raise LLMError(f"Unexpected LLM error: {general_err}") from general_err
