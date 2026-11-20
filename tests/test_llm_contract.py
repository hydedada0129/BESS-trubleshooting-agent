"""Contract tests: both clients must behave identically behind LLMClient."""

import json

import httpx
import pytest
import respx

from llm.base import (
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    Message,
    ToolCall,
    ToolSpec,
)
from llm.ollama import OllamaClient
from llm.openai_compat import OpenAICompatClient

TOOL = ToolSpec(
    name="get_case",
    description="Fetch a case by ID.",
    parameters={"type": "object", "properties": {"case_id": {"type": "string"}}, "required": ["case_id"]},
)
USER = [Message(role="user", content="Open case CASE-014.")]


class OpenAIProvider:
    url = "https://api.example.test/v1/chat/completions"

    def client(self, sleeps):
        return OpenAICompatClient(
            base_url="https://api.example.test/v1", model="test-model", api_key="test-key",
            max_retries=2, backoff_s=1.0, sleep=sleeps.append,
        )

    def text(self, content):
        return {"model": "test-model", "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7}}

    def tool(self, name, arguments):
        raw = arguments if isinstance(arguments, str) else json.dumps(arguments)
        return {"model": "test-model", "choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_abc", "type": "function", "function": {"name": name, "arguments": raw}}]}, "finish_reason": "tool_calls"}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7}}


