"""Unit tests for retrieval.py helpers (pure functions, no index needed)."""

import pytest

from retrieval import build_where, rrf, tokenize


def test_rrf_hand_calculated_example():
    # A: BM25 1, vector 3; B: BM25 2, vector 1; C: vector 2 only.
    scores = rrf([["A", "B"], ["B", "C", "A"]])
    assert scores["A"] == pytest.approx(1 / 61 + 1 / 63)
    assert scores["B"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["C"] == pytest.approx(1 / 62)
    assert sorted(scores, key=scores.get, reverse=True) == ["B", "A", "C"]


def test_rrf_empty():
    assert rrf([[], []]) == {}


@pytest.mark.parametrize("component, mode, expected", [
    (None, None, None),
    ("dc_side", None, {"symptom_component": "dc_side"}),
    (None, "charging", {"operating_mode": "charging"}),
    ("dc_side", "charging", {"$and": [{"symptom_component": "dc_side"}, {"operating_mode": "charging"}]}),
])
def test_build_where(component, mode, expected):
    assert build_where(component, mode) == expected


def test_tokenize():
    assert tokenize("DC_overvoltage trip, end-of-charge!") == ["dc", "overvoltage", "trip", "end", "of", "charge"]
    assert tokenize("冷卻風扇故障") == []
