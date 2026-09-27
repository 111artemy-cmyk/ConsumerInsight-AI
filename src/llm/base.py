"""Abstract base class for LLM back-ends.

Every concrete client (mock, OpenAI, Anthropic, local HF model, …) must
inherit from :class:`BaseLLMClient` and implement :meth:`complete`.

The interface is intentionally narrow so that downstream modules do not
leak provider-specific details.
"""

from __future__ import annotations

import abc
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Container for a single LLM completion."""

    text: str
    parsed: Optional[Any] = None  # dict or list, depending on the prompt
    raw: Optional[Any] = None
    usage: Dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.text)

    def as_dict(self) -> Dict[str, Any]:
        """Return parsed JSON payload (dict) or ``{"text": ...}`` fallback.

        For list payloads, callers should check ``resp.parsed`` directly.
        """
        if isinstance(self.parsed, dict):
            return self.parsed
        return {"text": self.text}


class BaseLLMClient(abc.ABC):
    """Provider-agnostic LLM interface."""

    name: str = "base"

    def __init__(self, model: str = "default", temperature: float = 0.2, **kwargs: Any):
        self.model = model
        self.temperature = temperature
        self._kwargs = kwargs

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def complete_json(
        self,
        system: str,
        user: str,
        schema_hint: Optional[str] = None,
    ) -> LLMResponse:
        """Call :meth:`complete` and try to parse the reply as JSON.

        Falls back gracefully when the response is not strict JSON.
        """
        if schema_hint:
            user = f"{user}\n\n请严格用 JSON 格式输出，结构如下：\n{schema_hint}"
        resp = self.complete(system=system, user=user)
        parsed = _try_parse_json(resp.text)
        resp.parsed = parsed
        return resp

    def batch_complete_json(
        self,
        system: str,
        user_messages: List[str],
        schema_hint: Optional[str] = None,
    ) -> List[LLMResponse]:
        """Convenience wrapper for batched JSON completion."""
        return [self.complete_json(system, u, schema_hint) for u in user_messages]

    # ------------------------------------------------------------------
    # Provider-specific implementation
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def complete(self, system: str, user: str) -> LLMResponse:
        """Run a single chat completion and return an :class:`LLMResponse`."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _try_parse_json(text: str) -> Optional[Any]:
    """Best-effort JSON parser.  Tolerant of markdown fences and trailing commas.

    Returns either a ``dict`` or a ``list`` (or ``None`` if parsing fails).
    The caller is responsible for type-checking the result.
    """
    if not text:
        return None
    cleaned = text.strip()
    # Strip markdown fences
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    # Try the outermost JSON array first (LLMs often emit a list payload)
    start_arr = cleaned.find("[")
    end_arr = cleaned.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        for parser in (_strict, _lax):
            try:
                return parser(cleaned[start_arr : end_arr + 1])
            except Exception:
                continue
    # Fall back to the outermost JSON object
    start_obj = cleaned.find("{")
    end_obj = cleaned.rfind("}")
    if start_obj == -1 or end_obj == -1 or end_obj <= start_obj:
        return None
    for parser in (_strict, _lax):
        try:
            return parser(cleaned[start_obj : end_obj + 1])
        except Exception:
            continue
    return None


def _strict(s: str) -> Dict[str, Any]:
    return json.loads(s)


def _lax(s: str) -> Dict[str, Any]:
    # Drop trailing commas before } or ]
    import re

    fixed = re.sub(r",\s*([}\]])", r"\1", s)
    return json.loads(fixed)
