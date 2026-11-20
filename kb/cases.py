"""Load and validate troubleshooting case files (D-04, D-33).

A case is a Markdown file with YAML front matter in `cases/`. Files whose
names start with "_" (templates) and README.md are not cases.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES_DIR = REPO_ROOT / "cases"
DEFAULT_TAXONOMY = REPO_ROOT / "config" / "taxonomy.toml"

REQUIRED_FIELDS = [
    "id", "title", "symptom_component", "root_cause_component", "operating_mode",
    "alarm_categories", "impact", "source", "reviewed",
]
REQUIRED_SECTIONS = ["Symptoms", "Conditions", "Troubleshooting steps", "Root cause", "Resolution"]
OPTIONAL_SECTIONS = ["Lessons"]
ID_PATTERN = re.compile(r"^CASE-\d{3}$")

# Confidentiality scan (CLAUDE.md): anything that looks like real identifiers.
_SENSITIVE_PATTERNS = {
    "IPv4 address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "MAC address": re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b"),
    "email address": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "serial number label": re.compile(r"\b(?:SN|S/N|serial(?: no\.?| number)?)\s*[:#]?\s*(?=[A-Za-z0-9-]*\d)[A-Za-z0-9][A-Za-z0-9-]{3,}", re.IGNORECASE),
    # Mixed letter+digit tokens with a dash, e.g. "AB12-7781"; CASE IDs are allowed.
    "serial-like code": re.compile(r"\b(?!CASE-\d{3}\b)(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9]{2,}-[A-Z0-9-]{3,}\b"),
}


@dataclass
class Case:
    path: Path
    meta: dict
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.meta.get("id", "")

    @property
    def reviewed(self) -> bool:
        return self.meta.get("reviewed") is True


def load_taxonomy(path: Path = DEFAULT_TAXONOMY) -> dict[str, list[str]]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def parse_case(path: Path) -> Case:
    text = Path(path).read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing YAML front matter")
    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: front matter is not a mapping")
    sections: dict[str, str] = {}
    current = None
    for line in match.group(2).splitlines():
        heading = re.match(r"^## (.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return Case(path=Path(path), meta=meta, sections={k: v.strip() for k, v in sections.items()})


def case_files(cases_dir: Path = DEFAULT_CASES_DIR) -> list[Path]:
    return sorted(p for p in Path(cases_dir).glob("*.md") if not p.name.startswith("_") and p.name != "README.md")


def load_cases(cases_dir: Path = DEFAULT_CASES_DIR, *, reviewed_only: bool = False) -> list[Case]:
    cases = [parse_case(p) for p in case_files(cases_dir)]
    return [c for c in cases if c.reviewed] if reviewed_only else cases


def find_sensitive(text: str) -> list[str]:
    """Return descriptions of substrings that look like confidential identifiers."""
    hits = []
    for label, pattern in _SENSITIVE_PATTERNS.items():
        hits.extend(f"{label}: {m.group(0)!r}" for m in pattern.finditer(text))
    return hits


def validate_case(case: Case, taxonomy: dict[str, list[str]]) -> list[str]:
    """Return problems with a case (empty list means valid)."""
    m = case.meta
    errors = [f"missing field '{f}'" for f in REQUIRED_FIELDS if f not in m]
    if errors:
        return errors

    if not ID_PATTERN.match(str(m["id"])):
        errors.append(f"id {m['id']!r} does not match CASE-###")
    if case.path.stem != m["id"]:
        errors.append(f"file name {case.path.name} does not match id {m['id']}")
    if not isinstance(m["title"], str) or not m["title"].strip():
        errors.append("title is empty")

    for key, allowed in [
        ("symptom_component", "components"),
        ("root_cause_component", "components"),
        ("operating_mode", "operating_modes"),
        ("impact", "impacts"),
        ("source", "sources"),
    ]:
        if m[key] not in taxonomy[allowed]:
            errors.append(f"{key} {m[key]!r} not in taxonomy.{allowed}")

    alarms = m["alarm_categories"]
    if not isinstance(alarms, list) or not alarms:
        errors.append("alarm_categories must be a non-empty list")
    else:
        errors.extend(f"alarm category {a!r} not in taxonomy" for a in alarms if a not in taxonomy["alarm_categories"])

    if not isinstance(m["reviewed"], bool):
        errors.append("reviewed must be true or false")

    for name in REQUIRED_SECTIONS:
        if not case.sections.get(name):
            errors.append(f"missing or empty section '{name}'")
    for name in case.sections:
        if name not in REQUIRED_SECTIONS + OPTIONAL_SECTIONS:
            errors.append(f"unknown section '{name}'")

    full_text = case.path.read_text(encoding="utf-8")
    errors.extend(f"possible confidential data ({hit})" for hit in find_sensitive(full_text))
    return errors
