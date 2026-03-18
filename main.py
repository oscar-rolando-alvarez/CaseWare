"""Application entry point.

Usage:
    uvicorn main:app --reload

The FastAPI app is assembled here by wiring concrete infrastructure
adapters to the abstract ports consumed by application services.
"""

from __future__ import annotations

import logging
import sys

import psycopg2
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.ingest_service import IngestService
from src.application.search_index import SearchIndex
from src.config import settings
from src.infrastructure.checkpoint import JsonCheckpointStore
from src.infrastructure.database import (
    PostgresCaseRepository,
    PostgresCustomerRepository,
    make_connection,
)
from src.infrastructure.event_emitter import JsonlEventEmitter
from src.infrastructure.lake_writer import JsonlLakeWriter
from src.presentation.api import (
    get_ingest_service,
    get_search_index,
    router,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Infrastructure wiring (singletons for this process lifetime)
# ---------------------------------------------------------------------------

def _build_ingest_service() -> IngestService:
    conn = make_connection(settings.db_dsn)
    return IngestService(
        customer_repo=PostgresCustomerRepository(conn),
        case_repo=PostgresCaseRepository(conn),
        checkpoint_store=JsonCheckpointStore(settings.checkpoint_path),
        lake_writer=JsonlLakeWriter(settings.lake_root),
        event_emitter=JsonlEventEmitter(settings.events_path),
    )


# Singleton instances
_ingest_service: IngestService | None = None
_search_index: SearchIndex = SearchIndex()


def _get_ingest_service() -> IngestService:
    global _ingest_service
    if _ingest_service is None:
        _ingest_service = _build_ingest_service()
    return _ingest_service


def _get_search_index() -> SearchIndex:
    return _search_index


# ---------------------------------------------------------------------------
# Lifespan: warm up DB connection + load search index from lake
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ARG001
    logger.info("Starting Data Interop Service…")

    # Warm up DB connection eagerly so startup failures are visible immediately
    try:
        _get_ingest_service()
        logger.info("Database connection established (DSN=%s)", settings.db_dsn)
    except psycopg2.OperationalError as exc:
        logger.error("Cannot connect to database: %s — /ingest will fail", exc)

    # Load search index from lake (if lake data already exists)
    _search_index.load_from_lake(settings.lake_root)
    logger.info("Service ready")

    yield  # application runs here

    logger.info("Service shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Data Interop Service",
    description="Incremental ingestion, event emission, and AI-ready search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire dependencies
app.dependency_overrides[get_ingest_service] = _get_ingest_service
app.dependency_overrides[get_search_index] = _get_search_index

app.include_router(router)
