---
area: polars
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area polars
status: seed
schema_version: 1.0
applies_to_versions: ">=1.0,<2.0"
---

# Polars — API Knowledge

## Idioms

### [pl-001] LazyFrame for any pipeline >1 step
**Summary:** `pl.scan_csv(...)` / `pl.scan_parquet(...)` returns a LazyFrame; chain operations; call `.collect()` once. The query optimizer fuses scans, predicates, and projections.
**Code:**
```python
df = (pl.scan_parquet("data/*.parquet")
        .filter(pl.col("active") == True)
        .group_by("city").agg(pl.col("price").mean())
        .collect())
```

### [pl-002] `with_columns` over chained `with_column`
**Summary:** `with_columns([...])` adds many columns in one pass. Avoid the deprecated `with_column` (singular).

### [pl-003] Expression API beats apply
**Summary:** `pl.col("x").str.to_lowercase()` is vectorized; `apply(lambda x: x.lower())` is per-row Python. Always prefer expressions.

### [pl-004] `pl.when().then().otherwise()` for conditionals
**Summary:** SQL-CASE-like expression that stays vectorized.

### [pl-005] Streaming engine for >RAM data
**Summary:** `.collect(streaming=True)` enables out-of-core execution for many ops. Not all ops support streaming yet - check the user guide.

### [pl-006] `pl.read_database` and `pl.read_database_uri`
**Summary:** Direct DB ingest via ConnectorX or ADBC. Often 5-10x faster than pandas + SQLAlchemy.

### [pl-007] Polars 1.0+ stable API
**Summary:** Since 1.0 (2024), the API is stable. Pre-1.0 code may use deprecated names like `pl.Utf8` (now `pl.String`).

## Conversions

- `df.to_pandas()` for sklearn / matplotlib interop.
- `df.to_numpy()` for fast array handoff to torch / xgboost.
- `pl.from_pandas(pdf)` to migrate.

## Pitfalls

- Polars Series and DataFrames are NOT mutable - operations return new objects.
- `pl.col("x").null_count()` returns an expression, not a value - need `.collect()` or call on a Series.
- Mixing `pl.col` and `pl.lit` in arithmetic - explicit `pl.lit` is sometimes required.
- `group_by` (Polars) vs `groupby` (Pandas) - different name.

## Key sources

- https://docs.pola.rs/
- https://github.com/pola-rs/polars/releases
