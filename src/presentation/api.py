"""FastAPI presentation layer — /ingest and /search endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.application.ingest_service import IngestService
from src.application.search_index import SearchIndex
from src.domain.models import SearchRequest, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency injectors (overridden in main.py via app.dependency_overrides)
# ---------------------------------------------------------------------------


def get_ingest_service() -> IngestService:  # pragma: no cover
    raise NotImplementedError("Dependency not wired")


def get_search_index() -> SearchIndex:  # pragma: no cover
    raise NotImplementedError("Dependency not wired")


# ---------------------------------------------------------------------------
# POST /ingest
# ---------------------------------------------------------------------------


@router.post("/ingest", response_class=JSONResponse)
async def ingest(
    dry_run: bool = Query(
        default=False,
        description="If true, compute delta manifest only — no writes, no events, no checkpoint advance.",
    ),
    ingest_svc: IngestService = Depends(get_ingest_service),
    search_idx: SearchIndex = Depends(get_search_index),
) -> dict:
    """Run an incremental ingest from Postgres to the lake.

    - **dry_run=true**: read-only manifest; nothing is mutated.
    - **dry_run=false**: write lake files → emit events → advance checkpoint,
      then rebuild the search index from the new delta.
    """
    try:
        manifest = ingest_svc.run(dry_run=dry_run)
    except Exception as exc:
        logger.exception("Ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    # Rebuild search index after a real ingest with new data
    if not dry_run and (
        manifest.customers.delta_row_count > 0
        or manifest.cases.delta_row_count > 0
    ):
        try:
            _rebuild_index_from_lake(search_idx)
        except Exception as exc:
            logger.warning("Index rebuild failed (non-fatal): %s", exc)

    return manifest.model_dump(mode="json")


def _rebuild_index_from_lake(search_idx: SearchIndex) -> None:
    """Trigger a lake-based rebuild of the search index."""
    from src.config import settings

    search_idx.load_from_lake(settings.lake_root)


# ---------------------------------------------------------------------------
# POST /search
# ---------------------------------------------------------------------------


@router.post("/search", response_model=list[SearchResult])
async def search(
    request: SearchRequest,
    search_idx: SearchIndex = Depends(get_search_index),
) -> list[SearchResult]:
    """Search cases using the in-memory TF-IDF index.

    Returns up to **top_k** results sorted descending by relevance score.
    Results are fully deterministic: same query + same data = same ordered list.
    """
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(status_code=422, detail="top_k must be between 1 and 100")

    results = search_idx.search(request.query, top_k=request.top_k)
    return results
