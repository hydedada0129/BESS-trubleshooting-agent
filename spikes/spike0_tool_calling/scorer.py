"""Pure scoring functions for Spike 0. No network access."""

from __future__ import annotations

import json
import re
from typing import Any

_TYPES = {"string": str, "integer": int}


def validate_args(args: Any, schema: dict) -> list[str]:
    """Return a list of schema violations (empty list means valid)."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return ["arguments are not valid JSON"]
    if not isinstance(args, dict):
        return ["arguments are not a JSON object"]

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
        expected_type = _TYPES[spec["type"]]
        if not isinstance(value, expected_type) or isinstance(value, bool):
            errors.append(f"argument '{name}' should be {spec['type']}")
            continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"argument '{name}' value '{value}' not in enum")
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            errors.append(f"argument '{name}' does not match pattern")
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"argument '{name}' below minimum")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"argument '{name}' above maximum")
    return errors


def _parse_args(args: Any) -> Any:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return None
    return args


def score_attempt(case: dict, message: dict | None, schemas: dict) -> dict:
    """Score one model response for one test case.

    `message` is the `message` object from Ollama's /api/chat response,
    or None if the request failed.
    """
    result = {
        "called": False,
        "tool": None,
        "tool_correct": None,
        "args_valid": None,
        "false_call": False,
        "valid": False,
        "errors": [],
    }
    if message is None:
        result["errors"].append("request failed")
        return result

    calls = message.get("tool_calls") or []
    expected = case["expected_tool"]

    if not calls:
        if expected is None:
            result["valid"] = True
        else:
            result["errors"].append("no tool call")
        return result

    result["called"] = True
    fn = calls[0].get("function", {})
    name = fn.get("name")
    raw_args = fn.get("arguments", {})
    result["tool"] = name

    if expected is None:
        result["false_call"] = True
        result["errors"].append(f"unexpected call to '{name}'")
        return result

    result["tool_correct"] = name == expected
    if not result["tool_correct"]:
        result["errors"].append(f"wrong tool '{name}', expected '{expected}'")
        return result

    errors = validate_args(raw_args, schemas[name])
    args = _parse_args(raw_args)
    if not errors:
        for key, want in case["expected_args"].items():
            if args.get(key) != want:
                errors.append(f"argument '{key}' is {args.get(key)!r}, expected {want!r}")
    result["args_valid"] = not errors
    result["errors"].extend(errors)
    result["valid"] = not errors
    return result


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def summarize(scored: list[dict]) -> dict:
    """Aggregate metrics. Each item needs `group` plus score_attempt() fields."""
    should_call = [s for s in scored if s["group"] != "no_call"]
    no_call = [s for s in scored if s["group"] == "no_call"]
    correct_tool = [s for s in should_call if s["tool_correct"]]
    return {
        "attempts": len(scored),
        "valid_rate": _rate(sum(s["valid"] for s in scored), len(scored)),
        "tool_selection_accuracy": _rate(len(correct_tool), len(should_call)),
        "arg_validity": _rate(sum(bool(s["args_valid"]) for s in correct_tool), len(correct_tool)),
        "false_call_rate": _rate(sum(s["false_call"] for s in no_call), len(no_call)),
        "miss_rate": _rate(sum(not s["called"] for s in should_call), len(should_call)),
        "hard_valid_rate": _rate(
            sum(s["valid"] for s in scored if s["group"] == "hard"),
            sum(1 for s in scored if s["group"] == "hard"),
        ),
    }
