"""Parse the project's generic alarm log CSV (D-20). Runs locally only.

Format: timestamp, device_id, severity, alarm_category, message, value, unit
Timestamps are ISO 8601. Bad rows are skipped with a warning; a wrong header
rejects the whole log.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

EXPECTED_COLUMNS = ["timestamp", "device_id", "severity", "alarm_category", "message", "value", "unit"]


class LogFormatError(ValueError):
    """The log cannot be parsed at all (e.g. wrong header)."""


@dataclass
class Event:
    timestamp: datetime
    device_id: str
    severity: str
    alarm_category: str
    message: str
    value: float | None
    unit: str


@dataclass
class ParsedLog:
    events: list[Event] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_log_file(path: str | Path, *, alarm_categories: list[str] | None = None) -> ParsedLog:
    # utf-8-sig: logs exported from Excel on Windows often start with a BOM.
    return parse_log_text(Path(path).read_text(encoding="utf-8-sig"), alarm_categories=alarm_categories)


def parse_log_text(text: str, *, alarm_categories: list[str] | None = None) -> ParsedLog:
    """Parse CSV text. If `alarm_categories` is given, unknown categories produce a warning (row kept)."""
    reader = csv.reader(io.StringIO(text.lstrip("﻿")), skipinitialspace=True)
    try:
        header = next(reader)
    except StopIteration:
        raise LogFormatError("log is empty") from None
    header = [h.strip().lower() for h in header]
    if header != EXPECTED_COLUMNS:
        raise LogFormatError(f"unexpected header {header}; expected {EXPECTED_COLUMNS}")

    log = ParsedLog()
    for line_no, row in enumerate(reader, start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(EXPECTED_COLUMNS):
            log.warnings.append(f"line {line_no}: expected {len(EXPECTED_COLUMNS)} fields, got {len(row)}; skipped")
            continue
        ts_raw, device_id, severity, category, message, value_raw, unit = (c.strip() for c in row)

        try:
            timestamp = datetime.fromisoformat(ts_raw)
        except ValueError:
            log.warnings.append(f"line {line_no}: invalid timestamp; skipped")
            continue
        if not category:
            log.warnings.append(f"line {line_no}: missing alarm_category; skipped")
            continue
        if alarm_categories is not None and category not in alarm_categories:
            log.warnings.append(f"line {line_no}: unknown alarm_category {category!r}; kept")

        value: float | None = None
        if value_raw:
            try:
                value = float(value_raw)
            except ValueError:
                log.warnings.append(f"line {line_no}: non-numeric value; value dropped")

        log.events.append(Event(timestamp, device_id, severity, category, message, value, unit))
    return log
