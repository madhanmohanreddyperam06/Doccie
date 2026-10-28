"""LLM provider package exposing base abstractions and Ollama provider."""

import logging
import os
from typing import Optional

from app.llm.base import (
    LLMError,
    LLMParseError,
    LLMProvider,
    LLMUnavailableError,
    clean_llm_json,
    parse_llm_json,
)
from app.llm.mock import MockLLMProvider
from app.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_type: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMProvider:
    """Factory to retrieve configured LLM provider instance.

    Defaults to OllamaProvider using environment variables OLLAMA_BASE_URL and OLLAMA_MODEL.
    If USE_MOCK_LLM is set to 'true' or provider_type='mock', returns MockLLMProvider.
    """
    selected_type = provider_type or os.getenv("LLM_PROVIDER", "ollama").lower()
    use_mock = os.getenv("USE_MOCK_LLM", "false").lower() in ("true", "1", "yes")

    if selected_type == "mock" or use_mock:
        logger.info("Using MockLLMProvider")
        return MockLLMProvider()

    logger.info("Using OllamaProvider (URL: %s, Model: %s)", base_url, model)
    return OllamaProvider(base_url=base_url, model=model)


__all__ = [
    "LLMError",
    "LLMParseError",
    "LLMProvider",
    "LLMUnavailableError",
    "MockLLMProvider",
    "OllamaProvider",
    "clean_llm_json",
    "get_llm_provider",
    "parse_llm_json",
]
