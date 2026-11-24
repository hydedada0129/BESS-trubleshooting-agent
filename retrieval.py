"""Hybrid case retrieval: BM25 + vector search fused with Reciprocal Rank Fusion.

Written by Claude at the owner's request (D-38); interface and behavior per
SPEC section 5 and D-10 / D-37. Contract: tests/test_retrieval.py.

What this module does
---------------------
Given a fault description (the query), find the most similar reviewed cases.
This is the "R" (retrieval) in RAG: the agent later puts these cases into the
prompt so the model answers from field experience instead of guessing.

Why two search methods ("hybrid")
---------------------------------
- BM25 (keyword search) matches exact words. It is good at precise terms such
  as alarm names ("precharge failure"), but it does not understand synonyms or
  other languages.
- Vector search (semantic search) compares meaning. bge-m3 turns text into a
  vector; similar meanings give nearby vectors, even across languages
  (a Chinese query can find an English case). It is weaker on exact terms.
Using both covers each method's blind spot.

Flow for search()
-----------------
    1. vector ranking  (Chroma, filters applied via `where`)
    2. BM25 ranking    (in memory, filters applied here, zero-score docs dropped)
    3. RRF fusion      score = sum(1 / (RRF_K + rank)) over the lists a case appears in
    4. top k           -> list[SearchResult]

Each ranker returns only an ordered list of case IDs (best first). Raw scores
are thrown away on purpose: BM25 scores and vector distances use different
scales and cannot be added together, but ranks can always be combined.
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

# RRF constant from the original RRF paper; 60 is the common default (D-10).
# A larger value flattens the difference between rank 1 and rank 10, so one
# ranker cannot dominate just because it put a case first.
RRF_K = 60

# How many candidates each ranker returns before fusion. If each side returned
# only k (e.g. 5), a case ranked 6th by both rankers could never surface, even
# though agreement between the two is exactly what RRF rewards.
MIN_CANDIDATES = 20


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words for BM25.

    Example: "DC_overvoltage trip, end-of-charge!" -> ["dc", "overvoltage", "trip", "end", "of", "charge"]

    - Lowercase, so "Trip" and "trip" are the same word.
    - Underscores become spaces, so taxonomy names like "dc_overvoltage" match
      the words "dc overvoltage" in case text.
    - The regex keeps only runs of a-z / 0-9, which drops punctuation
      ("trip," -> "trip").

    The SAME function is used to build the index and to split queries. If they
    differed, a word could be stored one way and searched another way and never match.

    Chinese text yields no tokens. That is intentional: the cases are English,
    so BM25 could not match Chinese anyway. Cross-language matching is the
    vector side's job (D-37).
    """
    return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))


def rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: merge several ranked lists into one score per ID.

    Each ranking is a list of IDs, best first (position 0 = rank 1). A case gets
    1 / (k + rank) from every list it appears in; lists it is missing from add
    nothing. So:
      - a case ranked high by BOTH rankers gets the highest score;
      - a case found by only ONE ranker still gets a score (it is not dropped).

    Worked example (k = 60), also checked in tests/test_retrieval_unit.py:
        A: BM25 rank 1, vector rank 3 -> 1/61 + 1/63 = 0.03226
        B: BM25 rank 2, vector rank 1 -> 1/62 + 1/61 = 0.03252   <- best
        C: vector rank 2 only         -> 1/62        = 0.01613
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):  # start=1: ranks begin at 1, not 0
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


