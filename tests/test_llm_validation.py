from llm.base import ToolCall, ToolSpec
from llm.validation import validate_tool_call

SEARCH = ToolSpec(
    name="search_cases",
    description="Search cases.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "component": {"type": "string", "enum": ["cooling", "dc_side"]},
            "k": {"type": "integer", "minimum": 1, "maximum": 10},
            "case_id": {"type": "string", "pattern": "^CASE-[0-9]{3}$"},
        },
        "required": ["query"],
    },
)


def call(arguments, name="search_cases", parse_error=None):
    return ToolCall(id="c", name=name, arguments=arguments, parse_error=parse_error)


def test_valid_call():
    assert validate_tool_call(call({"query": "fan", "component": "cooling", "k": 3}), [SEARCH]) == []


def test_unknown_tool():
    assert validate_tool_call(call({"query": "x"}, name="nope"), [SEARCH]) == ["unknown tool 'nope'"]


def test_parse_error():
    errors = validate_tool_call(call(None, parse_error="invalid JSON"), [SEARCH])
    assert errors and "could not be parsed" in errors[0]


def test_schema_violations():
    cases = [
        {"k": 3},                                  # missing required
        {"query": "x", "extra": 1},                # unknown argument
        {"query": 5},                              # wrong type
        {"query": "x", "component": "fan"},        # enum
        {"query": "x", "k": 0},                    # minimum
        {"query": "x", "k": 11},                   # maximum
        {"query": "x", "k": True},                 # bool is not integer
        {"query": "x", "case_id": "case 1"},       # pattern
    ]
    for args in cases:
        assert validate_tool_call(call(args), [SEARCH]), args
