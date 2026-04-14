---
area: data-engineer
category: role
track: common
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area data-engineer
status: seed
schema_version: 1.0
---

# Data Engineer — Pipeline and Quality Knowledge

## Core principles

### [de-001] Schema is the contract
**Summary:** Validate every input file against an explicit schema (`pandera`, `great_expectations`, `pydantic`). A schema mismatch should HARD STOP, not silently coerce.

### [de-002] Idempotency
**Summary:** Re-running a pipeline must produce the same output. No `INSERT INTO ... VALUES (NOW())`, no append-without-key. Use upserts keyed on natural identifiers.

### [de-003] Partition by ingestion date
**Summary:** Storage layout `dataset/year=2026/month=04/day=14/file.parquet`. Enables incremental processing, time-travel debugging, GDPR deletion by date range.

### [de-004] Format choice
**Summary:** Parquet > CSV always for analytics (10x smaller, 100x faster scan, schema preserved). Delta Lake / Iceberg / Hudi when you need ACID. CSV only for human handoff.

### [de-005] Polars over Pandas for >1GB
**Summary:** Polars is 5-30x faster, uses lazy evaluation, has streaming for larger-than-RAM. Pandas is fine for <1GB and Jupyter exploration. DuckDB for SQL-style aggregations on Parquet.

### [de-006] Data quality dimensions
**Summary:** Completeness (% missing), validity (passes schema), uniqueness (no dup keys), consistency (cross-field rules), timeliness (freshness SLA), accuracy (vs source of truth). Test all six.

### [de-007] Lineage tracking
**Summary:** Every output row should be traceable to its inputs. OpenLineage, Marquez, or simply embedding `_source_file` and `_ingest_ts` columns.

## Pitfalls

- Silent type coercion: pandas turns "0001234" zip codes into integers, drops the leading zeros.
- Datetime timezones: mixing naive and aware timestamps. Always store UTC, convert at display.
- Schema drift: a new column appears upstream and downstream code crashes weeks later.
- Tiny-file problem: many small Parquet files kill query performance. Compact periodically.
- Re-reading the same file in every step instead of caching the dataframe.

## Tools to know

- **Validation**: pandera, great_expectations, soda-core, dbt tests.
- **Orchestration**: Airflow, Prefect, Dagster, Mage.
- **Storage**: Parquet, Delta Lake, Iceberg, Hudi, DuckDB.
- **Streaming**: Kafka, Pulsar, Kinesis, Redpanda, Flink.
- **Compute**: Polars, DuckDB, Spark (only for >100GB), Dask, Ray Data.

## Key sources

- "Fundamentals of Data Engineering" (Reis & Housley)
- "Designing Data-Intensive Applications" (Kleppmann)
- Polars and DuckDB docs
- dbt and Dagster blogs
