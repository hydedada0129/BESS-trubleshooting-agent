"""Shared HTTP call with error mapping to LLMError subclasses."""

from __future__ import annotations

import httpx

from llm.base import LLMRateLimitError, LLMResponseError, LLMTimeoutError, LLMUnavailableError


def post_json(client: httpx.Client, url: str, payload: dict, headers: dict | None = None) -> dict:
    try:
        resp = client.post(url, json=payload, headers=headers or {})
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError(f"request timed out: {exc}") from exc
    except httpx.TransportError as exc:
        raise LLMUnavailableError(f"connection failed: {exc}", retryable=True) from exc

    if resp.status_code == 429:
        raise LLMRateLimitError("rate limited (429)")
    if resp.status_code >= 500:
        raise LLMUnavailableError(f"server error ({resp.status_code})", retryable=True)
    if resp.status_code >= 400:
        # Auth/config/request errors: retrying will not help.
        raise LLMUnavailableError(f"request rejected ({resp.status_code}): {resp.text[:200]}", retryable=False)

    try:
        body = resp.json()
    except ValueError as exc:
        raise LLMResponseError("response is not valid JSON") from exc
    if not isinstance(body, dict):
        raise LLMResponseError("response is not a JSON object")
    return body
