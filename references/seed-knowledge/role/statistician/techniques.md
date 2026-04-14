---
area: statistician
category: role
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area statistician
status: seed
schema_version: 1.0
---

# Statistician — Inference and Uncertainty Knowledge

## Core principles

### [stat-001] Confidence intervals beat point estimates
**Summary:** Always report a model metric WITH a 95% bootstrap CI. CV mean alone is misleading; if the std is wide, the model is unstable.

### [stat-002] Multiple testing correction
**Summary:** When you compare 50 features for significance, ~2-3 will look "significant" by chance. Use Bonferroni (strict), Benjamini-Hochberg FDR (looser), or Holm.

### [stat-003] Effect size beats p-value
**Summary:** With enough data everything is "significant". Report Cohen's d, odds ratio, or relative risk. A statistically significant 0.1% lift may be operationally worthless.

### [stat-004] Power analysis BEFORE the experiment
**Summary:** Compute required sample size for the minimum detectable effect (`statsmodels.power`). Running underpowered tests wastes time and fools stakeholders.

### [stat-005] Distribution checks
**Summary:** Don't assume normal. Use Q-Q plots, Shapiro-Wilk for n<5000, Anderson-Darling otherwise. Heavy-tailed targets often need log transform or Tweedie/quantile regression.

### [stat-006] Heteroskedasticity matters for linear models
**Summary:** OLS standard errors assume homoscedasticity. If residuals fan out, use HC0/HC3 robust standard errors or weighted least squares.

### [stat-007] Causal vs predictive thinking
**Summary:** A predictive model can use any correlated feature. A causal claim needs DAGs, identifiability, and either an experiment or a quasi-experimental design (DiD, RDD, IV, synthetic control).

## Pitfalls

- p-hacking: testing 20 hypotheses and reporting the one that hit p<0.05.
- Ignoring confounders in observational studies.
- Conflating prediction accuracy with causal effect.
- Reporting R^2 without checking residual structure.
- Bootstrapping with too few resamples (use >=1000).

## Recommended tools

- `statsmodels` for classical inference (GLM, OLS, time series, hypothesis tests).
- `scipy.stats` for distribution tests.
- `lifelines` for survival.
- `pingouin` for clean ANOVA / correlation / effect-size APIs.
- `causalml`, `econml`, `dowhy` for causal inference.

## Key sources

- "Statistical Rethinking" (Richard McElreath) - Bayesian-first
- "Practical Statistics for Data Scientists" (Bruce, Bruce, Gedeck)
- "All of Statistics" (Wasserman)
- "Causal Inference: The Mixtape" (Cunningham)
