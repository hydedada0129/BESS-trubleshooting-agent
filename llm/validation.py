"""Optional schema validation for tool calls (D-08, M1 Q5).

Logic adapted from the Spike 0 scorer; copied rather than imported because
production code must not import from spikes/ (D-30).
"""

from __future__ import annotations

import re

from llm.base import ToolCall, ToolSpec

_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}


def validate_arguments(args: dict, schema: dict) -> list[str]:
    """Return schema violations for an arguments object (empty list means valid)."""
    errors = []
    props = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in args:
            errors.append(f"missing required argument '{name}'")
    for name, value in args.items():
        spec = props.get(name)
        if spec is None:
            errors.append(f"unknown argument '{name}'")
            continue
        expected = _TYPES.get(spec.get("type", ""))
        if expected is not None:
            is_bool = isinstance(value, bool)
            if not isinstance(value, expected) or (is_bool and spec["type"] != "boolean"):
                errors.append(f"argument '{name}' should be {spec['type']}")
                continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"argument '{name}' value {value!r} not in enum")
        if "pattern" in spec and isinstance(value, str) and not re.fullmatch(spec["pattern"], value):
            errors.append(f"argument '{name}' does not match pattern")
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"argument '{name}' below minimum")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"argument '{name}' above maximum")
    return errors


def validate_tool_call(call: ToolCall, tools: list[ToolSpec]) -> list[str]:
    """Return problems with a tool call: unknown tool, unparsable or schema-invalid arguments."""
    spec = next((t for t in tools if t.name == call.name), None)
    if spec is None:
        return [f"unknown tool '{call.name}'"]
    if call.parse_error or call.arguments is None:
        return [f"arguments could not be parsed: {call.parse_error}"]
    return validate_arguments(call.arguments, spec.parameters)
