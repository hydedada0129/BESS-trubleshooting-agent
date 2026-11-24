"""Contract tests for retrieval.py (written by the owner; see SPEC section 5, D-37).

Skipped until retrieval.py exists at the repo root. Uses FakeEmbedder and a
temporary Chroma index, so no Ollama is needed.

Expected interface:

    class Retriever:
        def __init__(self, *, cases_dir=..., chroma_path=..., embedder=None): ...
        def search(self, query, *, component=None, operating_mode=None, k=5) -> list[SearchResult]: ...
        def get_case(self, case_id) -> Case | None: ...

`component` filters on symptom_component. Only reviewed cases are searchable.
"""

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if not (REPO_ROOT / "retrieval.py").exists():
    pytest.skip("retrieval.py not written yet", allow_module_level=True)

from retrieval import Retriever  # noqa: E402  (import errors must fail, not skip)

from kb.cases import DEFAULT_CASES_DIR, Case  # noqa: E402
from kb.embedder import FakeEmbedder  # noqa: E402
from kb.ingest import ingest  # noqa: E402
from kb.search_types import SearchResult  # noqa: E402

UNREVIEWED = """---
id: CASE-999
title: Zebrafault alarm during standby
symptom_component: dc_side
root_cause_component: dc_side
operating_mode: standby
alarm_categories: [insulation_fault]
impact: warning
source: synthetic
reviewed: false
---

## Symptoms

Zebrafault zebrafault zebrafault.

## Conditions

Standby.

## Troubleshooting steps

1. Checked.

## Root cause

Unknown.

## Resolution

None.
"""


@pytest.fixture(scope="module")
def retriever(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("retrieval")
    cases_dir = tmp / "cases"
    shutil.copytree(DEFAULT_CASES_DIR, cases_dir)
    (cases_dir / "CASE-999.md").write_text(UNREVIEWED, encoding="utf-8")
    embedder = FakeEmbedder()
    ingest(embedder=embedder, cases_dir=cases_dir, chroma_path=tmp / "chroma")
    return Retriever(cases_dir=cases_dir, chroma_path=tmp / "chroma", embedder=embedder)


def ids(results):
    return [r.case_id for r in results]


def test_result_shape(retriever):
    results = retriever.search("DC overvoltage trip")
    assert 0 < len(results) <= 5
    assert all(isinstance(r, SearchResult) for r in results)
    assert [r.rank for r in results] == list(range(1, len(results) + 1))
    assert len(set(ids(results))) == len(results)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_k_is_respected(retriever):
    assert len(retriever.search("trip", k=3)) == 3
    assert len(retriever.search("trip", k=100)) <= 30


def test_component_filter_uses_symptom_component(retriever):
    results = retriever.search("overvoltage trip", component="dc_side")
    assert results
    assert {r.symptom_component for r in results} == {"dc_side"}


def test_operating_mode_filter(retriever):
    results = retriever.search("trip", operating_mode="standby")
    assert results
    for r in results:
        assert retriever.get_case(r.case_id).meta["operating_mode"] == "standby"


def test_exact_alarm_term_ranks_high(retriever):
    assert "CASE-002" in ids(retriever.search("precharge failure", k=3))


def test_chinese_query_finds_english_case(retriever):
    assert "CASE-009" in ids(retriever.search("冷卻風扇故障"))


def test_misleading_cases_found_by_symptom(retriever):
    found = ids(retriever.search("DC overvoltage trip at end of charging", component="dc_side"))
    assert {"CASE-008", "CASE-022"} <= set(found)


def test_unreviewed_cases_are_not_searchable(retriever):
    assert "CASE-999" not in ids(retriever.search("zebrafault", k=30))
    assert retriever.get_case("CASE-999") is None


def test_get_case(retriever):
    case = retriever.get_case("CASE-008")
    assert isinstance(case, Case)
    assert case.id == "CASE-008"
    assert retriever.get_case("CASE-404") is None
