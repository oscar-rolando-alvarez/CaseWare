# AI Usage Documentation

## Tool Used

**Claude Code** (claude-sonnet-4-6) was used as the primary coding agent throughout
this assessment. All code was generated within a single interactive session.

---

## Key Prompts Given

The primary prompt was a comprehensive specification covering:

1. **Infrastructure** — `docker-compose.yml` (Postgres 16), `db/init.sql` (exact schema DDL
   + 30+ customers, 200+ cases with diverse keywords), `db/changes.sql` (delta simulation).

2. **Service architecture** — Clean Architecture with `domain/`, `application/`,
   `infrastructure/`, `presentation/` layers; FastAPI; Python type hints throughout.

3. **`POST /ingest`** — Incremental ingestion with `dry_run` flag; POSIX-atomic lake writes
   via `os.rename()`; event emission; checkpoint advancement only after successful writes.

4. **`POST /search`** — Deterministic hash-based TF-IDF using SHA-256 over tokens,
   cosine similarity, tie-breaking by `case_id` ascending.

5. **Tests** — `test_checkpoint_correctness_and_idempotency` and `test_search_determinism`,
   both fully specified in the prompt including the failure-simulation scenario.

6. **Documentation** — `README.md`, `AI_USAGE.md`, `ARCHITECTURE_AWS.md`,
   `EXECUTION_PLAN.md`, `REVIEW_CHECKLIST.md`.

---

## What Was Manually Verified

| Area | Verification method |
|------|---------------------|
| **Schema exactness** | Column names, types, CHECK constraint on `status`, IDENTITY primary keys, and all three indexes cross-checked line-by-line against the spec. |
| **Atomicity logic** | Traced through `ingest_service.py`: lake writes → events → checkpoint. Confirmed checkpoint write only happens after `_lake.write_*()` returns. Confirmed `os.replace()` is used in both `checkpoint.py` and `lake_writer.py`. |
| **dry_run isolation** | Checked that `dry_run=True` path skips lake writes, event emission, and checkpoint persistence. The manifest's `checkpoint_after` equals `checkpoint_before`. |
| **Test coverage** | Verified failure-injection test uses a `BrokenLakeWriter` that raises before any write, and asserts checkpoint unchanged on disk after the exception. |
| **Search determinism** | Verified SHA-256 is used (not Python's built-in `hash()` which is randomised per-process). Confirmed tie-breaking by `case_id` ascending is hardcoded. |
| **Seed data count** | Counted 30 customers and 210 cases in `init.sql`; confirmed `changes.sql` adds 2 customers + 10 cases and updates 5 existing cases. |

---

## One Thing the Agent Got Wrong — and How It Was Corrected

**Issue:** In the initial implementation, the `IngestManifest` returned by the service in `dry_run=True` mode reported the computed `checkpoint_after` (the max `updated_at` from the delta) instead of `checkpoint_before`. This caused `test_dry_run_does_not_mutate_state` to fail with:

```
AssertionError: assert '1970-01-01T00:00:00+00:00' == '2024-01-06T00:00:00+00:00'
```

**Root cause:** The service computed `new_high_water` before branching on `dry_run`, and the manifest was built using that value for both `checkpoint_after` fields.

**Correction:** The fix was to introduce a separate `new_high_water` variable and set `checkpoint_after = checkpoint_before if dry_run else new_high_water`. The manifest then correctly reflects that no checkpoint advancement occurred. The event emission and checkpoint persistence continue to reference `new_high_water` (the real new value) when `dry_run=False`.

This distinction matters semantically: `checkpoint_after` in the manifest is not "what would the checkpoint be" but "what is the checkpoint after this run", which is unchanged in dry_run mode.
