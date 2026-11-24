"""Build the vector index of reviewed cases (D-04, D-37).

Usage:
    python -m kb.ingest

Always rebuilds the Chroma collection from scratch. Only `reviewed: true` cases
are ingested; if any reviewed case fails validation, nothing is ingested.
The embedding text is symptom-side only (title, symptoms, conditions, alarms),
because queries describe symptoms, not root causes.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

from kb.cases import DEFAULT_CASES_DIR, Case, load_cases, load_taxonomy, validate_case
from kb.embedder import Embedder, OllamaEmbedder, build_embedder
from kb.vector_store import DEFAULT_CHROMA_PATH, recreate_collection


class CaseValidationError(RuntimeError):
    def __init__(self, problems: dict[str, list[str]]):
        self.problems = problems
        lines = [f"{case_id}: {p}" for case_id, ps in problems.items() for p in ps]
        super().__init__("reviewed cases failed validation; nothing ingested:\n" + "\n".join(lines))


@dataclass(frozen=True)
class IngestReport:
    ingested: int
    skipped_unreviewed: int
    duration_s: float


def embedding_text(case: Case) -> str:
    alarms = ", ".join(a.replace("_", " ") for a in case.meta["alarm_categories"])
    return "\n".join([
        case.meta["title"],
        f"Alarms: {alarms}",
        f"Symptoms: {case.sections['Symptoms']}",
        f"Conditions: {case.sections['Conditions']}",
    ])


def metadata(case: Case) -> dict:
    m = case.meta
    return {
        "title": m["title"],
        "symptom_component": m["symptom_component"],
        "root_cause_component": m["root_cause_component"],
        "operating_mode": m["operating_mode"],
        "impact": m["impact"],
        "alarm_categories": ",".join(m["alarm_categories"]),
    }


def ingest(
    *,
    embedder: Embedder,
    cases_dir: Path = DEFAULT_CASES_DIR,
    chroma_path: Path = DEFAULT_CHROMA_PATH,
) -> IngestReport:
    start = time.perf_counter()
    all_cases = load_cases(cases_dir)
    reviewed = [c for c in all_cases if c.reviewed]

    taxonomy = load_taxonomy()
    problems = {c.id or c.path.name: errs for c in reviewed if (errs := validate_case(c, taxonomy))}
    if problems:
        raise CaseValidationError(problems)

    # Embed before touching the store, so a failure leaves the old index intact.
    vectors = embedder.embed([embedding_text(c) for c in reviewed]) if reviewed else []
    collection = recreate_collection(chroma_path)
    if reviewed:
        collection.add(
            ids=[c.id for c in reviewed],
            embeddings=vectors,
            documents=[c.path.read_text(encoding="utf-8") for c in reviewed],
            metadatas=[metadata(c) for c in reviewed],
        )
    return IngestReport(len(reviewed), len(all_cases) - len(reviewed), time.perf_counter() - start)


def main() -> int:
    embedder = build_embedder()
    if isinstance(embedder, OllamaEmbedder) and (problem := embedder.preflight()):
        print(f"Error: {problem}")
        return 1
    try:
        report = ingest(embedder=embedder)
    except CaseValidationError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Ingested {report.ingested} reviewed cases "
          f"(skipped {report.skipped_unreviewed} unreviewed) in {report.duration_s:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
