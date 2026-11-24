"""The single set of rules for detecting confidential data (D-19, D-36).

Used by case validation (kb/cases.py), log anonymization, and the pre-send
guard. Built-in rules are generic; vendor-specific serial formats and real
site/customer names live only in local files that are never committed:

- config/denylist.local.txt   one term per line, "#" comments
- config/privacy.local.toml   extra regexes: [[patterns]] kind = "SERIAL", regex = "..."
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"

BUILTIN_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("MAC", re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # "SN: 4F7K22009", "serial number 12345678": the value must contain a digit.
    ("SERIAL", re.compile(
        r"\b(?:SN|S/N|serial(?: no\.?| number)?)\s*[:#]?\s*(?=[A-Za-z0-9-]*\d)[A-Za-z0-9][A-Za-z0-9-]{3,}",
        re.IGNORECASE,
    )),
    # Mixed letter+digit codes with a dash, e.g. "AB12-7781". Case IDs are allowed.
    ("SERIAL", re.compile(r"\b(?!CASE-\d{3}\b)(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9]{2,}-[A-Z0-9-]{3,}\b")),
    # Absolute dates can be matched against outage records.
    # Includes full ISO timestamps ("2026-03-02T15:44:30") so they are labelled DATE.
    ("DATE", re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?(?!\d)")),
]


@dataclass(frozen=True)
class Hit:
    kind: str
    value: str
    start: int
    end: int


def _term_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term)
    if term.isascii():
        # Whole-word match for Latin terms ("Site" must not match "Siteline").
        return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
    # CJK has no word boundaries: substring match.
    return re.compile(escaped, re.IGNORECASE)


class Detector:
    def __init__(self, denylist: list[str] | None = None, extra_patterns: list[tuple[str, str]] | None = None):
        self._patterns: list[tuple[str, re.Pattern]] = list(BUILTIN_PATTERNS)
        self._patterns += [(kind, re.compile(regex)) for kind, regex in (extra_patterns or [])]
        # Longest terms first so "North Plant 2" wins over "North Plant".
        terms = sorted({t for t in (denylist or []) if t}, key=len, reverse=True)
        self._patterns += [("SITE", _term_pattern(t)) for t in terms]

    def find(self, text: str) -> list[Hit]:
        """Non-overlapping hits sorted by position; on overlap the longer hit wins."""
        candidates = [
            Hit(kind, m.group(0), m.start(), m.end())
            for kind, pattern in self._patterns
            for m in pattern.finditer(text)
            if m.end() > m.start()
        ]
        candidates.sort(key=lambda h: (h.start, -(h.end - h.start)))
        hits: list[Hit] = []
        for hit in candidates:
            if hits and hit.start < hits[-1].end:
                if hit.end - hit.start > hits[-1].end - hits[-1].start:
                    hits[-1] = hit
                continue
            hits.append(hit)
        return hits

    def redact(self, text: str) -> str:
        """Replace every hit with a typed placeholder such as [SERIAL]."""
        for hit in reversed(self.find(text)):
            text = text[: hit.start] + f"[{hit.kind}]" + text[hit.end :]
        return text


def load_denylist(path: Path) -> list[str]:
    path = Path(path)
    if not path.is_file():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def load_extra_patterns(path: Path) -> list[tuple[str, str]]:
    path = Path(path)
    if not path.is_file():
        return []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return [(p.get("kind", "SERIAL"), p["regex"]) for p in data.get("patterns", [])]


def default_detector(config_dir: Path = CONFIG_DIR) -> Detector:
    """Built-in rules plus the owner's local denylist and extra patterns, if present."""
    config_dir = Path(config_dir)
    return Detector(
        denylist=load_denylist(config_dir / "denylist.local.txt"),
        extra_patterns=load_extra_patterns(config_dir / "privacy.local.toml"),
    )
