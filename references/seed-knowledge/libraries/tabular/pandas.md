---
area: pandas
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area pandas
status: seed
schema_version: 1.0
applies_to_versions: ">=2.0,<3.0"
---

# pandas — API Knowledge

## Important changes in 2.x

### [pd-001] PyArrow backend
**Summary:** `pd.read_csv(..., dtype_backend="pyarrow")` uses Arrow strings, ints, etc. 5-10x lower memory, faster string ops, native nullable types.

### [pd-002] Copy-on-Write becoming default
**Summary:** Pandas 3.0 will make CoW the default. Set `pd.options.mode.copy_on_write = True` now to surface chained-assignment bugs early.

### [pd-003] `pd.NA` over `np.nan` for nullable types
**Summary:** Use `Int64` (capital I), `boolean`, `string` dtypes for true nullable semantics. `np.nan` is a float and silently upcasts integer columns.

### [pd-004] `df.assign(**kwargs)` over chained assignment
**Summary:** `df["new"] = ...` triggers SettingWithCopyWarning in many cases. `df.assign(new=...)` is chain-friendly and CoW-safe.

### [pd-005] `read_csv` performance flags
**Summary:** `engine="pyarrow"`, `dtype_backend="pyarrow"`, `low_memory=False`. For >1GB CSVs, switch to Polars or DuckDB instead.

### [pd-006] `pd.concat` over `df.append`
**Summary:** `DataFrame.append` was removed in 2.0. Use `pd.concat([df1, df2], ignore_index=True)`.

### [pd-007] `query` and `eval` for big filters
**Summary:** `df.query("age > 30 and city == 'NY'")` is faster and clearer than boolean masks for non-trivial conditions.

## Pitfalls

- `inplace=True` is deprecated/discouraged - it doesn't save memory and breaks chaining.
- Datetime parse failures default to `object` dtype - always check dtypes after `read_csv`.
- `groupby(...).apply(func)` is slow if `func` returns a DataFrame; use `.agg`/`.transform` when possible.
- Iterating with `iterrows` is the slowest possible pattern - vectorize.
- Index alignment surprises in arithmetic between Series with mismatched indices.

## When to leave pandas

- Files >1GB or row counts >5M -> Polars or DuckDB.
- Out-of-core or distributed -> Dask, Modin, Spark.
- Pure SQL aggregation on Parquet -> DuckDB.

## Key sources

- https://pandas.pydata.org/docs/whatsnew/
- https://pandas.pydata.org/docs/user_guide/copy_on_write.html
