# Data Interop Service

Incremental ingestion from PostgreSQL to a JSONL data lake, event emission, and deterministic hash-based TF-IDF search — built with **FastAPI + Python 3.11+**.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker & Docker Compose | 24+ |
| Python | 3.11+ |
| pip / uv | any recent |

---

## Setup (< 5 minutes)

### 1. Start Postgres

```bash
docker compose up -d
# Wait until healthy:
docker compose ps   # Status should show "healthy"
```

### 2. Install Python dependencies

```bash
# Using a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
# Or with uv:
# uv pip install -e ".[dev]"
```

### 3. Start the service

```bash
uvicorn main:app --reload
# Service available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Run Tests

```bash
pytest -v
```

Expected: **11 passed** in < 1 second (no DB required — all tests use in-memory fakes).

---

## Example curl Commands

### Dry-run ingest (read-only, no state changes)

```bash
curl -s -X POST "http://localhost:8000/ingest?dry_run=true" | jq .
```

### Full ingest (writes lake files, emits events, advances checkpoint)

```bash
curl -s -X POST "http://localhost:8000/ingest?dry_run=false" | jq .
```

Sample response:
```json
{
  "run_id": "a1b2c3d4-...",
  "started_at": "2024-03-17T10:00:00Z",
  "finished_at": "2024-03-17T10:00:00.045Z",
  "customers": {
    "delta_row_count": 30,
    "lake_paths": ["lake/customers/date=2024-02-16/data.jsonl", "..."],
    "schema_fingerprint": "9f3a..."
  },
  "cases": {
    "delta_row_count": 210,
    "lake_paths": ["lake/cases/date=2024-02-16/data.jsonl", "..."],
    "schema_fingerprint": "4d8b..."
  },
  "checkpoint_before": "1970-01-01T00:00:00+00:00",
  "checkpoint_after": "2024-03-17T10:00:00+00:00",
  "dry_run": false
}
```

### Apply incremental changes

```bash
# Apply changes.sql to the running Postgres
docker exec -i interop_postgres psql -U interop -d interop < db/changes.sql

# Then ingest the delta
curl -s -X POST "http://localhost:8000/ingest?dry_run=false" | jq .
# customers.delta_row_count = 2, cases.delta_row_count = 15
```

### Search

```bash
curl -s -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "billing fraud", "top_k": 5}' | jq .
```

Sample response:
```json
[
  {"case_id": 7, "score": 0.42831209, "title": "Billing fraud ring", "status": "open"},
  {"case_id": 55, "score": 0.38104421, "title": "Billing fraud detection", "status": "open"},
  ...
]
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://interop:interop@localhost:5432/interop` | Postgres DSN |
| `STATE_DIR` | `./state` | Directory for checkpoint.json |
| `LAKE_ROOT` | `./lake` | Root of the JSONL data lake |
| `EVENTS_DIR` | `./events` | Directory for events.jsonl |

---

## Architecture

The service is organized following a Clean Architecture layout: `domain` is a pure data + ports layer, `application` holds use cases (`IngestService`, `SearchIndex`), `infrastructure` implements adapters (Postgres reader, JSONL lake writer, event emitter, checkpoint store) and `presentation` exposes the FastAPI routes.

### Layer and module map

```mermaid
flowchart TD
    subgraph Presentation [src/presentation]
        API[api.py<br/>FastAPI routes<br/>POST /ingest, POST /search]
    end
    subgraph Application [src/application]
        Ingest[ingest_service.py<br/>IngestService]
        Search[search_index.py<br/>hash TF-IDF]
    end
    subgraph Domain [src/domain]
        Models[models.py<br/>Customer, Case, IngestManifest,<br/>IngestEvent, SearchRequest/Result]
        Ports[ports.py<br/>abstract interfaces]
    end
    subgraph Infrastructure [src/infrastructure]
        DB[database.py<br/>psycopg2 reader]
        LW[lake_writer.py<br/>JSONL partitions]
        EE[event_emitter.py<br/>events.jsonl]
        CP[checkpoint.py<br/>state/checkpoint.json]
    end
    API --> Ingest
    API --> Search
    Ingest --> Ports
    Search --> Ports
    Ingest --> Models
    Search --> Models
    DB -.implements.-> Ports
    LW -.implements.-> Ports
    EE -.implements.-> Ports
    CP -.implements.-> Ports
    DB --> PG[(PostgreSQL<br/>customers, cases)]
    LW --> Lake[(lake/&lt;table&gt;/date=YYYY-MM-DD/data.jsonl)]
    EE --> Evts[(events/events.jsonl)]
    CP --> State[(state/checkpoint.json)]
```

### Incremental ingest lifecycle

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI /ingest
    participant Svc as IngestService
    participant CP as CheckpointStore
    participant DB as PostgresReader
    participant LW as LakeWriter
    participant EE as EventEmitter
    participant SI as SearchIndex

    Client->>API: POST /ingest?dry_run=false
    API->>Svc: run(dry_run=False)
    Svc->>CP: load() -> checkpoint_before
    Svc->>DB: read customers WHERE updated_at > checkpoint
    DB-->>Svc: delta rows
    Svc->>DB: read cases WHERE updated_at > checkpoint
    DB-->>Svc: delta rows
    alt not dry run
        Svc->>LW: write partitions per date (os.replace atomic)
        Svc->>EE: append IngestEvent per table
        Svc->>CP: save(new checkpoint = max updated_at)
        Svc->>SI: rebuild from lake
    end
    Svc-->>API: IngestManifest (run_id, delta counts, fingerprints)
    API-->>Client: 200 OK + manifest
```

### Search path (hash-trick TF-IDF)

```mermaid
flowchart LR
    Lake[(lake/cases/**/*.jsonl)] --> Build[SearchIndex.build]
    Build --> Tokens[tokenize + SHA-256 hash buckets]
    Tokens --> IDF[IDF weights]
    Query[POST /search query] --> Qtok[tokenize query]
    Qtok --> Score[cosine against cases]
    IDF --> Score
    Score --> Top[top_k SearchResult<br/>case_id, score, title, status]
```

## Key Assumptions

1. **Checkpoint semantics**: The checkpoint stores `max(updated_at)` across both tables seen in the last successful run. A row is "new" if `updated_at > checkpoint`. This means rows updated at the exact checkpoint timestamp are not re-ingested (strict `>`).

2. **Lake partitioning**: Files are partitioned by each row's own `updated_at` date (not the run date). Re-running overwrites the partition file — no duplicate rows accumulate.

3. **Search index**: Built from lake files on startup and rebuilt after every non-empty ingest. The index holds all cases ever ingested (not just the delta). The hash-trick TF-IDF uses SHA-256 for cross-platform determinism.

4. **Atomicity**: `os.replace()` (POSIX rename) is used for both checkpoint and lake partition writes. This is atomic on Linux/macOS. On Windows NTFS it is also atomic since Python 3.3+.

5. **No deduplication across lake partitions**: Each partition file contains only rows whose `updated_at` falls in that date. If a row is updated on a different day in a later run, it will appear in the new partition (the old partition keeps the old version). The search index always uses the latest ingest state.
