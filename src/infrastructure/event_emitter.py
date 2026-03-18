"""Event emitter — writes structured events to stdout + ./events/events.jsonl.

Each call to emit() appends one JSON line to events.jsonl and also prints to
stdout, satisfying both the streaming-event and persistence requirements.

Atomicity: events.jsonl is append-only so no temp-file dance is needed.
The file is opened in append mode with line buffering so each JSON line is
flushed immediately.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from src.domain.models import IngestEvent
from src.domain.ports import EventEmitter

logger = logging.getLogger(__name__)


class JsonlEventEmitter(EventEmitter):
    def __init__(self, events_path: Path) -> None:
        self._events_path = events_path
        self._events_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: IngestEvent) -> None:
        payload = json.dumps(event.to_dict(), ensure_ascii=False)

        # stdout — so callers / log aggregators can consume the stream
        print(payload, flush=True, file=sys.stdout)

        # Persistent append log
        with self._events_path.open("a", encoding="utf-8") as fh:
            fh.write(payload + "\n")

        logger.info(
            "Emitted event table=%s run_id=%s delta_row_count=%d",
            event.table,
            event.run_id,
            event.delta_row_count,
        )
