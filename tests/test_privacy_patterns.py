import pytest

from privacy.patterns import Detector, default_detector, load_denylist, load_extra_patterns

D = Detector(denylist=["Riverbend Plant", "Riverbend", "北港示範站"], extra_patterns=[("SERIAL", r"\bXQ\d{8}\b")])


@pytest.mark.parametrize("text, kind", [
    ("unit at 192.168.10.5", "IP"),
    ("MAC 00:1A:2B:3C:4D:5E", "MAC"),
    ("mail tech@example.com", "EMAIL"),
    ("SN: 4F7K22009", "SERIAL"),
    ("serial number 12345678", "SERIAL"),
    ("module AB12-7781 replaced", "SERIAL"),
    ("on 2026-03-02 at noon", "DATE"),
    ("at 2026-03-02T15:44:30 tripped", "DATE"),
    ("visit Riverbend Plant today", "SITE"),
    ("北港示範站的PCS跳機", "SITE"),
    ("unit XQ12345678", "SERIAL"),
])
def test_detects(text, kind):
    assert [h.kind for h in D.find(text)] == [kind]


@pytest.mark.parametrize("text", [
    "See CASE-014 for a similar trip.",
    "Serial fieldbus link between the EMS and PCS.",
    "Checked the 24 V auxiliary supply at 105.2 %Vdc_rated.",
    "Riverbendish is not a site name.",
    "DEV_1 and DEV_123 are pseudonyms.",
])
def test_allows(text):
    assert D.find(text) == []


def test_longer_overlapping_hit_wins():
    hits = D.find("Riverbend Plant tripped")
    assert [(h.kind, h.value) for h in hits] == [("SITE", "Riverbend Plant")]


def test_redact_uses_typed_placeholders():
    assert D.redact("SN: 4F7K22009 at 10.0.0.1, Riverbend") == "[SERIAL] at [IP], [SITE]"


def test_case_insensitive_denylist():
    assert D.redact("riverbend plant") == "[SITE]"


def test_load_local_files(tmp_path):
    (tmp_path / "denylist.local.txt").write_text("﻿# comment\nAlpha Site\n\n北港\n", encoding="utf-8")
    (tmp_path / "privacy.local.toml").write_text('[[patterns]]\nregex = "\\\\bZZ\\\\d{4}\\\\b"\n', encoding="utf-8")
    assert load_denylist(tmp_path / "denylist.local.txt") == ["Alpha Site", "北港"]
    assert load_extra_patterns(tmp_path / "privacy.local.toml") == [("SERIAL", r"\bZZ\d{4}\b")]
    detector = default_detector(tmp_path)
    assert detector.redact("Alpha Site ZZ1234 北港") == "[SITE] [SERIAL] [SITE]"


def test_missing_local_files_are_fine(tmp_path):
    assert default_detector(tmp_path).find("plain text") == []
