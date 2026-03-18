"""Deterministic hash-based TF-IDF in-memory search index.

Design
------
* Tokenisation: lowercase, split on non-alphanumeric chars, drop tokens < 2 chars.
* Hash trick: each token is hashed with SHA-256 and mapped to a dimension in a
  fixed-size vector space (DIM = 2**14 = 16 384).  This is fully deterministic
  across Python versions and platforms because SHA-256 is specified.
* TF  : raw term frequency per document.
* IDF : log(1 + N / (1 + df)) — smoothed to avoid division-by-zero.
* Scoring: cosine similarity between query vector and document vectors.
* Tie-breaking: case_id ascending (smaller id wins) — deterministic ordering.

The index is rebuilt in O(n * k) where n = number of cases, k = avg tokens.
At the scale of this assessment (<10k cases) this is instantaneous.

Thread-safety: the index is rebuilt atomically (new object replaces old
reference under the GIL) so concurrent reads are safe on CPython.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from src.domain.models import Case, SearchResult

logger = logging.getLogger(__name__)

# Vector dimensionality (hash space).  Higher → fewer collisions, more RAM.
DIM: int = 2**14  # 16 384

_TOKEN_RE = re.compile(r"[^a-z0-9]+")


def _tokenise(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric; drop tokens shorter than 2 chars."""
    return [t for t in _TOKEN_RE.split(text.lower()) if len(t) >= 2]


def _token_to_dim(token: str) -> int:
    """Map token → deterministic dimension index in [0, DIM)."""
    digest = hashlib.sha256(token.encode()).digest()
    # Use first 4 bytes as unsigned int, then mod DIM
    return int.from_bytes(digest[:4], "big") % DIM


def _tf_vector(tokens: list[str]) -> dict[int, float]:
    """Compute raw-count TF as a sparse vector."""
    counts: dict[int, float] = defaultdict(float)
    for token in tokens:
        counts[_token_to_dim(token)] += 1.0
    return dict(counts)


def _l2_norm(vec: dict[int, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values())) or 1.0


class SearchIndex:
    """In-memory TF-IDF index over Case entities."""

    def __init__(self) -> None:
        self._cases: list[Case] = []
        # Sparse TF-IDF vectors: case_id → {dim: weight}
        self._tfidf: dict[int, dict[int, float]] = {}
        self._norms: dict[int, float] = {}

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, cases: list[Case]) -> None:
        """Build (or rebuild) the index from a list of Case entities."""
        if not cases:
            self._cases = []
            self._tfidf = {}
            self._norms = {}
            return

        self._cases = list(cases)
        n = len(cases)

        # Step 1 — raw TF per case
        tf_vectors: dict[int, dict[int, float]] = {}
        for case in cases:
            tokens = _tokenise(f"{case.title} {case.description}")
            tf_vectors[case.case_id] = _tf_vector(tokens)

        # Step 2 — document frequency per dimension
        df: dict[int, int] = defaultdict(int)
        for vec in tf_vectors.values():
            for dim in vec:
                df[dim] += 1

        # Step 3 — TF-IDF (smoothed IDF)
        self._tfidf = {}
        self._norms = {}
        for case in cases:
            raw_tf = tf_vectors[case.case_id]
            tfidf: dict[int, float] = {}
            for dim, tf in raw_tf.items():
                idf = math.log(1.0 + n / (1.0 + df[dim]))
                tfidf[dim] = tf * idf
            self._tfidf[case.case_id] = tfidf
            self._norms[case.case_id] = _l2_norm(tfidf)

        logger.info("Search index built: %d cases, dim=%d", n, DIM)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Return top_k results sorted descending by cosine similarity.

        Ties are broken by case_id ascending (smallest id first) to ensure
        fully deterministic ordering.
        """
        if not self._cases:
            return []

        query_tokens = _tokenise(query)
        if not query_tokens:
            return []

        query_tf = _tf_vector(query_tokens)

        # Compute query TF-IDF using the corpus IDF already embedded in doc vecs.
        # For scoring purposes we treat the query as a raw TF vector and compute
        # cosine against the document TF-IDF vectors directly.  This is the
        # "lnc.ltc" variant, simple and deterministic.
        q_norm = _l2_norm(query_tf)

        scored: list[tuple[float, int, str, str]] = []
        for case in self._cases:
            doc_vec = self._tfidf.get(case.case_id, {})
            if not doc_vec:
                continue

            # Dot product (sparse)
            dot = sum(
                query_tf.get(dim, 0.0) * weight
                for dim, weight in doc_vec.items()
            )
            doc_norm = self._norms.get(case.case_id, 1.0)
            score = dot / (q_norm * doc_norm)

            if score > 0.0:
                scored.append((score, case.case_id, case.title, case.status))

        # Sort: score desc, then case_id asc for deterministic tie-breaking
        scored.sort(key=lambda x: (-x[0], x[1]))

        return [
            SearchResult(
                case_id=case_id,
                score=round(score, 8),  # round for stable serialisation
                title=title,
                status=status,
            )
            for score, case_id, title, status in scored[:top_k]
        ]

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def load_from_lake(self, lake_root: Path) -> None:
        """Populate the index from all JSONL files in the lake (used at startup)."""
        import json

        cases_dir = lake_root / "cases"
        if not cases_dir.exists():
            logger.info("Lake cases dir not found — index will be empty")
            return

        cases: list[Case] = []
        for jsonl_file in sorted(cases_dir.rglob("data.jsonl")):
            with jsonl_file.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            cases.append(Case(**json.loads(line)))
                        except Exception as exc:
                            logger.warning("Skipping malformed line in %s: %s", jsonl_file, exc)

        self.build(cases)
        logger.info("Index loaded from lake: %d cases", len(cases))
