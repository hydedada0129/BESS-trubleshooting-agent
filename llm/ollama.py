"""Client for a local Ollama server (native /api/chat)."""

from __future__ import annotations

from typing import Any

import httpx

from llm._http import post_json
from llm.base import (
    LLMClient,
    LLMResponse,
    LLMResponseError,
    Message,
    ToolCall,
    ToolSpec,
    Usage,
    parse_tool_arguments,
)


class OllamaClient(LLMClient):
    def __init__(
        self,
        *,
        host: str = "http://localhost:11434",
        model: str,
        num_ctx: int = 8192,
        think: bool = False,
        timeout_s: float = 120.0,
        http_client: httpx.Client | None = None,
        **retry_kwargs: Any,
    ):
        super().__init__(**retry_kwargs)
        self.host = host.rstrip("/")
        self.model = model
        self.num_ctx = num_ctx
        self.think = think
        self._http = http_client or httpx.Client(timeout=timeout_s)

    def _chat_once(self, messages, tools, *, max_tokens, temperature) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_wire(m) for m in messages],
            "stream": False,
            "think": self.think,
            "options": {"temperature": temperature, "num_ctx": self.num_ctx, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
                for t in tools
            ]
        body = post_json(self._http, f"{self.host}/api/chat", payload)
        return _from_wire(body)


def _to_wire(msg: Message) -> dict:
    out: dict[str, Any] = {"role": msg.role, "content": msg.content}
    if msg.tool_calls:
        # Ollama expects arguments as an object, not a JSON string.
        out["tool_calls"] = [{"function": {"name": c.name, "arguments": c.arguments or {}}} for c in msg.tool_calls]
    return out


def _from_wire(body: dict) -> LLMResponse:
    message = body.get("message")
    if not isinstance(message, dict):
        raise LLMResponseError("response has no message")

    tool_calls = []
    for i, raw in enumerate(message.get("tool_calls") or []):
        fn = raw.get("function") or {}
        args, raw_args, error = parse_tool_arguments(fn.get("arguments", {}))
        # Ollama does not return call IDs; generate stable ones.
        tool_calls.append(ToolCall(
            id=raw.get("id") or f"call_{i}",
            name=fn.get("name", ""),
            arguments=args,
            raw_arguments=raw_args,
            parse_error=error,
        ))

    if tool_calls:
        stop = "tool_calls"
    else:
        stop = {"stop": "stop", "length": "length"}.get(body.get("done_reason"), "other")
    return LLMResponse(
        content=message.get("content") or "",
        tool_calls=tool_calls,
        stop_reason=stop,
        usage=Usage(body.get("prompt_eval_count", 0), body.get("eval_count", 0)),
        model=body.get("model", ""),
    )
