# Review Checklist

## Contract Compliance

- [x] **Schema matches contract exactly** — `customers` and `cases` tables use `BIGINT GENERATED ALWAYS AS IDENTITY`, correct column names/types, `UNIQUE` on `email`, `CHECK (status IN ('open','in_progress','closed'))`, and all three required indexes (`customers(updated_at)`, `cases(updated_at)`, `cases(customer_id)`)
- [x] **Seed data volume** — 30 customers, 210 cases in `init.sql` (customers 1–10: 7 cases each; customers 11–30: 7 cases each); `changes.sql` adds 2 customers + 10 cases, updates 5 cases
- [x] **Diverse keywords present** — billing, audit, compliance, payments, reconciliation, onboarding, fraud, AML all appear in case titles and descriptions
- [x] **updated_at spans last 30 days** — seed uses `NOW() - INTERVAL 'N days'` for N = 1..30

## Ingest Behaviour

- [x] **Incremental fetch** — `WHERE updated_at > %s` (strict greater-than) using checkpoint as parameter
- [x] **Checkpoint atomicity implemented** — `os.replace()` after `fsync`; checkpoint write is the last step after lake writes succeed
- [x] **dry_run does not mutate state** — lake writes, event emission, and checkpoint advance are all gated on `if not dry_run:`; `manifest.checkpoint_after == manifest.checkpoint_before` in dry_run mode
- [x] **No duplicates on re-run** — lake writer overwrites partition files (does not append); idempotent by design
- [x] **Atomic lake writes** — `tempfile.mkstemp()` + `os.replace()` per partition in `lake_writer.py`
- [x] **Events emitted** — one JSON line per table to stdout and `./events/events.jsonl`
- [x] **Manifest structure** — `run_id`, `started_at`, `finished_at`, per-table `delta_row_count` / `lake_paths` / `schema_fingerprint`, `checkpoint_before`, `checkpoint_after`, `dry_run`
- [x] **schema_fingerprint** — SHA-256 of sorted `col:type` pairs

## Search

- [x] **Search is deterministic across runs** — SHA-256 token hashing (not `hash()`), explicit tie-breaking by `case_id` ascending; same query + same data = same ordered results
- [x] **TF-IDF-like scoring** — hash-trick TF with smoothed IDF (`log(1 + N/(1+df))`), cosine similarity
- [x] **Index rebuilt after ingest** — `load_from_lake()` called on startup and after each non-empty ingest
- [x] **top_k validated** — 422 if `top_k < 1` or `top_k > 100`; empty query returns 422

## Code Quality

- [x] **Type hints throughout** — all function signatures, return types, and variable annotations; `from __future__ import annotations` in all modules
- [x] **No hardcoded paths** — all paths via `pathlib.Path`; roots configurable via environment variables
- [x] **All config via env vars** — `DATABASE_URL`, `STATE_DIR`, `LAKE_ROOT`, `EVENTS_DIR` with sensible defaults in `src/config.py`
- [x] **Structured logging** — `logging.basicConfig` with timestamp + level; per-module loggers
- [x] **No bare `except`** — all exception handlers name the exception type
- [x] **Clean Architecture** — `domain/` (models, ports), `application/` (services), `infrastructure/` (adapters), `presentation/` (API); outer layers depend on inner, never reverse

## Tests

- [x] **All required tests present** — `test_checkpoint_correctness_and_idempotency` (5 sub-cases) and `test_search_determinism` (6 sub-cases)
- [x] **Tests pass** — `11 passed` with no live database dependency
- [x] **Failure simulation test** — `BrokenLakeWriter` raises mid-run; asserts checkpoint unchanged on disk

## Files Present

- [x] `docker-compose.yml`
- [x] `db/init.sql`
- [x] `db/changes.sql`
- [x] `src/domain/models.py`
- [x] `src/domain/ports.py`
- [x] `src/application/ingest_service.py`
- [x] `src/application/search_index.py`
- [x] `src/infrastructure/checkpoint.py`
- [x] `src/infrastructure/database.py`
- [x] `src/infrastructure/lake_writer.py`
- [x] `src/infrastructure/event_emitter.py`
- [x] `src/presentation/api.py`
- [x] `src/config.py`
- [x] `main.py`
- [x] `tests/conftest.py`
- [x] `tests/test_ingest.py`
- [x] `pyproject.toml`
- [x] `README.md`
- [x] `AI_USAGE.md`
- [x] `ARCHITECTURE_AWS.md`
- [x] `EXECUTION_PLAN.md`
- [x] `REVIEW_CHECKLIST.md`