def build_where(component: str | None, operating_mode: str | None) -> dict | None:
    """Build Chroma's `where` filter from the optional search filters.

    Chroma's syntax depends on how many conditions there are:
        none -> None (no filter)
        one  -> {"field": "value"}
        two  -> {"$and": [{...}, {...}]}
    Wrapping a single condition in $and is rejected by Chroma, hence the branches.

    `component` is matched against symptom_component (where the alarm appears),
    not root_cause_component: users only know the symptom, and filtering on the
    root cause would hide misleading cases such as CASE-008 (D-37).
    """
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
    """Searches reviewed cases. Build once, then call search() / get_case() many times.

    All slow work (reading case files, building the BM25 index, opening Chroma)
    happens once in __init__, so each search() only does the actual lookup.
    """

    def __init__(
        self,
        *,  # everything after * must be passed by name: Retriever(cases_dir=...)
        cases_dir: Path = DEFAULT_CASES_DIR,
        chroma_path: Path = DEFAULT_CHROMA_PATH,
        embedder: Embedder | None = None,
    ):
        # 1. Load cases into a dict {case_id: Case} for O(1) lookup by ID.
        #    reviewed_only=True: unreviewed drafts are never searchable (D-04).
        self._cases: dict[str, Case] = {c.id: c for c in load_cases(cases_dir, reviewed_only=True)}

        # 2. The embedder turns the query into a vector. Tests pass FakeEmbedder;
        #    in real use the default is bge-m3 via Ollama (config/settings.toml).
        self._embedder = embedder or build_embedder()

        # 3. Open the vector index built by `python -m kb.ingest`.
        try:
            self._collection = get_collection(chroma_path)
        except Exception as exc:  # chromadb raises different exception types across versions
            raise RuntimeError(f"case index not found at {chroma_path}; run `python -m kb.ingest` first") from exc

        # 4. Build the BM25 index in memory. BM25 only knows documents by position
        #    (0, 1, 2, ...), so we keep a parallel list mapping position -> case ID.
        #    The indexed text is the same symptom-side text used for embeddings
        #    (title, alarms, symptoms, conditions), so both rankers compare the
        #    query against the same kind of content (D-37).
        self._bm25_ids = list(self._cases)
        corpus = [tokenize(embedding_text(self._cases[i])) for i in self._bm25_ids]
        self._bm25 = BM25Okapi(corpus) if corpus else None  # BM25Okapi cannot be built from an empty corpus

    def get_case(self, case_id: str) -> Case | None:
        """Full case by ID, or None if unknown or unreviewed (dict.get returns None when missing)."""
        return self._cases.get(case_id)

    def search(
        self,
        query: str,
        *,
        component: str | None = None,
        operating_mode: str | None = None,
        k: int = 5,
    ) -> list[SearchResult]:
        """Return up to k reviewed cases most similar to the query, best first."""
        # Nothing sensible to search for: return an empty list rather than raising.
        if not query.strip() or k < 1 or not self._cases:
            return []

        # Ask each ranker for more candidates than we will return (see MIN_CANDIDATES).
        n_candidates = max(k, MIN_CANDIDATES)
        rankings = [
            self._vector_ranking(query, component, operating_mode, n_candidates),
            self._bm25_ranking(query, component, operating_mode, n_candidates),
        ]

        # Fuse the two ranked lists into one score per case.
        scores = rrf(rankings)

        # Sort by score, highest first. The key (-score, case_id) means: higher
        # score wins; on an exact tie, the smaller case ID wins, so results are
        # always in the same order (stable, reproducible output). Then keep top k.
        ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[:k]
        return [self._result(cid, scores[cid], rank) for rank, cid in enumerate(ordered, start=1)]

    # --- rankers -------------------------------------------------------------
    # Each ranker returns a list of case IDs, best first, with filters applied.

    def _vector_ranking(self, query: str, component: str | None, mode: str | None, n: int) -> list[str]:
        """Semantic search in Chroma."""
        # Never ask Chroma for more results than the collection holds.
        n = min(n, self._collection.count())
        if n == 0:
            return []
        result = self._collection.query(
            query_embeddings=self._embedder.embed([query]),  # a list, because Chroma accepts many queries at once
            n_results=n,
            where=build_where(component, mode),  # Chroma applies the filters for us
        )
        # Results are "lists of lists" (one inner list per query); we sent one
        # query, so take [0]. Chroma already sorts by similarity, best first.
        # Keep only IDs this retriever knows: if the index is stale (e.g. a case
        # was un-reviewed after ingest), the extra case is discarded here.
        return [cid for cid in result["ids"][0] if cid in self._cases]

    def _bm25_ranking(self, query: str, component: str | None, mode: str | None, n: int) -> list[str]:
        """Keyword search with BM25."""
        tokens = tokenize(query)
        # No index, or the query has no usable words (e.g. a Chinese-only query).
        if self._bm25 is None or not tokens:
            return []

        # One score per indexed document, in the same order as self._bm25_ids.
        scores = self._bm25.get_scores(tokens)

        # zip pairs each case ID with its score. Keep a case only if:
        #   - score > 0: it shares at least one word with the query. Without this,
        #     every case would enter the BM25 list and RRF would treat
        #     "no keyword match at all" as if BM25 had found it;
        #   - it passes the filters. Chroma's `where` only filters the vector
        #     side, so BM25 must apply the same filters itself.
        hits = [
            (score, cid)
            for cid, score in zip(self._bm25_ids, scores)
            if score > 0 and self._matches(self._cases[cid], component, mode)
        ]
        # Highest score first; ties broken by case ID for a stable order.
        hits.sort(key=lambda h: (-h[0], h[1]))
        return [cid for _, cid in hits[:n]]

    # --- helpers -------------------------------------------------------------

    @staticmethod  # does not use self: a plain function grouped with the class
    def _matches(case: Case, component: str | None, mode: str | None) -> bool:
        """Python version of build_where(), used on the BM25 side.

        A filter left as None means "no restriction". Same rule as Chroma:
        component is compared with symptom_component (D-37).
        """
        if component and case.meta["symptom_component"] != component:
            return False
        if mode and case.meta["operating_mode"] != mode:
            return False
        return True

    def _result(self, case_id: str, score: float, rank: int) -> SearchResult:
        """Package one hit as a SearchResult (kb/search_types.py) for the agent's tools."""
        meta = self._cases[case_id].meta
        return SearchResult(
            case_id=case_id,
            title=meta["title"],
            score=score,  # the RRF score: only meaningful for ordering, not as a probability
            rank=rank,  # 1 = best match
            symptom_component=meta["symptom_component"],
            root_cause_component=meta["root_cause_component"],
        )
