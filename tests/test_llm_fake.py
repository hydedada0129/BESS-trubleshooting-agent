import pytest

from llm.base import LLMClient, LLMTimeoutError, Message
from llm.fake import FakeLLMClient, text_response, tool_call_response


def test_fake_is_an_llm_client():
    assert isinstance(FakeLLMClient([]), LLMClient)


def test_returns_script_in_order_and_records_calls():
    fake = FakeLLMClient([tool_call_response("search_cases", {"query": "x"}), text_response("done")])
    first = fake.chat([Message(role="user", content="hi")], max_tokens=100)
    second = fake.chat([Message(role="user", content="again")])
    assert first.tool_calls[0].name == "search_cases"
    assert first.stop_reason == "tool_calls"
    assert second.content == "done"
    assert [c.messages[0].content for c in fake.calls] == ["hi", "again"]
    assert fake.calls[0].max_tokens == 100


def test_scripted_exception_is_raised():
    fake = FakeLLMClient([LLMTimeoutError("slow")])
    with pytest.raises(LLMTimeoutError):
        fake.chat([])


def test_retries_can_be_enabled():
    fake = FakeLLMClient([LLMTimeoutError("slow"), text_response("ok")], max_retries=1)
    assert fake.chat([]).content == "ok"
    assert len(fake.calls) == 2


def test_exhausted_script_fails_loudly():
    with pytest.raises(AssertionError):
        FakeLLMClient([]).chat([])
