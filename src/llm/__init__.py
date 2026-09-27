"""Pluggable LLM back-ends for ConsumerInsight-AI.

The project is intentionally designed to work with *any* LLM provider.
The two shipped implementations are:

* :class:`MockLLMClient`  — fully offline, rule-based; default for
  reproducible demos that don't require an API key.
* :class:`OpenAIClient`   — thin wrapper around OpenAI Chat Completions
  (compatible with most OpenAI-compatible endpoints such as Azure
  OpenAI, 智谱 GLM, DeepSeek, etc.).

Add a new provider by subclassing :class:`BaseLLMClient` and implementing
:meth:`complete`.
"""

from .base import BaseLLMClient, LLMResponse
from .mock_client import MockLLMClient
from .openai_client import OpenAIClient, is_openai_available
from .prompts import PromptLibrary
from .factory import build_llm_client

__all__ = [
    "BaseLLMClient",
    "LLMResponse",
    "MockLLMClient",
    "OpenAIClient",
    "is_openai_available",
    "PromptLibrary",
    "build_llm_client",
]
