"""Pytest fixtures shared across tests.

All infrastructure is replaced with in-memory / tmp-directory fakes so the
tests run without a live database.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.application.ingest_service import IngestService
from src.application.search_index import SearchIndex
from src.domain.models import Case, Customer
from src.domain.ports import (
    CaseRepository,
    CheckpointStore,
    CustomerRepository,
    EventEmitter,
    LakeWriter,
)
from src.domain.models import IngestEvent
from src.infrastructure.checkpoint import JsonCheckpointStore
from src.infrastructure.event_emitter import JsonlEventEmitter
from src.infrastructure.lake_writer import JsonlLakeWriter
from src.presentation.api import get_ingest_service, get_search_index

# ---------------------------------------------------------------------------
# In-memory fakes
# ---------------------------------------------------------------------------

BASE_TS = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _make_customer(cid: int, days_ago: int = 0) -> Customer:
    return Customer(
        customer_id=cid,
        name=f"Customer {cid}",
        email=f"customer{cid}@example.com",
        country="US",
        updated_at=BASE_TS + timedelta(days=days_ago),
    )


def _make_case(
    case_id: int,
    customer_id: int,
    days_ago: int = 0,
    title: str = "Default case",
    description: str = "Default description",
    status: str = "open",
) -> Case:
    return Case(
        case_id=case_id,
        customer_id=customer_id,
        title=title,
        description=description,
        status=status,
        updated_at=BASE_TS + timedelta(days=days_ago),
    )


class FakeCustomerRepository(CustomerRepository):
    def __init__(self, customers: list[Customer]) -> None:
        self._customers = customers

    def fetch_since(self, since: datetime) -> list[Customer]:
        return [c for c in self._customers if c.updated_at > since]


class FakeCaseRepository(CaseRepository):
    def __init__(self, cases: list[Case]) -> None:
        self._cases = cases

    def fetch_since(self, since: datetime) -> list[Case]:
        return [c for c in self._cases if c.updated_at > since]


class FakeEventEmitter(EventEmitter):
    def __init__(self) -> None:
        self.emitted: list[IngestEvent] = []

    def emit(self, event: IngestEvent) -> None:
        self.emitted.append(event)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dirs() -> Generator[dict[str, Path], None, None]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        yield {
            "root": root,
            "state": root / "state",
            "lake": root / "lake",
            "events": root / "events",
        }


@pytest.fixture()
def seed_customers() -> list[Customer]:
    return [_make_customer(i, days_ago=i) for i in range(1, 6)]


@pytest.fixture()
def seed_cases() -> list[Case]:
    return [
        _make_case(1, 1, days_ago=1, title="Billing discrepancy", description="billing payments invoice"),
        _make_case(2, 1, days_ago=2, title="Fraud alert AML", description="fraud aml suspicious transaction"),
        _make_case(3, 2, days_ago=3, title="Compliance audit", description="compliance audit regulatory"),
        _make_case(4, 2, days_ago=4, title="Onboarding KYC", description="onboarding kyc identity verification"),
        _make_case(5, 3, days_ago=5, title="Payment reconciliation", description="payment reconciliation mismatch"),
    ]


@pytest.fixture()
def ingest_service_factory(tmp_dirs: dict[str, Path]):
    """Factory that creates an IngestService with configurable repos."""
    def _factory(
        customers: list[Customer],
        cases: list[Case],
        emitter: FakeEventEmitter | None = None,
    ) -> tuple[IngestService, FakeEventEmitter]:
        _emitter = emitter or FakeEventEmitter()
        svc = IngestService(
            customer_repo=FakeCustomerRepository(customers),
            case_repo=FakeCaseRepository(cases),
            checkpoint_store=JsonCheckpointStore(tmp_dirs["state"] / "checkpoint.json"),
            lake_writer=JsonlLakeWriter(tmp_dirs["lake"]),
            event_emitter=_emitter,
        )
        return svc, _emitter
    return _factory


@pytest.fixture()
def test_client(
    tmp_dirs: dict[str, Path],
    seed_customers: list[Customer],
    seed_cases: list[Case],
) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with all dependencies wired to fakes."""
    from main import app

    emitter = FakeEventEmitter()
    search_idx = SearchIndex()
    svc = IngestService(
        customer_repo=FakeCustomerRepository(seed_customers),
        case_repo=FakeCaseRepository(seed_cases),
        checkpoint_store=JsonCheckpointStore(tmp_dirs["state"] / "checkpoint.json"),
        lake_writer=JsonlLakeWriter(tmp_dirs["lake"]),
        event_emitter=emitter,
    )

    app.dependency_overrides[get_ingest_service] = lambda: svc
    app.dependency_overrides[get_search_index] = lambda: search_idx

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
