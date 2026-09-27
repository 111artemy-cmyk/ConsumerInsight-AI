"""Factory that returns a concrete LLM client based on configuration.

The factory implements a simple preference order so the project can
"just run" on any laptop:

1.  If ``OPENAI_API_KEY`` is set and the ``openai`` package is
    installed, use the real :class:`OpenAIClient`.
2.  Otherwise, fall back to the deterministic :class:`MockLLMClient`.

The factory also accepts explicit overrides via ``CI_LLM_BACKEND``:

* ``CI_LLM_BACKEND=mock``   — force mock
* ``CI_LLM_BACKEND=openai`` — force OpenAI (will error if unavailable)
"""

from __future__ import annotations

from typing import Any

from .base import BaseLLMClient
from .mock_client import MockLLMClient
from .openai_client import OpenAIClient, is_openai_available


def build_llm_client(
    backend: str = "auto",
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    **kwargs: Any,
) -> BaseLLMClient:
    """Construct an LLM client.

    Parameters
    ----------
    backend:
        ``"auto"`` (default), ``"mock"``, or ``"openai"``.
    model:
        Model identifier forwarded to the provider.
    temperature:
        Sampling temperature.
    """
    backend = backend.lower()
    if backend not in {"auto", "mock", "openai"}:
        raise ValueError(f"Unknown LLM backend: {backend}")

    if backend == "openai" or (backend == "auto" and is_openai_available()):
        return OpenAIClient(model=model, temperature=temperature, **kwargs)
    return MockLLMClient(model=model or "mock-llm-v1", temperature=temperature, **kwargs)
