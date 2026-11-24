"""Types shared between ingest, retrieval.py (owner-written) and the agent."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    case_id: str
    title: str
    score: float  # higher is better (e.g. RRF score)
    rank: int  # 1-based
    symptom_component: str
    root_cause_component: str