class OllamaProvider:
    url = "http://ollama.test:11434/api/chat"

    def client(self, sleeps):
        return OllamaClient(host="http://ollama.test:11434", model="test-model", max_retries=2, backoff_s=1.0, sleep=sleeps.append)

    def text(self, content):
        return {"model": "test-model", "message": {"role": "assistant", "content": content}, "done": True,
                "done_reason": "stop", "prompt_eval_count": 11, "eval_count": 7}

    def tool(self, name, arguments):
        return {"model": "test-model", "message": {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": name, "arguments": arguments}}]}, "done": True, "done_reason": "stop",
            "prompt_eval_count": 11, "eval_count": 7}


@pytest.fixture(params=[OpenAIProvider(), OllamaProvider()], ids=["openai_compat", "ollama"])
def provider(request):
    return request.param


@pytest.fixture
def sleeps():
    return []


@respx.mock
def test_text_response(provider, sleeps):
    respx.post(provider.url).mock(return_value=httpx.Response(200, json=provider.text("Hello")))
    r = provider.client(sleeps).chat(USER)
    assert r.content == "Hello"
    assert r.tool_calls == []
    assert r.stop_reason == "stop"
    assert (r.usage.input_tokens, r.usage.output_tokens) == (11, 7)
    assert r.model == "test-model"
    assert r.latency_s >= 0


@respx.mock
def test_tool_call_response(provider, sleeps):
    respx.post(provider.url).mock(return_value=httpx.Response(200, json=provider.tool("get_case", {"case_id": "CASE-014"})))
    r = provider.client(sleeps).chat(USER, [TOOL])
    assert r.stop_reason == "tool_calls"
    assert len(r.tool_calls) == 1
    call = r.tool_calls[0]
    assert call.name == "get_case"
    assert call.arguments == {"case_id": "CASE-014"}
    assert call.parse_error is None
    assert call.id


@respx.mock
def test_tools_are_sent(provider, sleeps):
    route = respx.post(provider.url).mock(return_value=httpx.Response(200, json=provider.text("ok")))
    provider.client(sleeps).chat(USER, [TOOL])
    sent = json.loads(route.calls.last.request.content)
    assert sent["tools"][0]["function"]["name"] == "get_case"
    assert sent["tools"][0]["function"]["parameters"] == TOOL.parameters


@respx.mock
def test_invalid_tool_arguments_do_not_raise(provider, sleeps):
    respx.post(provider.url).mock(return_value=httpx.Response(200, json=provider.tool("get_case", '{"case_id": ')))
    call = provider.client(sleeps).chat(USER, [TOOL]).tool_calls[0]
    assert call.arguments is None
    assert call.parse_error
    assert call.raw_arguments == '{"case_id": '


@respx.mock
def test_retries_server_error_then_succeeds(provider, sleeps):
    route = respx.post(provider.url).mock(side_effect=[httpx.Response(503), httpx.Response(200, json=provider.text("ok"))])
    assert provider.client(sleeps).chat(USER).content == "ok"
    assert route.call_count == 2
    assert sleeps == [1.0]


@respx.mock
def test_server_error_exhausts_retries(provider, sleeps):
    route = respx.post(provider.url).mock(return_value=httpx.Response(500))
    with pytest.raises(LLMUnavailableError) as exc:
        provider.client(sleeps).chat(USER)
    assert exc.value.retryable
    assert route.call_count == 3
    assert sleeps == [1.0, 2.0]


@respx.mock
def test_rate_limit(provider, sleeps):
    route = respx.post(provider.url).mock(return_value=httpx.Response(429))
    with pytest.raises(LLMRateLimitError):
        provider.client(sleeps).chat(USER)
    assert route.call_count == 3


@respx.mock
def test_timeout(provider, sleeps):
    route = respx.post(provider.url).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(LLMTimeoutError):
        provider.client(sleeps).chat(USER)
    assert route.call_count == 3


@respx.mock
def test_connection_failure(provider, sleeps):
    respx.post(provider.url).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(LLMUnavailableError) as exc:
        provider.client(sleeps).chat(USER)
    assert exc.value.retryable


@respx.mock
def test_auth_error_is_not_retried(provider, sleeps):
    route = respx.post(provider.url).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    with pytest.raises(LLMUnavailableError) as exc:
        provider.client(sleeps).chat(USER)
    assert not exc.value.retryable
    assert route.call_count == 1
    assert sleeps == []


@respx.mock
def test_unparsable_response(provider, sleeps):
    respx.post(provider.url).mock(return_value=httpx.Response(200, text="not json"))
    with pytest.raises(LLMResponseError):
        provider.client(sleeps).chat(USER)


@respx.mock
def test_unexpected_response_shape(provider, sleeps):
    respx.post(provider.url).mock(return_value=httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(LLMResponseError):
        provider.client(sleeps).chat(USER)


@respx.mock
def test_tool_result_round_trip(provider, sleeps):
    """A full tool turn (assistant call + tool result) can be sent back."""
    route = respx.post(provider.url).mock(return_value=httpx.Response(200, json=provider.text("done")))
    history = USER + [
        Message(role="assistant", tool_calls=[ToolCall(id="call_1", name="get_case", arguments={"case_id": "CASE-014"})]),
        Message(role="tool", content='{"title": "example"}', tool_call_id="call_1"),
    ]
    assert provider.client(sleeps).chat(history, [TOOL]).content == "done"
    sent = json.loads(route.calls.last.request.content)["messages"]
    assert [m["role"] for m in sent] == ["user", "assistant", "tool"]
    assert sent[1]["tool_calls"][0]["function"]["name"] == "get_case"
    assert sent[2]["content"] == '{"title": "example"}'


# --- provider-specific wire details -------------------------------------------


@respx.mock
def test_openai_request_format():
    route = respx.post(OpenAIProvider.url).mock(return_value=httpx.Response(200, json=OpenAIProvider().text("ok")))
    OpenAIProvider().client([]).chat(USER, max_tokens=256, temperature=0.2)
    req = route.calls.last.request
    sent = json.loads(req.content)
    assert req.headers["Authorization"] == "Bearer test-key"
    assert (sent["model"], sent["max_tokens"], sent["temperature"]) == ("test-model", 256, 0.2)


@respx.mock
def test_openai_tool_message_and_string_arguments():
    route = respx.post(OpenAIProvider.url).mock(return_value=httpx.Response(200, json=OpenAIProvider().text("ok")))
    history = [Message(role="assistant", tool_calls=[ToolCall(id="c1", name="get_case", arguments={"case_id": "CASE-014"})]),
               Message(role="tool", content="r", tool_call_id="c1")]
    OpenAIProvider().client([]).chat(history)
    sent = json.loads(route.calls.last.request.content)["messages"]
    assert json.loads(sent[0]["tool_calls"][0]["function"]["arguments"]) == {"case_id": "CASE-014"}
    assert sent[1]["tool_call_id"] == "c1"


@respx.mock
@pytest.mark.parametrize("kwargs", [{"model": ""}, {"api_key": None}])
def test_openai_missing_config_fails_without_request(kwargs):
    route = respx.post(OpenAIProvider.url)
    params = {"base_url": "https://api.example.test/v1", "model": "test-model", "api_key": "test-key", **kwargs}
    with pytest.raises(LLMUnavailableError) as exc:
        OpenAICompatClient(**params, sleep=lambda s: None).chat(USER)
    assert not exc.value.retryable
    assert route.call_count == 0


@respx.mock
def test_ollama_request_format():
    route = respx.post(OllamaProvider.url).mock(return_value=httpx.Response(200, json=OllamaProvider().text("ok")))
    OllamaClient(host="http://ollama.test:11434", model="m", num_ctx=8192, think=False).chat(USER, max_tokens=256)
    sent = json.loads(route.calls.last.request.content)
    assert sent["stream"] is False
    assert sent["think"] is False
    assert sent["options"] == {"temperature": 0.0, "num_ctx": 8192, "num_predict": 256}


@respx.mock
def test_ollama_tool_call_arguments_sent_as_object():
    route = respx.post(OllamaProvider.url).mock(return_value=httpx.Response(200, json=OllamaProvider().text("ok")))
    history = [Message(role="assistant", tool_calls=[ToolCall(id="c1", name="get_case", arguments={"case_id": "CASE-014"})])]
    OllamaProvider().client([]).chat(history)
    sent = json.loads(route.calls.last.request.content)["messages"]
    assert sent[0]["tool_calls"][0]["function"]["arguments"] == {"case_id": "CASE-014"}
