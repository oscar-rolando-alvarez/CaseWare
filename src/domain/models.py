"""Domain models — pure data classes with no external dependencies."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


class Customer(BaseModel):
    model_config = ConfigDict(frozen=True)

    customer_id: int
    name: str
    email: str
    country: str
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "country": self.country,
            "updated_at": self.updated_at.isoformat(),
        }


class Case(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: int
    customer_id: int
    title: str
    description: str
    status: str
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "customer_id": self.customer_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "updated_at": self.updated_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Ingest manifest
# ---------------------------------------------------------------------------


class TableManifest(BaseModel):
    delta_row_count: int
    lake_paths: list[str]
    schema_fingerprint: str


class IngestManifest(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    customers: TableManifest
    cases: TableManifest
    checkpoint_before: str
    checkpoint_after: str
    dry_run: bool


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class IngestEvent(BaseModel):
    table: str
    run_id: str
    schema_fingerprint: str
    delta_row_count: int
    lake_paths: list[str]
    checkpoint_after: str

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    case_id: int
    score: float
    title: str
    status: str


# ---------------------------------------------------------------------------
# Schema fingerprint helper (belongs to domain — pure computation)
# ---------------------------------------------------------------------------

CUSTOMERS_SCHEMA: list[tuple[str, str]] = [
    ("customer_id", "bigint"),
    ("country", "text"),
    ("email", "text"),
    ("name", "text"),
    ("updated_at", "timestamptz"),
]

CASES_SCHEMA: list[tuple[str, str]] = [
    ("case_id", "bigint"),
    ("customer_id", "bigint"),
    ("description", "text"),
    ("status", "text"),
    ("title", "text"),
    ("updated_at", "timestamptz"),
]


def compute_schema_fingerprint(schema_pairs: list[tuple[str, str]]) -> str:
    """SHA-256 over sorted 'col:type' pairs — deterministic across runs."""
    sorted_pairs = sorted(schema_pairs)
    payload = "|".join(f"{col}:{typ}" for col, typ in sorted_pairs)
    return hashlib.sha256(payload.encode()).hexdigest()


CUSTOMERS_FINGERPRINT: str = compute_schema_fingerprint(CUSTOMERS_SCHEMA)
CASES_FINGERPRINT: str = compute_schema_fingerprint(CASES_SCHEMA)
