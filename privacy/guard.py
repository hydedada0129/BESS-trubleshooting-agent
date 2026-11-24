"""Pre-send privacy guard for cloud models (D-16, D-19, D-36).

`GuardedClient` wraps a cloud LLMClient. Before every request it scans all
message content and tool-call arguments; any hit raises PrivacyBlockedError and
nothing is sent. False positives are accepted: a block only means degraded mode,
a miss would be a leak. Errors report hit kinds and counts, never the values.
"""

from __future__ import annotations

from collections import Counter

from llm.base import LLMClient, LLMError, LLMResponse, Message, ToolSpec
from privacy.patterns import Detector


class PrivacyBlockedError(LLMError):
    """A cloud request was blocked because it contained confidential-looking data.

    Never retry and never reroute to another cloud provider: fall back to local (D-16).
    """

    retryable = False

    def __init__(self, kinds: dict[str, int]):
        self.kinds = dict(kinds)
        summary = ", ".join(f"{kind} x{count}" for kind, count in sorted(self.kinds.items()))
        super().__init__(f"request blocked by privacy guard: {summary}")


def _texts(messages: list[Message]):
    for m in messages:
        yield m.content
        for call in m.tool_calls:
            yield call.name
            yield call.raw_arguments or ""
            yield str(call.arguments or "")


def scan_messages(messages: list[Message], detector: Detector) -> dict[str, int]:
    """Return {kind: count} of detected confidential data in the messages."""
    counts: Counter[str] = Counter()
    for text in _texts(messages):
        counts.update(hit.kind for hit in detector.find(text))
    return dict(counts)


class GuardedClient(LLMClient):
    def __init__(self, inner: LLMClient, detector: Detector):
        # Retries belong to the inner client; the guard itself never retries.
        super().__init__(max_retries=0)
        self._inner = inner
        self._detector = detector

    def _chat_once(self, messages: list[Message], tools: list[ToolSpec] | None, *, max_tokens: int, temperature: float) -> LLMResponse:
        kinds = scan_messages(messages, self._detector)
        if kinds:
            raise PrivacyBlockedError(kinds)
        return self._inner.chat(messages, tools, max_tokens=max_tokens, temperature=temperature)
