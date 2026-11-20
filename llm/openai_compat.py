"""Client for any OpenAI-compatible chat completions API (default: Kimi)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from llm._http import post_json
from llm.base import (
    LLMClient,
    LLMResponse,
    LLMResponseError,
    LLMUnavailableError,
    Message,
    ToolCall,
    ToolSpec,
    Usage,
    parse_tool_arguments,
)

_STOP_REASONS = {"stop": "stop", "length": "length", "tool_calls": "tool_calls"}


class OpenAICompatClient(LLMClient):
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout_s: float = 30.0,
        http_client: httpx.Client | None = None,
        **retry_kwargs: Any,
    ):
        super().__init__(**retry_kwargs)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._api_key = api_key
        self._http = http_client or httpx.Client(timeout=timeout_s)

    def _chat_once(self, messages, tools, *, max_tokens, temperature) -> LLMResponse:
        if not self.model:
            raise LLMUnavailableError("cloud model is not configured (config/settings.toml)", retryable=False)
        if not self._api_key:
            raise LLMUnavailableError("API key is not set", retryable=False)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_wire(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = [_tool_to_wire(t) for t in tools]

        body = post_json(
            self._http,
            f"{self.base_url}/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        return _from_wire(body)


def _tool_to_wire(tool: ToolSpec) -> dict:
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters},
    }


def _to_wire(msg: Message) -> dict:
    if msg.role == "tool":
        return {"role": "tool", "tool_call_id": msg.tool_call_id, "content": msg.content}
    out: dict[str, Any] = {"role": msg.role, "content": msg.content}
    if msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": c.id,
                "type": "function",
                "function": {
                    "name": c.name,
                    "arguments": c.raw_arguments or json.dumps(c.arguments or {}, ensure_ascii=False),
                },
            }
            for c in msg.tool_calls
        ]
    return out


def _from_wire(body: dict) -> LLMResponse:
    try:
        choice = body["choices"][0]
        message = choice["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("response has no choices[0].message") from exc

    tool_calls = []
    for i, raw in enumerate(message.get("tool_calls") or []):
        fn = raw.get("function") or {}
        args, raw_args, error = parse_tool_arguments(fn.get("arguments", ""))
        tool_calls.append(ToolCall(
            id=raw.get("id") or f"call_{i}",
            name=fn.get("name", ""),
            arguments=args,
            raw_arguments=raw_args,
            parse_error=error,
        ))

    usage = body.get("usage") or {}
    stop = "tool_calls" if tool_calls else _STOP_REASONS.get(choice.get("finish_reason"), "other")
    return LLMResponse(
        content=message.get("content") or "",
        tool_calls=tool_calls,
        stop_reason=stop,
        usage=Usage(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
        model=body.get("model", ""),
    )
