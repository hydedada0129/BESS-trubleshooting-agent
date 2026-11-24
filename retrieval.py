"""Hybrid case retrieval: BM25 + vector search fused with Reciprocal Rank Fusion.

Written by Claude at the owner's request (D-38); interface and behavior per
SPEC section 5 and D-10 / D-37. Contract: tests/test_retrieval.py.

Flow for search():
    1. vector ranking  (Chroma, filters applied via `where`)
    2. BM25 ranking    (in memory, filters applied here, zero-score docs dropped)
    3. RRF fusion      score = sum(1 / (RRF_K + rank)) over the lists a case appears in
    4. top k           -> list[SearchResult]
"""

from __future__ import annotations

import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from kb.cases import DEFAULT_CASES_DIR, Case, load_cases
from kb.embedder import Embedder, build_embedder
from kb.ingest import embedding_text
from kb.search_types import SearchResult
from kb.vector_store import DEFAULT_CHROMA_PATH, get_collection

RRF_K = 60  # standard RRF constant (D-10)
MIN_CANDIDATES = 20  # each ranker returns at least this many candidates before fusion


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens; underscores split ("dc_overvoltage" -> "dc", "overvoltage").

    Used for both indexing and queries, so they always match the same way.
    CJK text yields no tokens: cross-language matching is the vector side's job (D-37).
    """
    return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))


def rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion. Each ranking is a list of IDs, best first (rank 1)."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


def build_where(component: str | None, operating_mode: str | None) -> dict | None:
    """Chroma `where` clause. A single condition must not be wrapped in $and."""
    conditions = []
    if component:
        conditions.append({"symptom_component": component})
    if operating_mode:
        conditions.append({"operating_mode": operating_mode})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


class Retriever:
    def __init__(
        self,
        *,
        cases_dir: Path = DEFAULT_CASES_DIR,
        chroma_path: Path = DEFAULT_CHROMA_PATH,
        embedder: Embedder | None = None,
    ):
        # Only reviewed cases are searchable or retrievable (D-04).
        self._cases: dict[str, Case] = {c.id: c for c in load_cases(cases_dir, reviewed_only=True)}
        self._embedder = embedder or build_embedder()
        try:
            self._collection = get_collection(chroma_path)
        except Exception as exc:  # chromadb raises different types across versions
            raise RuntimeError(f"case index not found at {chroma_path}; run `python -m kb.ingest` first") from exc

        # BM25 over the same symptom-side text used for embeddings (D-37).
        self._bm25_ids = list(self._cases)
        corpus = [tokenize(embedding_text(self._cases[i])) for i in self._bm25_ids]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def get_case(self, case_id: str) -> Case | None:
        return self._cases.get(case_id)

    def search(
        self,
        query: str,
        *,
        component: str | None = None,
        operating_mode: str | None = None,
        k: int = 5,
    ) -> list[SearchResult]:
        if not query.strip() or k < 1 or not self._cases:
            return []
        n_candidates = max(k, MIN_CANDIDATES)
        rankings = [
            self._vector_ranking(query, component, operating_mode, n_candidates),
            self._bm25_ranking(query, component, operating_mode, n_candidates),
        ]
        scores = rrf(rankings)
        ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[:k]  # ties broken by ID for stability
        return [self._result(cid, scores[cid], rank) for rank, cid in enumerate(ordered, start=1)]

    # --- rankers -------------------------------------------------------------

    def _vector_ranking(self, query: str, component: str | None, mode: str | None, n: int) -> list[str]:
        n = min(n, self._collection.count())
        if n == 0:
            return []
        result = self._collection.query(
            query_embeddings=self._embedder.embed([query]),
            n_results=n,
            where=build_where(component, mode),
        )
        # Guard against a stale index: keep only reviewed cases known to this retriever.
        return [cid for cid in result["ids"][0] if cid in self._cases]

    def _bm25_ranking(self, query: str, component: str | None, mode: str | None, n: int) -> list[str]:
        tokens = tokenize(query)
        if self._bm25 is None or not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        hits = [
            (score, cid)
            for cid, score in zip(self._bm25_ids, scores)
            if score > 0 and self._matches(self._cases[cid], component, mode)
        ]
        hits.sort(key=lambda h: (-h[0], h[1]))
        return [cid for _, cid in hits[:n]]

    # --- helpers -------------------------------------------------------------

    @staticmethod
    def _matches(case: Case, component: str | None, mode: str | None) -> bool:
        # component filters on symptom_component so misleading cases stay findable (D-37).
        if component and case.meta["symptom_component"] != component:
            return False
        if mode and case.meta["operating_mode"] != mode:
            return False
        return True

    def _result(self, case_id: str, score: float, rank: int) -> SearchResult:
        meta = self._cases[case_id].meta
        return SearchResult(
            case_id=case_id,
            title=meta["title"],
            score=score,
            rank=rank,
            symptom_component=meta["symptom_component"],
            root_cause_component=meta["root_cause_component"],
        )
