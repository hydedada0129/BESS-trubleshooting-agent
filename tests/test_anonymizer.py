from datetime import datetime

from privacy.anonymizer import Anonymizer, events_to_text, time_of_day
from privacy.patterns import Detector
from tools.parse_log import Event, parse_log_text

DETECTOR = Detector(denylist=["Riverbend Plant", "北港示範站"])


def ev(ts, device="AB12-7781", message="x", value=None, unit=""):
    return Event(datetime.fromisoformat(ts), device, "warning", "comm_loss", message, value, unit)


def test_relative_time_and_buckets_sorted_by_time():
    out = Anonymizer(DETECTOR).events([ev("2026-03-02T15:44:34"), ev("2026-03-02T05:40:00"), ev("2026-03-02T19:00:00")])
    assert [e.offset for e in out] == ["+00:00:00", "+10:04:34", "+13:20:00"]
    assert [e.time_of_day for e in out] == ["night", "afternoon", "evening"]


def test_time_of_day_boundaries():
    assert [time_of_day(datetime(2026, 1, 1, h)) for h in (0, 5, 6, 11, 12, 17, 18, 23)] == \
        ["night", "night", "morning", "morning", "afternoon", "afternoon", "evening", "evening"]


def test_device_pseudonyms_are_stable_and_ordered():
    a = Anonymizer(DETECTOR)
    out = a.events([ev("2026-03-02T10:00:00", "AB12-7781"), ev("2026-03-02T10:00:01", "CD34-9900"),
                    ev("2026-03-02T10:00:02", "AB12-7781")])
    assert [e.device for e in out] == ["DEV_1", "DEV_2", "DEV_1"]


def test_device_id_inside_message_uses_pseudonym():
    out = Anonymizer(DETECTOR).events([ev("2026-03-02T10:00:00", "PCS-01", message="PCS-01 tripped, PCS-012 ok")])
    assert out[0].message.startswith("DEV_1 tripped")


def test_message_identifiers_are_redacted():
    out = Anonymizer(DETECTOR).events([ev("2026-03-02T10:00:00", message="Riverbend Plant 192.168.1.20 tech@example.com")])
    assert out[0].message == "[SITE] [IP] [EMAIL]"


def test_values_and_units_are_kept():
    line = Anonymizer(DETECTOR).events([ev("2026-03-02T10:00:00", value=105.2, unit="%Vdc_rated")])[0].to_line()
    assert "value=105.2 %Vdc_rated" in line


def test_free_text_description():
    a = Anonymizer(DETECTOR)
    assert a.text("北港示範站 SN: 4F7K22009 一直跳機") == "[SITE] [SERIAL] 一直跳機"


def test_empty_log():
    assert Anonymizer(DETECTOR).events([]) == []


def test_text_output_has_no_dates_or_ids():
    log = parse_log_text("timestamp,device_id,severity,alarm_category,message,value,unit\n"
                         "2026-03-02T15:44:34,AB12-7781,critical,dc_overvoltage,trip at Riverbend Plant,105.2,%Vdc_rated\n")
    text = events_to_text(Anonymizer(DETECTOR).events(log.events))
    assert text == "+00:00:00 (afternoon) DEV_1 [critical] dc_overvoltage: trip at [SITE] value=105.2 %Vdc_rated"
    assert DETECTOR.find(text) == []
