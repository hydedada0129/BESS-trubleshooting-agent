from pathlib import Path

import pytest

from kb.cases import load_taxonomy
from tools.parse_log import LogFormatError, parse_log_file, parse_log_text

HEADER = "timestamp,device_id,severity,alarm_category,message,value,unit\n"
SAMPLES = Path(__file__).resolve().parent.parent / "samples" / "logs"


def test_parses_valid_rows():
    log = parse_log_text(HEADER + "2026-03-02T15:44:34,PCS-01,critical,dc_overvoltage,DC overvoltage trip,105.2,%Vdc_rated\n")
    assert log.warnings == []
    e = log.events[0]
    assert (e.timestamp.hour, e.device_id, e.alarm_category, e.value, e.unit) == (15, "PCS-01", "dc_overvoltage", 105.2, "%Vdc_rated")


def test_spaces_after_commas_and_bom():
    log = parse_log_text("﻿timestamp, device_id, severity, alarm_category, message, value, unit\n"
                         "2026-03-02T15:44:34, PCS-01, info, comm_loss, link lost, , \n")
    assert log.events[0].value is None
    assert log.events[0].device_id == "PCS-01"


def test_bad_rows_are_skipped_with_warnings():
    log = parse_log_text(HEADER + "\n".join([
        "not-a-time,PCS-01,info,comm_loss,x,,",
        "2026-03-02T15:00:00,PCS-01,info,,missing category,,",
        "2026-03-02T15:00:01,PCS-01,info,comm_loss,too few fields",
        "2026-03-02T15:00:02,PCS-01,info,comm_loss,bad value,abc,V",
        "2026-03-02T15:00:03,PCS-01,info,comm_loss,ok,,",
        "",
    ]))
    assert len(log.events) == 2
    assert log.events[0].value is None
    joined = "\n".join(log.warnings)
    for expected in ["line 2: invalid timestamp", "line 3: missing alarm_category", "line 4: expected 7 fields",
                     "line 5: non-numeric value"]:
        assert expected in joined


def test_unknown_category_is_kept_with_warning():
    log = parse_log_text(HEADER + "2026-03-02T15:00:00,PCS-01,info,made_up,x,,\n", alarm_categories=["comm_loss"])
    assert len(log.events) == 1
    assert "unknown alarm_category 'made_up'" in log.warnings[0]


@pytest.mark.parametrize("text", ["", "a,b,c\n1,2,3\n"])
def test_wrong_or_missing_header_is_rejected(text):
    with pytest.raises(LogFormatError):
        parse_log_text(text)


@pytest.mark.parametrize("path", sorted(SAMPLES.glob("*.csv")), ids=lambda p: p.name)
def test_sample_logs_parse_cleanly(path):
    log = parse_log_file(path, alarm_categories=load_taxonomy()["alarm_categories"])
    assert log.events
    assert log.warnings == []
