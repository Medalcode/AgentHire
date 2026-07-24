"""
agents/core/llm_client.py
=========================
Unified async LLM client supporting OpenAI and Google Gemini.

Provider is selected via the LLM_PROVIDER environment variable:
    LLM_PROVIDER=openai   → uses openai>=1.57.0
    LLM_PROVIDER=gemini   → uses google-generativeai>=0.8.0

Features:
  - async def complete()      — returns raw text
  - async def complete_json() — returns parsed dict (auto-repairs JSON)
  - Exponential backoff retry via tenacity
  - Token usage logging via loguru

Environment variables:
    LLM_PROVIDER     — "openai" | "gemini"  (default: openai)
    OPENAI_API_KEY   — required when LLM_PROVIDER=openai
    GEMINI_API_KEY   — required when LLM_PROVIDER=gemini
    LLM_MODEL        — model name override (default per provider)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging  # tenacity uses stdlib logging

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "dummy-key")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# Default models per provider
_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
    "qwen": "qwen2.5-coder:7b",
}
LLM_MODEL: str = os.environ.get("LLM_MODEL", "") or _DEFAULT_MODELS.get(LLM_PROVIDER, "gpt-4o-mini")

# Retry configuration
_MAX_ATTEMPTS = 4
_WAIT_MIN = 2      # seconds
_WAIT_MAX = 30     # seconds
_WAIT_MULTIPLIER = 2

# ---------------------------------------------------------------------------
# Lazy-initialised provider clients
# ---------------------------------------------------------------------------

_openai_client: Any = None
_gemini_model: Any = None


def _get_openai_client() -> Any:
    """Return (lazily create) the AsyncOpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        client_kwargs = {"api_key": OPENAI_API_KEY}
        
        # Auto-configure URL for Qwen (assuming Ollama on localhost)
        if LLM_PROVIDER == "qwen" and not OPENAI_BASE_URL:
            # host.docker.internal works for Docker to reach host
            client_kwargs["base_url"] = "http://host.docker.internal:11434/v1"
        elif OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
            
        _openai_client = AsyncOpenAI(**client_kwargs)
        logger.info("OpenAI client initialised (model={}, provider={})", LLM_MODEL, LLM_PROVIDER)
    return _openai_client


def _get_gemini_model(model: str) -> Any:
    """Return (lazily create) a google-generativeai GenerativeModel."""
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(model)
        logger.info("Gemini model initialised (model={})", model)
    return _gemini_model


# ---------------------------------------------------------------------------
# Retry decorator factory (applied to each provider call)
# ---------------------------------------------------------------------------

def _retry_on_api_error():
    """Return a tenacity retry decorator appropriate for LLM API errors."""
    # Import lazily so we don't crash if only one provider is installed
    try:
        from openai import APIError as OpenAIError
        retryable = (OpenAIError, Exception)
    except ImportError:
        retryable = (Exception,)

    return retry(
        retry=retry_if_exception_type(retryable),
        stop=stop_after_attempt(_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=_WAIT_MULTIPLIER,
            min=_WAIT_MIN,
            max=_WAIT_MAX,
        ),
        before_sleep=before_sleep_log(logging.getLogger("llm_client"), logging.WARNING),
        reraise=True,
    )


# ---------------------------------------------------------------------------
# Internal: OpenAI completion
# ---------------------------------------------------------------------------

async def _complete_openai(prompt: str, system: str, model: str) -> tuple[str, dict]:
    """
    Call the OpenAI Chat Completions API.

    Returns:
        (text_content, usage_dict)
    """
    client = _get_openai_client()

    @_retry_on_api_error()
    async def _call() -> Any:
        return await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

    response = await _call()
    text = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return text, usage


# ---------------------------------------------------------------------------
# Internal: Gemini completion
# ---------------------------------------------------------------------------

