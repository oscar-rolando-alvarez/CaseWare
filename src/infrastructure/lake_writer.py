"""JSONL lake writer with atomic file replacement.

Layout:
    ./lake/customers/date=YYYY-MM-DD/data.jsonl
    ./lake/cases/date=YYYY-MM-DD/data.jsonl

Atomicity strategy (required by spec):
    1. All rows for a partition are serialised to an in-memory buffer.
    2. The buffer is written to a sibling temp file in the target directory.
    3. os.replace() atomically swaps the temp file to data.jsonl.
    → Re-running with the same rows produces identical output (idempotent).
    → A crash before os.replace() leaves data.jsonl untouched.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections import defaultdict
from pathlib import Path

from src.domain.models import Case, Customer
from src.domain.ports import LakeWriter

logger = logging.getLogger(__name__)


def _write_partition(partition_path: Path, lines: list[str]) -> str:
    """Write *lines* to *partition_path*/data.jsonl atomically."""
    partition_path.mkdir(parents=True, exist_ok=True)
    target = partition_path / "data.jsonl"

    payload = "\n".join(lines) + "\n" if lines else ""

    fd, tmp = tempfile.mkstemp(dir=partition_path, prefix=".data_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return str(target)


class JsonlLakeWriter(LakeWriter):
    """Writes domain entities as JSONL files partitioned by calendar date."""

    def __init__(self, lake_root: Path) -> None:
        self._lake_root = lake_root

    def write_customers(
        self, customers: list[Customer], run_date: str
    ) -> list[str]:
        return self._write_entities(
            entities=[c.to_dict() for c in customers],
            table="customers",
            run_date=run_date,
        )

    def write_cases(self, cases: list[Case], run_date: str) -> list[str]:
        return self._write_entities(
            entities=[c.to_dict() for c in cases],
            table="cases",
            run_date=run_date,
        )

    def _write_entities(
        self,
        entities: list[dict],
        table: str,
        run_date: str,  # noqa: ARG002 — kept for interface consistency
    ) -> list[str]:
        """Partition entities by their own updated_at date, write each partition."""
        if not entities:
            return []

        # Group by date partition derived from updated_at
        partitions: dict[str, list[str]] = defaultdict(list)
        for entity in entities:
            # updated_at is already an ISO string from .to_dict()
            date_part = entity["updated_at"][:10]  # YYYY-MM-DD
            partitions[date_part].append(json.dumps(entity, ensure_ascii=False))

        written: list[str] = []
        for date_part, lines in sorted(partitions.items()):
            partition_dir = self._lake_root / table / f"date={date_part}"
            path = _write_partition(partition_dir, lines)
            written.append(path)
            logger.debug("Wrote %d rows to %s", len(lines), path)

        return written
