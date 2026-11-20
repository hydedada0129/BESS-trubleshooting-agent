"""Scripted LLM client for tests. No network."""

from __future__ import annotations

from dataclasses import dataclass

from llm.base import LLMClient, LLMResponse, Message, ToolCall, ToolSpec, Usage


@dataclass
class RecordedCall:
    messages: list[Message]
    tools: list[ToolSpec] | None
    max_tokens: int
    temperature: float


class FakeLLMClient(LLMClient):
    """Returns (or raises) scripted items in order and records every request.

    Example:
        fake = FakeLLMClient([tool_call_response("search_cases", {"query": "x"}), text_response("done")])
    """

    def __init__(self, script: list[LLMResponse | Exception], **retry_kwargs):
        retry_kwargs.setdefault("max_retries", 0)
        retry_kwargs.setdefault("sleep", lambda _s: None)
        super().__init__(**retry_kwargs)
        self._script = list(script)
        self.calls: list[RecordedCall] = []

    def _chat_once(self, messages, tools, *, max_tokens, temperature) -> LLMResponse:
        self.calls.append(RecordedCall(list(messages), tools, max_tokens, temperature))
        if not self._script:
            raise AssertionError("FakeLLMClient script exhausted")
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def text_response(content: str, model: str = "fake") -> LLMResponse:
    return LLMResponse(content=content, tool_calls=[], stop_reason="stop", usage=Usage(), model=model)


def tool_call_response(name: str, arguments: dict, call_id: str = "call_0", model: str = "fake") -> LLMResponse:
    call = ToolCall(id=call_id, name=name, arguments=arguments)
    return LLMResponse(content="", tool_calls=[call], stop_reason="tool_calls", usage=Usage(), model=model)
