"""The one module that talks to a language model.

Every caller goes through `chat()`. The provider is a base URL and a key, so
swapping Grok for Gemini (or anything OpenAI-compatible) is a config change,
not a code change. The key is read from .env and never logged.
"""

from __future__ import annotations

import time

import httpx

from zenai.config import settings


class LLMError(RuntimeError):
    pass


def available() -> bool:
    return bool(settings.XAI_API_KEY)


def chat(messages: list[dict], *, temperature: float = 0.7, max_tokens: int = 220,
         model: str | None = None, timeout: float = 45.0) -> dict:
    """Returns {"text", "model", "ms", "tokens_in", "tokens_out"}."""
    if not available():
        raise LLMError("No XAI_API_KEY in .env")
    t0 = time.perf_counter()
    try:
        r = httpx.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.XAI_API_KEY}"},
            json={"model": model or settings.LLM_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=timeout,
        )
    except httpx.HTTPError as e:
        raise LLMError(f"could not reach the model: {e.__class__.__name__}") from e
    if r.status_code != 200:
        raise LLMError(f"model answered {r.status_code}: {r.text[:200]}")
    d = r.json()
    u = d.get("usage") or {}
    return {
        "text": (d["choices"][0]["message"]["content"] or "").strip(),
        "model": d.get("model", model or settings.LLM_MODEL),
        "ms": round((time.perf_counter() - t0) * 1000),
        "tokens_in": u.get("prompt_tokens"),
        "tokens_out": u.get("completion_tokens"),
    }
