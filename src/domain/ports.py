"""Abstract ports (interfaces) that the application layer depends on.

Concrete adapters live in infrastructure/ and are injected at startup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.models import Case, Customer, IngestEvent


class CustomerRepository(ABC):
    @abstractmethod
    def fetch_since(self, since: datetime) -> list[Customer]:
        """Return all customers with updated_at > since, ordered by updated_at asc."""
        ...


class CaseRepository(ABC):
    @abstractmethod
    def fetch_since(self, since: datetime) -> list[Case]:
        """Return all cases with updated_at > since, ordered by updated_at asc."""
        ...


class CheckpointStore(ABC):
    @abstractmethod
    def read(self) -> datetime:
        """Read current checkpoint; return epoch if missing."""
        ...

    @abstractmethod
    def write(self, ts: datetime) -> None:
        """Persist new checkpoint value."""
        ...


class LakeWriter(ABC):
    @abstractmethod
    def write_customers(
        self, customers: list[Customer], run_date: str
    ) -> list[str]:
        """Write customers to lake; return list of written paths."""
        ...

    @abstractmethod
    def write_cases(self, cases: list[Case], run_date: str) -> list[str]:
        """Write cases to lake; return list of written paths."""
        ...


class EventEmitter(ABC):
    @abstractmethod
    def emit(self, event: IngestEvent) -> None:
        """Emit a single ingest event to stdout and events.jsonl."""
        ...
