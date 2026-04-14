---
area: real-estate
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area real-estate
status: seed
schema_version: 1.0
---

# Real Estate — Domain Knowledge

> Baseline seeded from training cutoff. Refresh with the command above.

## Core features

### [re-001] Price per square foot is a leakage trap
**Summary:** `price_per_sqft = price / sqft` derived from the target leaks perfectly. Likewise `price / num_bedrooms`, `price / lot_size`. Any ratio with the target in the numerator must be removed before training.
**When to use:** Never as a feature; only as an EDA cross-check.
**Pitfall:** Models score implausibly well on CV; deploy app collapses.

### [re-002] Location encoding
**Summary:** Pin code / postal code / locality is the single highest-signal feature. Use target-encoding with CV folds (out-of-fold means) or hierarchical means (city -> locality -> sub-locality).
**When to use:** Always; raw one-hot of pin codes blows up dimensionality.
**Pitfall:** Plain target encoding leaks; needs CV folds and a smoothing prior.

### [re-003] Area unit normalization
**Summary:** Indian listings mix sq.ft, sq.m, sq.yd, marla, kanal. Strings like "1350(125.42 sq.m.)" or "Super Built up area 1350" need parsing to a single unit. Carpet area vs super built-up vs built-up differ by 15-25%.
**When to use:** Always when ingesting scraped MagicBricks/99acres/Housing.com data.
**Pitfall:** Mixing units silently produces 10x outliers.

### [re-004] Currency string parsing
**Summary:** Indian price strings: "45 Lac" = 4.5e6, "1.25 Crore" = 1.25e7, "₹85L" = 8.5e6. Western: "$1.2M", "£450k". Build a robust parser, expose as a `FunctionTransformer`.
**When to use:** Whenever `price` arrives as a string.
**Pitfall:** Naive `float()` drops the magnitude suffix.

### [re-005] Floor parsing
**Summary:** "2nd of 4 Floors", "Ground", "G+12", "Top floor of 5" -> extract `floor_num` + `total_floors` + `is_ground` + `is_top`. Top and ground floors price differently.
**When to use:** Apartment/flat datasets.

## Pitfalls

- Mixed listing types (apartments + houses + plots) in `data/raw/` need a `listing_type` column; train one model per type or include the type as a feature.
- Time-of-listing matters: prices drift seasonally and with macro rates. Include `listing_month` and consider time-based CV.
- Furnishing status ("furnished/semi/unfurnished") is high-value but inconsistently labelled.

## Recommended metrics

- **Primary**: MAE in original currency units (interpretable to users).
- **Secondary**: MAPE (capped at 100%), R^2.
- Avoid RMSLE if prices span <2 orders of magnitude.

## Key sources to refresh from

- Kaggle "House Prices - Advanced Regression Techniques" winning solutions
- Zillow tech blog (zestimate methodology posts)
- 99acres/MagicBricks scraping notebooks on Kaggle
- Papers: "Hedonic Price Models" literature
