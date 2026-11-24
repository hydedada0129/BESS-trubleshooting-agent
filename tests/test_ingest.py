import shutil

import pytest

from kb.cases import DEFAULT_CASES_DIR, load_cases
from kb.embedder import FakeEmbedder
from kb.ingest import CaseValidationError, embedding_text, ingest
from kb.vector_store import get_collection


@pytest.fixture
def cases_copy(tmp_path):
    dest = tmp_path / "cases"
    shutil.copytree(DEFAULT_CASES_DIR, dest)
    return dest


def set_reviewed(path, value):
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("reviewed: true", f"reviewed: {str(value).lower()}"), encoding="utf-8")


def test_ingests_all_reviewed_cases(tmp_path):
    report = ingest(embedder=FakeEmbedder(), chroma_path=tmp_path / "chroma")
    n_reviewed = len(load_cases(reviewed_only=True))
    assert report.ingested == n_reviewed
    col = get_collection(tmp_path / "chroma")
    assert col.count() == n_reviewed
    got = col.get(ids=["CASE-008"], include=["metadatas", "documents"])
    meta = got["metadatas"][0]
    assert (meta["symptom_component"], meta["root_cause_component"]) == ("dc_side", "bms_interface")
    assert meta["alarm_categories"] == "dc_overvoltage,comm_loss"
    assert "## Root cause" in got["documents"][0]  # full case stored for get_case


def test_rebuild_is_idempotent(tmp_path):
    for _ in range(2):
        ingest(embedder=FakeEmbedder(), chroma_path=tmp_path / "chroma")
    assert get_collection(tmp_path / "chroma").count() == len(load_cases(reviewed_only=True))


def test_unreviewed_cases_are_skipped(cases_copy, tmp_path):
    set_reviewed(cases_copy / "CASE-001.md", False)
    report = ingest(embedder=FakeEmbedder(), cases_dir=cases_copy, chroma_path=tmp_path / "chroma")
    assert report.skipped_unreviewed == 1
    assert get_collection(tmp_path / "chroma").get(ids=["CASE-001"])["ids"] == []


def test_invalid_reviewed_case_stops_ingest_and_keeps_old_index(cases_copy, tmp_path):
    chroma = tmp_path / "chroma"
    ingest(embedder=FakeEmbedder(), cases_dir=cases_copy, chroma_path=chroma)
    before = get_collection(chroma).count()
    bad = cases_copy / "CASE-002.md"
    bad.write_text(bad.read_text(encoding="utf-8").replace("impact: trip", "impact: explosion"), encoding="utf-8")
    with pytest.raises(CaseValidationError) as exc:
        ingest(embedder=FakeEmbedder(), cases_dir=cases_copy, chroma_path=chroma)
    assert "CASE-002" in str(exc.value)
    assert get_collection(chroma).count() == before


def test_embedding_text_is_symptom_side_only():
    case = next(c for c in load_cases() if c.id == "CASE-008")
    text = embedding_text(case)
    assert case.meta["title"] in text
    assert "dc overvoltage" in text
    assert case.sections["Symptoms"][:40] in text
    assert case.sections["Root cause"][:40] not in text
    assert case.sections["Resolution"][:40] not in text
