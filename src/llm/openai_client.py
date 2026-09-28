"""Optional OpenAI / OpenAI-compatible LLM client.

This module is only imported if the user has the ``openai`` package
installed *and* has exported an ``OPENAI_API_KEY``.  In any other case
the factory in :mod:`src.llm.factory` falls back to the offline mock.

The client also works with OpenAI-compatible endpoints (Azure OpenAI,
智谱 GLM, DeepSeek, Moonshot, etc.) — just point ``base_url`` to the
provider's endpoint.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .base import BaseLLMClient, LLMResponse


def is_openai_available() -> bool:
    """Return True if the openai package *and* an API key are present.

    仅设 OPENAI_BASE_URL 而没有 API key 时，OpenAIClient 会在请求时
    拿到 401。这里要求 key 存在才视为可用。
    """
    try:
        import openai  # noqa: F401
    except Exception:
        return False
    return bool(os.getenv("OPENAI_API_KEY"))


class OpenAIClient(BaseLLMClient):
    """Thin wrapper around the OpenAI Chat Completions API."""

    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(model=model, temperature=temperature, **kwargs)
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover - exercised only by users
            raise RuntimeError(
                "The `openai` package is required for OpenAIClient. "
                "Install with: pip install openai>=1.0.0"
            ) from e
        self._client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )

    def complete(self, system: str, user: str) -> LLMResponse:
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:  # pragma: no cover - exercised only by users
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        text = (resp.choices[0].message.content or "").strip()
        usage: Dict[str, int] = {}
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens": getattr(resp.usage, "total_tokens", 0),
            }
        return LLMResponse(text=text, raw=resp, usage=usage)
