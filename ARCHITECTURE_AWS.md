# Production Architecture — AWS (5,000 Tenants, 50M Customers, 200M Cases)

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SOURCE                                                                  │
│  Aurora PostgreSQL (Multi-AZ, r6g.2xlarge)                              │
│  ├─ customers table  (500 writes/s peak)                                 │
│  └─ cases table      (5,000 writes/s peak)                               │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ Logical Replication / CDC
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  INGEST TIER (ECS Fargate, per-tenant shard pool)                        │
│                                                                          │
│  ┌──────────────┐   Redis ZADD   ┌──────────────────────┐               │
│  │ Checkpoint   │◄──────────────►│ ElastiCache Redis    │               │
│  │ Workers      │  distributed   │ (checkpoint store +  │               │
│  │ (1 per shard)│  lock per      │  distributed lock)   │               │
│  └──────┬───────┘  tenant-table  └──────────────────────┘               │
│         │                                                                │
│         │ write JSONL                                                    │
│         ▼                                                                │
│  ┌──────────────────────────────────────────────────────┐               │
│  │  Amazon S3  (lake, versioned + lifecycle)             │               │
│  │  s3://lake/tenantId={t}/customers/date=YYYY-MM-DD/   │               │
│  │  s3://lake/tenantId={t}/cases/date=YYYY-MM-DD/       │               │
│  └──────────────┬───────────────────────────────────────┘               │
└─────────────────┼───────────────────────────────────────────────────────┘
                  │ S3 Event Notification
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  EVENT FAN-OUT                                                           │
│  EventBridge (custom bus, per-tenant rules)                              │
│  └──► SQS FIFO queues (one per tenant, deduplication window 5 min)      │
│       └──► Lambda consumers (index updater, downstream integrations)    │
└─────────────────────────────────────────────────────────────────────────┘
                  │
                  │ index documents
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SEARCH TIER                                                             │
│  OpenSearch Serverless (vector + keyword, per-tenant index prefix)       │
│                                                                          │
│  API Gateway (Regional) → Lambda (search handler, 3008 MB)              │
│    ├─ Provisioned Concurrency: 50 (handles 300 QPS baseline)            │
│    └─ Auto-scaling to 1,000 QPS burst; p95 < 300 ms, p99 < 800 ms       │
└─────────────────────────────────────────────────────────────────────────┘
                  │
                  │ query/audit
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ANALYTICAL LAYER                                                        │
│  AWS Glue Catalog + Athena (ad-hoc SQL over S3 lake)                    │
│  AWS Glue ETL jobs (daily compaction: small JSONL → Parquet)            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AWS Service Choices with Rationale

| Service | Role | Rationale |
|---------|------|-----------|
| **Aurora PostgreSQL** (Multi-AZ) | Source of truth | Native logical replication; compatible with DMS; automated failover for 99.99% SLA |
| **ECS Fargate** (ingest workers) | Incremental ingest | Serverless containers; scale out by shard count; no EC2 patching overhead |
| **ElastiCache Redis** (Cluster Mode) | Checkpoint + distributed lock | Sub-millisecond reads; `SET NX PX` for exactly-once ingest per tenant-table pair; Sorted Set for per-table high-water marks |
| **S3** (versioned, Intelligent-Tiering) | Data lake | Effectively zero data loss (11 nines); multipart PUT is atomic from client perspective; lifecycle rules age to Glacier |
| **EventBridge** custom bus | Event routing | Rule-based fan-out to per-tenant SQS; schema registry for contract enforcement |
| **SQS FIFO** | Ordered per-tenant delivery | Exactly-once delivery within dedup window; prevents race conditions on index writes |
| **OpenSearch Serverless** | Search index | Scales to zero; no cluster management; supports BM25 (keyword) + k-NN (embedding) in same index |
| **API Gateway + Lambda** | Search API | Auto-scales to 1,000 QPS burst without pre-provisioning; Provisioned Concurrency eliminates cold starts |
| **Glue + Athena** | Analytics | Serverless SQL over S3; no separate warehouse needed at this scale |

---

## Top 3 Cost Drivers and Mitigations

1. **S3 PUT/GET at volume** (~5,000 ingest writes/s × 5 KB avg = 25 MB/s):
   - *Mitigation*: Micro-batch within ingest workers (buffer 1–5 s, write one S3 object per partition). Reduces PUTs 5–50×. Use S3 Intelligent-Tiering to move cold partitions to cheaper tiers automatically.

2. **OpenSearch Serverless indexing compute** (5 OCUs minimum, ~$700/month per collection):
   - *Mitigation*: One collection shared across all tenants with index aliases `cases-{tenantId}`. Bulk index API with 500-document batches. Async Lambda consumer decouples write rate from index throughput.

3. **Fargate task count at peak** (5,000 tasks × $0.04/vCPU-hour):
   - *Mitigation*: Shard workers so each Fargate task handles N tenants. Use Spot capacity for non-critical background ingestion (p99 latency tolerant). Scale in aggressively during off-peak via Application Auto Scaling.

---

## Tradeoffs

- **DMS vs custom ingest workers**: DMS is simpler to bootstrap and handles schema changes gracefully, but charges per GB replicated and is opaque when debugging lag. Custom Fargate workers with `pg_logical` give full control over checkpointing, retry logic, and dead-letter handling — preferred at 5,000 tenants where per-tenant isolation matters.

- **OpenSearch vs pgvector for search**: `pgvector` keeps search co-located with the source, eliminating index sync complexity, but adds CPU pressure to Aurora and cannot scale search independently. OpenSearch Serverless scales search horizontally without affecting DB performance — the right choice at 300–1,000 QPS.

- **Checkpoint in Redis vs DynamoDB**: Redis is faster (< 1 ms vs 5–10 ms) and supports distributed locks natively. DynamoDB is more durable (11 nines) and cheaper at low call rates. We chose Redis because the lock acquisition latency directly affects ingest throughput at peak. RPO is mitigated by the S3 lake: even if Redis is lost, re-scanning S3 manifests reconstructs the checkpoint.

- **Multi-tenant isolation — shared vs siloed index**: A shared OpenSearch collection with tenant-prefixed indices is 10× cheaper than one collection per tenant, but a noisy tenant can saturate OCUs. Mitigation: per-tenant index quotas enforced via resource policies; escalate to siloed collection for Tier-1 tenants exceeding 10% of total QPS.

- **Freshness SLA (10 min p95)**: The async fan-out (S3 → EventBridge → SQS → Lambda → OpenSearch) introduces ~30–90 s lag. To hit the 10-minute SLA with margin: set ingest worker cycle to 60 s, SQS visibility timeout to 120 s, and Lambda concurrency reservation to 200. Monitor end-to-end lag with a CloudWatch metric `IndexFreshnessSeconds` alarming at 8 min.
