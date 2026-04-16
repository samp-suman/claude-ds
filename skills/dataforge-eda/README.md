# dataforge-eda

Exploratory Data Analysis with parallel per-column statistical profiling, distribution plots, correlation heatmaps, target analysis, and domain-specific insights.

## Usage

```
/dataforge-eda <dataset>                            # Full EDA (per-column + global)
/dataforge-eda column <dataset> [target]            # Per-column analysis only
/dataforge-eda global <dataset> [target]            # Global analysis only (correlations, target dist)
/dataforge-eda summary <dataset>                    # Quick text summary
```

Or via the router:

```
/dataforge eda <dataset>
```

## What it does

- **Per-column analysis** — Spawns parallel agents (batches of 10) that compute statistics and generate distribution plots for each column (numeric histograms, categorical bar charts, datetime timelines).
- **Global analysis** — Correlation heatmap, target distribution, missing value matrix, feature-target relationships.
- **Domain insights** — When a domain is detected (healthcare, finance, retail, etc.), adds domain-specific feature studies and clinical/business thresholds.

## Output

All plots are saved to `reports/eda/` in the project directory. The EDA summary JSON is written to `data/interim/eda_summary.json`.
