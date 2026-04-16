# dataforge-analysis (Workflow)

Data analysis workflow that helps you understand a dataset without building models. Runs ingestion, validation, profiling, EDA, and report generation.

## Usage

```
/dataforge-analysis <dataset> [target]
/dataforge analyze <dataset> [target]
```

## Pipeline steps

```
ingest -> validate -> profile -> EDA -> report
```

1. **Ingest** — Load dataset
2. **Validate** — Quality checks
3. **Profile** — Statistics and problem type detection
4. **EDA** — Full exploratory analysis with plots
5. **Report** — EDA-focused HTML report

## When to use

Use this instead of `/dataforge run` when you want to explore and understand a dataset before committing to model training. The target column is optional — if omitted, the analysis focuses on general data profiling without target-specific insights.
