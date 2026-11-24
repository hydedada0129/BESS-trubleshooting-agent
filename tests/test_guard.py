"""End-to-end privacy tests: zero leaks of seeded identifiers to the cloud (D-26)."""

import json

import httpx
import pytest
import respx

from llm.base import LLMError, Message, ToolCall
from llm.fake import FakeLLMClient, text_response
from llm.openai_compat import OpenAICompatClient
from privacy.anonymizer import Anonymizer, events_to_text
from privacy.guard import GuardedClient, PrivacyBlockedError, scan_messages
from privacy.patterns import Detector
from tools.parse_log import parse_log_text

SECRETS = ["AB12-7781", "192.168.10.5", "00:1A:2B:3C:4D:5E", "tech@example.com", "Riverbend Plant", "北港示範站",
           "4F7K22009", "2026-03-02"]
DETECTOR = Detector(denylist=["Riverbend Plant", "北港示範站"])
SEEDED_LOG = (
    "timestamp,device_id,severity,alarm_category,message,value,unit\n"
    "2026-03-02T15:44:30,AB12-7781,info,bms_alarm,limit reduced at Riverbend Plant,40,%I_rated\n"
    "2026-03-02T15:44:31,AB12-7781,warning,comm_loss,gateway 192.168.10.5 timeout (MAC 00:1A:2B:3C:4D:5E),,\n"
    "2026-03-02T15:44:34,AB12-7781,critical,dc_overvoltage,trip; notify tech@example.com; SN: 4F7K22009,105.2,%Vdc_rated\n"
)
DESCRIPTION = "北港示範站 PCS AB12-7781 一直在充電末段跳機，請協助。"
URL = "https://api.example.test/v1/chat/completions"
OK_BODY = {"model": "m", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]}


def cloud():
    inner = OpenAICompatClient(base_url="https://api.example.test/v1", model="m", api_key="k", sleep=lambda s: None)
    return GuardedClient(inner, DETECTOR)


def anonymized_messages():
    anon = Anonymizer(DETECTOR)
    events_text = events_to_text(anon.events(parse_log_text(SEEDED_LOG).events))
    return [Message(role="user", content=anon.text(DESCRIPTION) + "\n\nEvents:\n" + events_text)]


@respx.mock
def test_anonymized_payload_is_sent_with_zero_leaks():
    route = respx.post(URL).mock(return_value=httpx.Response(200, json=OK_BODY))
    assert cloud().chat(anonymized_messages()).content == "ok"
    body = route.calls.last.request.content.decode("utf-8")
    body_text = json.loads(body)["messages"][0]["content"]
    leaks = [s for s in SECRETS if s in body or s in body_text]
    assert leaks == []
    assert "DEV_1" in body_text and "[SITE]" in body_text


@respx.mock
def test_raw_payload_is_blocked_and_nothing_is_sent():
    route = respx.post(URL).mock(return_value=httpx.Response(200, json=OK_BODY))
    raw = [Message(role="user", content=DESCRIPTION + "\n" + SEEDED_LOG)]
    with pytest.raises(PrivacyBlockedError) as exc:
        cloud().chat(raw)
    assert route.call_count == 0
    assert not exc.value.retryable
    assert {"SITE", "SERIAL", "IP", "MAC", "EMAIL", "DATE"} <= set(exc.value.kinds)
    # The error must not contain any of the values themselves.
    assert [s for s in SECRETS if s in str(exc.value)] == []


@respx.mock
def test_tool_call_arguments_are_scanned():
    route = respx.post(URL).mock(return_value=httpx.Response(200, json=OK_BODY))
    msgs = [Message(role="assistant", tool_calls=[ToolCall(id="c", name="search_cases", arguments={"query": "Riverbend Plant trip"})])]
    with pytest.raises(PrivacyBlockedError):
        cloud().chat(msgs)
    assert route.call_count == 0


def test_blocked_error_is_an_llm_error_and_not_retried():
    inner = FakeLLMClient([text_response("should not be reached")])
    guarded = GuardedClient(inner, DETECTOR)
    with pytest.raises(LLMError):
        guarded.chat([Message(role="user", content="SN: 4F7K22009")])
    assert inner.calls == []


def test_clean_messages_pass_through_to_inner_client():
    inner = FakeLLMClient([text_response("fine")])
    assert GuardedClient(inner, DETECTOR).chat([Message(role="user", content="DC overvoltage trip, see CASE-008")]).content == "fine"
    assert len(inner.calls) == 1


def test_scan_messages_counts_kinds():
    msgs = [Message(role="user", content="10.0.0.1 and 10.0.0.2 at Riverbend Plant")]
    assert scan_messages(msgs, DETECTOR) == {"IP": 2, "SITE": 1}
