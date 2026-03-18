# Execution Plan

## 6-Phase Build Timeline

| Phase | What was built | Output |
|-------|---------------|--------|
| **1 — Schema & Seed** | `docker-compose.yml`, `db/init.sql` (schema + 30 customers + 210 cases), `db/changes.sql` | Runnable Postgres with realistic data |
| **2 — Domain Layer** | `src/domain/models.py` (Pydantic v2 entities + manifest types), `src/domain/ports.py` (abstract interfaces), `src/config.py` | Pure Python, zero external deps, fully typed |
| **3 — Infrastructure Adapters** | `checkpoint.py` (atomic JSON file), `database.py` (psycopg2 repos), `lake_writer.py` (JSONL + `os.replace()`), `event_emitter.py` (stdout + append log) | Each adapter independently testable |
| **4 — Application Services** | `ingest_service.py` (incremental orchestration + atomicity contract), `search_index.py` (SHA-256 hash-trick TF-IDF, cosine similarity, deterministic tie-breaking) | Core business logic, no FastAPI dependency |
| **5 — API + Wiring** | `src/presentation/api.py` (FastAPI router, dependency stubs), `main.py` (lifespan, dependency injection, singleton wiring) | Runnable service |
| **6 — Tests & Docs** | `tests/conftest.py` (in-memory fakes, fixtures), `tests/test_ingest.py` (11 test cases), all `.md` documentation files | 11/11 green, no live DB required |

---

## Risks Identified and Mitigated

| Risk | Mitigation |
|------|-----------|
| **Checkpoint written before lake flush** | Atomicity: checkpoint write is the *last* step; any exception in lake write leaves checkpoint unchanged |
| **Partial lake write visible to readers** | `tempfile.mkstemp()` + `os.replace()` per partition — readers see either the old file or the complete new file, never a partial write |
| **Search non-determinism across runs** | SHA-256 (not Python's `hash()` which is PYTHONHASHSEED-randomised) for token hashing; stable `sorted()` for scoring; explicit tie-break by `case_id asc` |
| **Duplicate rows on re-ingest** | Lake writer *overwrites* the partition file each run (idempotent); no append mode |
| **dry_run leaking state** | All three mutation paths (lake write, event emit, checkpoint write) are gated on `if not dry_run:`; tests verify each independently |
| **Seed data determinism** | `init.sql` uses `NOW() - INTERVAL 'N days'` so rows are always relative to current time; `changes.sql` uses `NOW()` to guarantee rows are always ahead of the seed checkpoint |

---

## Time Spent — AI vs Manual

| Activity | AI-generated | Manual review / correction |
|----------|-------------|---------------------------|
| Schema + seed SQL | 90% | 10% — counted rows, verified column types and CHECK constraint |
| Domain models + ports | 95% | 5% — confirmed Pydantic v2 `ConfigDict(frozen=True)` usage |
| Infrastructure adapters | 85% | 15% — traced `os.replace()` atomicity, verified `fsync` before rename |
| Ingest service + atomicity | 80% | 20% — caught dry_run checkpoint_after bug, verified ordering of steps |
| Search index | 90% | 10% — confirmed SHA-256 determinism, verified tie-breaking logic |
| FastAPI wiring | 85% | 15% — updated deprecated `on_event` to `lifespan` handler |
| Tests | 75% | 25% — added failure-injection test, fixed unused fixture parameters |
| Documentation | 70% | 30% — verified technical accuracy of AWS service choices and cost estimates |

**Overall**: ~85% AI-generated, ~15% manual verification and correction.
