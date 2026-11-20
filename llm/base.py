"""Provider-neutral LLM interface.

All LLM access in this project goes through `LLMClient`. Provider-specific
formats are converted inside each client; callers only see the types below.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

Role = Literal["system", "user", "assistant", "tool"]
StopReason = Literal["stop", "length", "tool_calls", "other"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict  # JSON schema of the arguments object


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict | None  # None when the model's arguments could not be parsed
    raw_arguments: str = ""
    parse_error: str | None = None


@dataclass
class Message:
    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)  # assistant messages only
    tool_call_id: str | None = None  # tool messages only


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    stop_reason: StopReason
    usage: Usage
    model: str
    latency_s: float = 0.0


# --- errors -----------------------------------------------------------------


class LLMError(Exception):
    """Base class for all LLM client errors."""

    retryable = False


class LLMTimeoutError(LLMError):
    retryable = True


class LLMRateLimitError(LLMError):
    """HTTP 429."""

    retryable = True


class LLMUnavailableError(LLMError):
    """5xx or connection failure (retryable), or a configuration/auth problem (not retryable)."""

    def __init__(self, message: str, *, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


class LLMResponseError(LLMError):
    """The provider answered, but the response could not be parsed."""


# --- helpers ------------------------------------------------------------------


def parse_tool_arguments(raw: Any) -> tuple[dict | None, str, str | None]:
    """Return (arguments, raw_string, parse_error). Never raises."""
    if isinstance(raw, dict):
        return raw, json.dumps(raw, ensure_ascii=False), None
    if not isinstance(raw, str):
        return None, repr(raw), f"arguments have unexpected type {type(raw).__name__}"
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        return None, raw, f"invalid JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, raw, "arguments are not a JSON object"
    return parsed, raw, None


# --- interface ----------------------------------------------------------------


class LLMClient(ABC):
    """Single entry point: `chat()`. Retries transient errors with exponential backoff (D-15).

    Retries live here; switching to another model (fallback) is the router's job.
    """

    def __init__(
        self,
        *,
        max_retries: int = 2,
        backoff_s: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self._sleep = sleep

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResponse:
        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                response = self._chat_once(messages, tools, max_tokens=max_tokens, temperature=temperature)
            except LLMError as exc:
                if not exc.retryable or attempt == self.max_retries:
                    raise
                self._sleep(self.backoff_s * 2**attempt)
                continue
            response.latency_s = time.perf_counter() - start
            return response
        raise AssertionError("unreachable")

    @abstractmethod
    def _chat_once(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None,
        *,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """One request to the provider, raising LLMError subclasses on failure."""
