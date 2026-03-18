"""JSON file-based checkpoint store.

The checkpoint is the high-water mark: the maximum updated_at seen in the
previous successful ingest run.  It is stored as an ISO-8601 UTC string so
the file is human-readable.

Atomicity guarantee:
  write() uses os.replace() (atomic on POSIX) — the file is never observed
  in a partially-written state by concurrent readers.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.domain.ports import CheckpointStore

logger = logging.getLogger(__name__)

EPOCH: datetime = datetime(1970, 1, 1, tzinfo=timezone.utc)
_CHECKPOINT_KEY = "checkpoint"


class JsonCheckpointStore(CheckpointStore):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> datetime:
        if not self._path.exists():
            logger.info("No checkpoint found at %s — starting from epoch", self._path)
            return EPOCH

        try:
            data = json.loads(self._path.read_text())
            ts = datetime.fromisoformat(data[_CHECKPOINT_KEY])
            # Ensure timezone-aware
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            logger.info("Read checkpoint: %s", ts.isoformat())
            return ts
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(
                "Corrupt checkpoint file %s (%s) — falling back to epoch",
                self._path,
                exc,
            )
            return EPOCH

    def write(self, ts: datetime) -> None:
        """Persist checkpoint atomically via write-to-temp + os.replace()."""
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        payload = json.dumps({_CHECKPOINT_KEY: ts.isoformat()}, indent=2)

        # Write to a sibling temp file in the same directory so os.replace()
        # is guaranteed to be atomic (same filesystem).
        fd, tmp_path = tempfile.mkstemp(
            dir=self._path.parent, prefix=".checkpoint_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, self._path)
        except Exception:
            # Best-effort cleanup of temp file; do not swallow the real error.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        logger.info("Checkpoint written: %s", ts.isoformat())
