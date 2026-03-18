"""PostgreSQL repository implementations using psycopg2."""

from __future__ import annotations

import logging
from datetime import datetime

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from src.domain.models import Case, Customer
from src.domain.ports import CaseRepository, CustomerRepository

logger = logging.getLogger(__name__)


def make_connection(dsn: str) -> PgConnection:
    """Open and return a psycopg2 connection with autocommit disabled."""
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    return conn


class PostgresCustomerRepository(CustomerRepository):
    """Fetches customers from PostgreSQL."""

    def __init__(self, conn: PgConnection) -> None:
        self._conn = conn

    def fetch_since(self, since: datetime) -> list[Customer]:
        sql = """
            SELECT customer_id, name, email, country, updated_at
            FROM   customers
            WHERE  updated_at > %s
            ORDER  BY updated_at ASC
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, (since,))
            rows = cur.fetchall()

        customers = [Customer(**dict(row)) for row in rows]
        logger.debug("Fetched %d customers since %s", len(customers), since.isoformat())
        return customers


class PostgresCaseRepository(CaseRepository):
    """Fetches cases from PostgreSQL."""

    def __init__(self, conn: PgConnection) -> None:
        self._conn = conn

    def fetch_since(self, since: datetime) -> list[Case]:
        sql = """
            SELECT case_id, customer_id, title, description, status, updated_at
            FROM   cases
            WHERE  updated_at > %s
            ORDER  BY updated_at ASC
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, (since,))
            rows = cur.fetchall()

        cases = [Case(**dict(row)) for row in rows]
        logger.debug("Fetched %d cases since %s", len(cases), since.isoformat())
        return cases
