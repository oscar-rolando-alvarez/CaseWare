"""
Test 1 — test_checkpoint_correctness_and_idempotency
    a. Run /ingest dry_run=false → checkpoint advances.
    b. Run again with no DB changes → delta_row_count=0, no new files.
    c. Simulate a failure mid-run (lake write raises) → checkpoint unchanged.

Test 2 — test_search_determinism
    a. Ingest data into index.
    b. POST /search "billing fraud" three times → identical ordered results.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.application.ingest_service import IngestService
from src.application.search_index import SearchIndex
from src.domain.models import Case, Customer
from src.domain.ports import LakeWriter
from src.infrastructure.checkpoint import JsonCheckpointStore, EPOCH

from tests.conftest import (
    FakeCaseRepository,
    FakeCustomerRepository,
    FakeEventEmitter,
    _make_case,
)


# =============================================================================
# Test 1 — Checkpoint correctness and idempotency
# =============================================================================


class TestCheckpointCorrectnessAndIdempotency:

    def test_checkpoint_advances_on_first_run(
        self,
        ingest_service_factory,
        seed_customers: list[Customer],
        seed_cases: list[Case],
        tmp_dirs: dict[str, Path],
    ) -> None:
        """Checkpoint should advance to max(updated_at) after a successful ingest."""
        svc, _ = ingest_service_factory(seed_customers, seed_cases)

        manifest = svc.run(dry_run=False)

        assert manifest.checkpoint_before == EPOCH.isoformat()
        assert manifest.checkpoint_after != EPOCH.isoformat()

        # Checkpoint on disk should match manifest
        store = JsonCheckpointStore(tmp_dirs["state"] / "checkpoint.json")
        saved = store.read()
        assert saved.isoformat() == manifest.checkpoint_after

        # Sanity: delta counts should match seed sizes
        assert manifest.customers.delta_row_count == len(seed_customers)
        assert manifest.cases.delta_row_count == len(seed_cases)

    def test_idempotent_second_run_produces_zero_delta(
        self,
        ingest_service_factory,
        seed_customers: list[Customer],
        seed_cases: list[Case],
    ) -> None:
        """Second run with no DB changes should produce empty deltas."""
        svc, _ = ingest_service_factory(seed_customers, seed_cases)

        first = svc.run(dry_run=False)
        assert first.customers.delta_row_count > 0

        # Same service instance; same repos; checkpoint has advanced
        second = svc.run(dry_run=False)

        assert second.customers.delta_row_count == 0
        assert second.cases.delta_row_count == 0
        assert second.customers.lake_paths == []
        assert second.cases.lake_paths == []
        # Checkpoint should remain the same
        assert second.checkpoint_after == first.checkpoint_after

    def test_no_new_files_written_when_delta_is_empty(
        self,
        ingest_service_factory,
        seed_customers: list[Customer],
        seed_cases: list[Case],
        tmp_dirs: dict[str, Path],
    ) -> None:
        """When delta is empty, no new lake files are created."""
        svc, _ = ingest_service_factory(seed_customers, seed_cases)
        svc.run(dry_run=False)  # first run

        lake_files_before = list(tmp_dirs["lake"].rglob("data.jsonl"))

        svc.run(dry_run=False)  # second run (no new data)

        lake_files_after = list(tmp_dirs["lake"].rglob("data.jsonl"))
        # File *paths* should be identical (no new partitions)
        assert set(str(p) for p in lake_files_after) == set(
            str(p) for p in lake_files_before
        )

    def test_failure_mid_run_leaves_checkpoint_unchanged(
        self,
        seed_customers: list[Customer],
        seed_cases: list[Case],
        tmp_dirs: dict[str, Path],
    ) -> None:
        """If lake write fails, checkpoint must NOT advance."""
        checkpoint_path = tmp_dirs["state"] / "checkpoint.json"
        checkpoint_store = JsonCheckpointStore(checkpoint_path)

        class BrokenLakeWriter(LakeWriter):
            def write_customers(self, customers, run_date):
                raise RuntimeError("Simulated disk failure")

            def write_cases(self, cases, run_date):
                raise RuntimeError("Simulated disk failure")

        svc = IngestService(
            customer_repo=FakeCustomerRepository(seed_customers),
            case_repo=FakeCaseRepository(seed_cases),
            checkpoint_store=checkpoint_store,
            lake_writer=BrokenLakeWriter(),
            event_emitter=FakeEventEmitter(),
        )

        checkpoint_before = checkpoint_store.read()

        with pytest.raises(RuntimeError, match="Simulated disk failure"):
            svc.run(dry_run=False)

        checkpoint_after = checkpoint_store.read()
        assert checkpoint_before == checkpoint_after, (
            "Checkpoint must not advance when a mid-run failure occurs"
        )

    def test_dry_run_does_not_mutate_state(
        self,
        ingest_service_factory,
        seed_customers: list[Customer],
        seed_cases: list[Case],
        tmp_dirs: dict[str, Path],
    ) -> None:
        """dry_run=True must not write lake files, emit events, or advance checkpoint."""
        svc, emitter = ingest_service_factory(seed_customers, seed_cases)

        manifest = svc.run(dry_run=True)

        # No lake files written
        assert not list(tmp_dirs["lake"].rglob("data.jsonl"))
        # No events emitted
        assert emitter.emitted == []
        # Checkpoint unchanged
        assert manifest.checkpoint_before == manifest.checkpoint_after
        # But delta counts should reflect what WOULD have been ingested
        assert manifest.customers.delta_row_count == len(seed_customers)
        assert manifest.cases.delta_row_count == len(seed_cases)


# =============================================================================
# Test 2 — Search determinism
# =============================================================================


class TestSearchDeterminism:

    def _build_index_with_cases(self, cases: list[Case]) -> SearchIndex:
        idx = SearchIndex()
        idx.build(cases)
        return idx

    def _rich_cases(self) -> list[Case]:
        return [
            _make_case(1, 1, 0, "Billing invoice error", "billing payments invoice double charge reconciliation"),
            _make_case(2, 1, 1, "Fraud AML alert", "fraud aml suspicious transaction monitoring flagged"),
            _make_case(3, 2, 2, "Compliance audit report", "compliance audit regulatory gap remediation"),
            _make_case(4, 2, 3, "Onboarding KYC review", "onboarding kyc identity verification documents"),
            _make_case(5, 3, 4, "Payment reconciliation", "payment reconciliation mismatch billing"),
            _make_case(6, 3, 5, "AML fraud crossover", "aml fraud billing compliance reconciliation payments"),
            _make_case(7, 4, 6, "Billing fraud detection", "billing fraud detection reconciliation audit payments"),
            _make_case(8, 4, 7, "Onboarding compliance", "onboarding compliance billing payments verification"),
        ]

    def test_same_query_returns_identical_results_three_times(self) -> None:
        """Querying the same index three times must produce byte-identical results."""
        cases = self._rich_cases()
        idx = self._build_index_with_cases(cases)

        results = [idx.search("billing fraud", top_k=5) for _ in range(3)]

        # All three runs must be identical
        assert results[0] == results[1], "Run 1 and 2 differ"
        assert results[1] == results[2], "Run 2 and 3 differ"

    def test_results_are_ordered_by_score_descending(self) -> None:
        """Result list must be strictly descending (or equal) by score."""
        idx = self._build_index_with_cases(self._rich_cases())
        results = idx.search("billing fraud", top_k=5)

        assert len(results) > 0
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score, (
                f"Score out of order at index {i}: {results[i].score} < {results[i+1].score}"
            )

    def test_determinism_across_fresh_index_instances(self) -> None:
        """Two independently-built indexes on the same data must return the same results."""
        cases = self._rich_cases()

        idx_a = self._build_index_with_cases(cases)
        idx_b = self._build_index_with_cases(cases)

        results_a = idx_a.search("billing fraud", top_k=5)
        results_b = idx_b.search("billing fraud", top_k=5)

        assert results_a == results_b, (
            "Different index instances produced different results for same data+query"
        )

    def test_search_via_http_endpoint_is_deterministic(
        self,
        test_client: TestClient,
    ) -> None:
        """End-to-end: ingest → 3x /search must return identical JSON responses."""
        # Ingest data (this also populates the in-memory cases via FakeRepos)
        ingest_resp = test_client.post("/ingest?dry_run=false")
        assert ingest_resp.status_code == 200

        # Manually seed the search index with known cases.
        # We retrieve it by calling the override lambda stored on the app.
        from fastapi import FastAPI as _FastAPI
        _app: _FastAPI = test_client.app  # type: ignore[assignment]
        from src.presentation.api import get_search_index as _gsi
        search_idx: SearchIndex = _app.dependency_overrides[_gsi]()
        cases = [
            _make_case(1, 1, 0, "Billing invoice error", "billing payments invoice double charge"),
            _make_case(2, 1, 1, "Fraud AML alert", "fraud aml suspicious transaction"),
            _make_case(3, 2, 2, "Compliance audit", "compliance audit regulatory"),
        ]
        search_idx.build(cases)

        responses = [
            test_client.post("/search", json={"query": "billing fraud", "top_k": 5})
            for _ in range(3)
        ]

        assert all(r.status_code == 200 for r in responses)
        bodies = [r.json() for r in responses]
        assert bodies[0] == bodies[1], "HTTP run 1 and 2 differ"
        assert bodies[1] == bodies[2], "HTTP run 2 and 3 differ"

    def test_empty_index_returns_empty_results(self) -> None:
        idx = SearchIndex()
        results = idx.search("billing fraud", top_k=5)
        assert results == []

    def test_unknown_query_returns_empty_results(self) -> None:
        idx = self._build_index_with_cases(self._rich_cases())
        results = idx.search("xyzzy frobnicator", top_k=5)
        assert results == []
