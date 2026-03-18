"""Application configuration loaded from environment variables.

All paths are pathlib.Path objects.  Defaults assume you run from the repo root.
"""

from __future__ import annotations

import os
from pathlib import Path


class Settings:
    # PostgreSQL DSN — components can be overridden individually via env vars
    db_dsn: str

    # Filesystem roots
    state_dir: Path
    lake_root: Path
    events_dir: Path

    def __init__(self) -> None:
        self.db_dsn = os.environ.get(
            "DATABASE_URL",
            "postgresql://interop:interop@localhost:5432/interop",
        )
        self.state_dir = Path(os.environ.get("STATE_DIR", "./state"))
        self.lake_root = Path(os.environ.get("LAKE_ROOT", "./lake"))
        self.events_dir = Path(os.environ.get("EVENTS_DIR", "./events"))

    @property
    def checkpoint_path(self) -> Path:
        return self.state_dir / "checkpoint.json"

    @property
    def events_path(self) -> Path:
        return self.events_dir / "events.jsonl"


# Module-level singleton — imported everywhere
settings = Settings()
