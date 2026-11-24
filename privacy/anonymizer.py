"""Local anonymization of parsed logs and free text (D-19, D-36).

- Text: detected identifiers become typed placeholders ([SERIAL], [IP], [SITE], ...).
- device_id: replaced by a pseudonym (DEV_1, DEV_2, ...) that is stable within one log.
  The mapping stays in this object's memory; it is never sent or written to traces.
- Time: absolute timestamps become an offset from the first event plus a coarse
  time-of-day bucket (night 00-06, morning 06-12, afternoon 12-18, evening 18-24).
- Numeric values and units are kept: they are diagnostic and not identifying.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from privacy.patterns import Detector
from tools.parse_log import Event


@dataclass(frozen=True)
class AnonymizedEvent:
    offset_s: int
    time_of_day: str
    device: str
    severity: str
    alarm_category: str
    message: str
    value: float | None
    unit: str

    @property
    def offset(self) -> str:
        hours, rest = divmod(self.offset_s, 3600)
        minutes, seconds = divmod(rest, 60)
        return f"+{hours:02d}:{minutes:02d}:{seconds:02d}"

    def to_line(self) -> str:
        value = "" if self.value is None else f" value={self.value:g}{(' ' + self.unit) if self.unit else ''}"
        return f"{self.offset} ({self.time_of_day}) {self.device} [{self.severity}] {self.alarm_category}: {self.message}{value}"


def time_of_day(ts: datetime) -> str:
    return ("night", "morning", "afternoon", "evening")[ts.hour // 6]


class Anonymizer:
    def __init__(self, detector: Detector):
        self._detector = detector
        self._devices: dict[str, str] = {}

    def pseudonym(self, device_id: str) -> str:
        if not device_id:
            return "DEV_?"
        if device_id not in self._devices:
            # Underscore form: never matches the serial-like rule, even past DEV_99.
            self._devices[device_id] = f"DEV_{len(self._devices) + 1}"
        return self._devices[device_id]

    def text(self, text: str) -> str:
        # Known device IDs inside free text get their pseudonym first, longest first.
        for real in sorted(self._devices, key=len, reverse=True):
            text = text.replace(real, self._devices[real])
        return self._detector.redact(text)

    def events(self, events: list[Event]) -> list[AnonymizedEvent]:
        if not events:
            return []
        ordered = sorted(events, key=lambda e: e.timestamp)
        for e in ordered:
            self.pseudonym(e.device_id)
        t0 = ordered[0].timestamp
        return [
            AnonymizedEvent(
                offset_s=int((e.timestamp - t0).total_seconds()),
                time_of_day=time_of_day(e.timestamp),
                device=self.pseudonym(e.device_id),
                severity=self.text(e.severity),
                alarm_category=self.text(e.alarm_category),
                message=self.text(e.message),
                value=e.value,
                unit=self.text(e.unit),
            )
            for e in ordered
        ]


def events_to_text(events: list[AnonymizedEvent]) -> str:
    return "\n".join(e.to_line() for e in events)
