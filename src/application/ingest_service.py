"""Ingest service — orchestrates incremental ingestion from DB to lake.

Atomicity contract (dry_run=False):
    1. Fetch delta rows from DB.
    2. Write all lake files atomically (each via temp + os.replace).
    3. Emit events.
    4. Write checkpoint.

    If step 2 or 3 raises, step 4 never executes → checkpoint unchanged.
    On retry the same delta is re-fetched and files are overwritten (idempotent).

dry_run=True:
    Only steps 1 is executed (read-only).  Nothing is written.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from src.domain.models import (
    CASES_FINGERPRINT,
    CUSTOMERS_FINGERPRINT,
    Case,
    Customer,
    IngestEvent,
    IngestManifest,
    TableManifest,
)
from src.domain.ports import (
    CaseRepository,
    CheckpointStore,
    CustomerRepository,
    EventEmitter,
    LakeWriter,
)

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        case_repo: CaseRepository,
        checkpoint_store: CheckpointStore,
        lake_writer: LakeWriter,
        event_emitter: EventEmitter,
    ) -> None:
        self._customers = customer_repo
        self._cases = case_repo
        self._checkpoint = checkpoint_store
        self._lake = lake_writer
        self._emitter = event_emitter

    def run(self, dry_run: bool = False) -> IngestManifest:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(tz=timezone.utc)
        run_date = started_at.strftime("%Y-%m-%d")

        # ── 1. Read checkpoint ─────────────────────────────────────────────
        checkpoint_before = self._checkpoint.read()
        logger.info(
            "Ingest run=%s dry_run=%s checkpoint_before=%s",
            run_id,
            dry_run,
            checkpoint_before.isoformat(),
        )

        # ── 2. Fetch delta ─────────────────────────────────────────────────
        new_customers: list[Customer] = self._customers.fetch_since(checkpoint_before)
        new_cases: list[Case] = self._cases.fetch_since(checkpoint_before)

        # Compute new high-water mark = max updated_at across both tables
        all_timestamps: list[datetime] = [
            r.updated_at for r in new_customers
        ] + [r.updated_at for r in new_cases]

        new_high_water = (
            max(all_timestamps) if all_timestamps else checkpoint_before
        )

        # In dry_run mode the checkpoint never advances — report it as unchanged
        checkpoint_after = checkpoint_before if dry_run else new_high_water

        customer_paths: list[str] = []
        case_paths: list[str] = []

        if not dry_run:
            # ── 3. Write lake (atomic per partition) ──────────────────────
            if new_customers:
                customer_paths = self._lake.write_customers(new_customers, run_date)
            if new_cases:
                case_paths = self._lake.write_cases(new_cases, run_date)

            # ── 4. Emit events (once per table) ───────────────────────────
            if new_customers:
                self._emitter.emit(
                    IngestEvent(
                        table="customers",
                        run_id=run_id,
                        schema_fingerprint=CUSTOMERS_FINGERPRINT,
                        delta_row_count=len(new_customers),
                        lake_paths=customer_paths,
                        checkpoint_after=new_high_water.isoformat(),
                    )
                )
            if new_cases:
                self._emitter.emit(
                    IngestEvent(
                        table="cases",
                        run_id=run_id,
                        schema_fingerprint=CASES_FINGERPRINT,
                        delta_row_count=len(new_cases),
                        lake_paths=case_paths,
                        checkpoint_after=new_high_water.isoformat(),
                    )
                )

            # ── 5. Advance checkpoint (only after successful lake writes) ──
            if new_high_water != checkpoint_before:
                self._checkpoint.write(new_high_water)

        finished_at = datetime.now(tz=timezone.utc)

        manifest = IngestManifest(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            customers=TableManifest(
                delta_row_count=len(new_customers),
                lake_paths=customer_paths,
                schema_fingerprint=CUSTOMERS_FINGERPRINT,
            ),
            cases=TableManifest(
                delta_row_count=len(new_cases),
                lake_paths=case_paths,
                schema_fingerprint=CASES_FINGERPRINT,
            ),
            checkpoint_before=checkpoint_before.isoformat(),
            checkpoint_after=checkpoint_after.isoformat(),
            dry_run=dry_run,
        )

        logger.info(
            "Ingest complete run=%s customers=%d cases=%d checkpoint_after=%s",
            run_id,
            len(new_customers),
            len(new_cases),
            checkpoint_after.isoformat(),
        )
        return manifest