async def _complete_gemini(prompt: str, system: str, model: str) -> tuple[str, dict]:
    """
    Call the Google Gemini GenerativeModel API.

    Returns:
        (text_content, usage_dict)
    """
    import asyncio
    import google.generativeai as genai

    gem_model = _get_gemini_model(model)
    full_prompt = f"{system}\n\n{prompt}"

    @_retry_on_api_error()
    async def _call() -> Any:
        # google-generativeai is sync; run in executor to avoid blocking the loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: gem_model.generate_content(full_prompt),
        )

    response = await _call()
    text = response.text or ""
    # Gemini usage metadata may not always be populated
    usage_meta = getattr(response, "usage_metadata", None)
    usage = {
        "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0),
        "completion_tokens": getattr(usage_meta, "candidates_token_count", 0),
        "total_tokens": getattr(usage_meta, "total_token_count", 0),
    }
    return text, usage


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def complete(
    prompt: str,
    system: str,
    model: Optional[str] = None,
) -> str:
    """
    Send a prompt to the configured LLM and return the raw text response.

    Args:
        prompt:  User-facing content to complete.
        system:  System/instruction prompt that sets the assistant's behaviour.
        model:   Optional model override (defaults to LLM_MODEL env var).

    Returns:
        Raw text string from the LLM.

    Raises:
        RuntimeError if LLM_PROVIDER is not recognised.

    Example:
        summary = await complete(
            prompt="Summarise this job description: ...",
            system="You are a helpful HR assistant.",
        )
    """
    effective_model = model or LLM_MODEL

    if LLM_PROVIDER in ("openai", "qwen"):
        text, usage = await _complete_openai(prompt, system, effective_model)
    elif LLM_PROVIDER == "gemini":
        text, usage = await _complete_gemini(prompt, system, effective_model)
    else:
        raise RuntimeError(
            f"Unsupported LLM_PROVIDER='{LLM_PROVIDER}'. Use 'openai', 'gemini' or 'qwen'."
        )

    logger.info(
        "LLM call complete | provider={} model={} prompt_tokens={} completion_tokens={} total={}",
        LLM_PROVIDER,
        effective_model,
        usage.get("prompt_tokens", "?"),
        usage.get("completion_tokens", "?"),
        usage.get("total_tokens", "?"),
    )
    return text


async def complete_json(
    prompt: str,
    system: str,
    model: Optional[str] = None,
) -> dict[str, Any] | list:
    """
    Send a prompt to the LLM and parse the response as JSON.

    The system prompt should instruct the model to return only valid JSON.
    This function strips markdown code fences and repairs minor formatting
    issues before parsing.

    Args:
        prompt: User prompt (should request JSON output).
        system: System prompt (should include "respond only with valid JSON").
        model:  Optional model override.

    Returns:
        Parsed Python dict.

    Raises:
        ValueError  if the LLM response cannot be parsed as JSON after cleanup.

    Example:
        result = await complete_json(
            prompt=f"Rank this job: {job_description}",
            system="You are a job-ranking AI. Respond with JSON only.",
        )
        score = result["score"]
    """
    raw = await complete(prompt, system, model)
    return _parse_json_from_llm(raw)


def _parse_json_from_llm(raw: str) -> dict[str, Any] | list:
    """
    Attempt to extract and parse JSON from an LLM text response.

    Strategy:
      1. Strip leading/trailing whitespace.
      2. Remove ```json ... ``` or ``` ... ``` markdown fences.
      3. Attempt json.loads directly.
      4. Extract first {...} block with regex as a fallback.
      5. Raise ValueError if all attempts fail.
    """
    text = raw.strip()

    # Remove markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # First attempt: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: extract first JSON array
    match_arr = re.search(r"\[[\s\S]*\]", text)
    if match_arr:
        try:
            return json.loads(match_arr.group())
        except json.JSONDecodeError:
            pass

    logger.error("Failed to parse JSON from LLM response: {}", raw[:300])
    raise ValueError(f"LLM response is not valid JSON. Raw (first 300 chars): {raw[:300]}")
