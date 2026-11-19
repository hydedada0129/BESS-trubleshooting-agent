from spikes.spike0_tool_calling.prompts import CASES
from spikes.spike0_tool_calling.scorer import score_attempt, summarize, validate_args
from spikes.spike0_tool_calling.tools import SCHEMAS

CASES_BY_ID = {c["id"]: c for c in CASES}


def call(name, arguments):
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def test_prompt_set_composition():
    groups = [c["group"] for c in CASES]
    assert len(CASES) == 24
    assert groups.count("call") == 16
    assert groups.count("no_call") == 4
    assert groups.count("hard") == 4
    assert len({c["id"] for c in CASES}) == 24


def test_expected_args_are_schema_valid():
    for case in CASES:
        if case["expected_tool"] is None:
            continue
        assert case["expected_tool"] in SCHEMAS
        # expected args alone may omit required fields; check them as a partial object
        schema = dict(SCHEMAS[case["expected_tool"]], required=[])
        assert validate_args(case["expected_args"], schema) == [], case["id"]


def test_correct_call_is_valid():
    r = score_attempt(CASES_BY_ID["C11"], call("get_case", {"case_id": "CASE-014"}), SCHEMAS)
    assert r["valid"] and r["tool_correct"] and r["args_valid"]


def test_string_arguments_are_parsed():
    r = score_attempt(CASES_BY_ID["C11"], call("get_case", '{"case_id": "CASE-014"}'), SCHEMAS)
    assert r["valid"]


def test_invalid_json_arguments():
    r = score_attempt(CASES_BY_ID["C11"], call("get_case", '{"case_id": '), SCHEMAS)
    assert not r["valid"] and r["args_valid"] is False


def test_wrong_tool():
    r = score_attempt(CASES_BY_ID["C11"], call("search_cases", {"query": "CASE-014"}), SCHEMAS)
    assert not r["valid"] and r["tool_correct"] is False


def test_missing_required_argument():
    r = score_attempt(CASES_BY_ID["C07"], call("search_cases", {"k": 5}), SCHEMAS)
    assert not r["valid"]
    assert any("missing required" in e for e in r["errors"])


def test_invalid_enum_value():
    r = score_attempt(CASES_BY_ID["H01"], call("search_cases", {"query": "fan", "component": "fan", "operating_mode": "charging"}), SCHEMAS)
    assert not r["valid"]


def test_wrong_expected_enum_value():
    r = score_attempt(CASES_BY_ID["H01"], call("search_cases", {"query": "fan", "component": "cooling", "operating_mode": "standby"}), SCHEMAS)
    assert not r["valid"]


def test_unknown_argument():
    r = score_attempt(CASES_BY_ID["C11"], call("get_case", {"case_id": "CASE-014", "verbose": "yes"}), SCHEMAS)
    assert not r["valid"]


def test_pattern_mismatch():
    r = score_attempt(CASES_BY_ID["C13"], call("get_case", {"case_id": "case 27"}), SCHEMAS)
    assert not r["valid"]


def test_integer_bounds_and_bool_rejected():
    schema = SCHEMAS["search_cases"]
    assert validate_args({"query": "x", "k": 11}, schema)
    assert validate_args({"query": "x", "k": True}, schema)
    assert validate_args({"query": "x", "k": 3}, schema) == []


def test_no_call_case():
    no_call = CASES_BY_ID["N01"]
    assert score_attempt(no_call, {"role": "assistant", "content": "Power conversion system."}, SCHEMAS)["valid"]
    r = score_attempt(no_call, call("search_cases", {"query": "PCS"}), SCHEMAS)
    assert not r["valid"] and r["false_call"]


def test_missed_call_and_failed_request():
    case = CASES_BY_ID["C07"]
    assert score_attempt(case, {"role": "assistant", "content": "Sure."}, SCHEMAS)["errors"] == ["no tool call"]
    assert score_attempt(case, None, SCHEMAS)["errors"] == ["request failed"]


def test_summarize_rates():
    def scored(case_id, message):
        case = CASES_BY_ID[case_id]
        return {"group": case["group"], **score_attempt(case, message, SCHEMAS)}

    items = [
        scored("C11", call("get_case", {"case_id": "CASE-014"})),       # valid
        scored("C12", call("search_cases", {"query": "x"})),            # wrong tool
        scored("C13", {"role": "assistant", "content": "no"}),          # miss
        scored("H01", call("search_cases", {"query": "fan", "component": "cooling", "operating_mode": "charging"})),  # valid
        scored("N01", {"role": "assistant", "content": "answer"}),      # valid
        scored("N02", call("get_case", {"case_id": "CASE-001"})),       # false call
    ]
    s = summarize(items)
    assert s["attempts"] == 6
    assert s["valid_rate"] == 0.5
    assert s["tool_selection_accuracy"] == 0.5
    assert s["arg_validity"] == 1.0
    assert s["false_call_rate"] == 0.5
    assert s["miss_rate"] == 0.25
    assert s["hard_valid_rate"] == 1.0
