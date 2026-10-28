"""Abstract Base Interface and utilities for LLM Providers."""

import abc
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for all LLM errors."""
    pass


class LLMUnavailableError(LLMError):
    """Raised when the LLM service (e.g. Ollama) cannot be reached."""
    pass


class LLMParseError(LLMError):
    """Raised when LLM output cannot be parsed into the expected format."""
    pass


def clean_llm_json(raw_text: str) -> str:
    """Normalize and clean LLM text output into parseable JSON string.

    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Preamble and postamble conversational text
    - Trailing commas in arrays and objects
    """
    if not raw_text or not raw_text.strip():
        raise LLMParseError("Received empty output from LLM.")

    text = raw_text.strip()

    # 1. Extract content inside markdown code fences if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    fence_matches = re.findall(fence_pattern, text, re.IGNORECASE)
    if fence_matches:
        # Use the largest block if multiple
        text = max(fence_matches, key=len).strip()
    else:
        # 2. Find outermost JSON object {...} or array [...]
        first_brace = text.find("{")
        first_bracket = text.find("[")

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = text.rfind("}")
            if last_brace != -1 and last_brace > first_brace:
                text = text[first_brace : last_brace + 1].strip()
        elif first_bracket != -1:
            last_bracket = text.rfind("]")
            if last_bracket != -1 and last_bracket > first_bracket:
                text = text[first_bracket : last_bracket + 1].strip()

    # 3. Clean up trailing commas before closing braces/brackets
    text = re.sub(r",\s*([\]}])", r"\1", text)

    return text


def parse_llm_json(raw_text: str) -> Union[Dict[str, Any], List[Any]]:
    """Clean and parse JSON from raw LLM output, with fallback normalization."""
    cleaned = clean_llm_json(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as primary_err:
        logger.warning(
            "Primary JSON parse failed: %s. Attempting fallback normalization.",
            primary_err,
        )
        # Attempt fallback: replace curly quotes or single-quoted keys
        try:
            fallback = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
            # Replace single-quoted dictionary keys with double-quoted
            fallback = re.sub(r"([{,]\s*)'([^']+)'\s*:", r'\1"\2":', fallback)
            return json.loads(fallback)
        except Exception as fallback_err:
            logger.error("Failed to parse JSON from LLM: %s. Cleaned text: %s", fallback_err, cleaned)
            raise LLMParseError(f"Could not parse valid JSON from LLM output: {primary_err}") from primary_err


class LLMProvider(abc.ABC):
    """Abstract Base Class for LLM inference providers."""

    @abc.abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate completion text for a given prompt."""
        raise NotImplementedError

    def generate_json(
        self,
        prompt: str,
        schema_description: str = "",
        system: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Generate and parse structured JSON with defensive retry.

        If the first attempt fails to parse as valid JSON, retries once with an explicit
        error-correction prompt before raising LLMParseError.
        """
        system_prompt = (
            (system + "\n\n" if system else "")
            + "CRITICAL: You must return ONLY valid, raw JSON. "
            "Do not include any Markdown code fences (no ```json). "
            "Do not include conversational preamble or explanation."
        )

        full_prompt = prompt
        if schema_description:
            full_prompt += f"\n\nRequired JSON Schema / Structure:\n{schema_description}"

        logger.debug("Generating JSON from LLM...")
        raw_output = self.generate(full_prompt, system=system_prompt)

        try:
            return parse_llm_json(raw_output)
        except LLMParseError as err:
            logger.warning(
                "First JSON parse attempt failed: %s. Performing 1 error-correction retry...",
                err,
            )
            correction_prompt = (
                f"{full_prompt}\n\n"
                f"ERROR: Your previous output could not be parsed as valid JSON.\n"
                f"Previous output snippet:\n{raw_output[:300]}\n\n"
                f"Please fix the error and output ONLY the valid JSON object now:"
            )
            second_attempt = self.generate(correction_prompt, system=system_prompt)
            return parse_llm_json(second_attempt)
