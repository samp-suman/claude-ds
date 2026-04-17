# Reference: Data Science Role Context

This reference guides role detection and pipeline adaptation. Each role has different
success criteria, output expectations, and technique priorities.

## The 5 Roles

### 1. Data Analyst

**Core question they're answering:** "What is happening and why?"

**Success criteria:** Business stakeholders understand and can act on the analysis
**Output format:** Executive summaries, charts, dashboards, plain-language insights
**Tools they use:** SQL, Excel/Sheets, Tableau/Power BI, Python (pandas, matplotlib)
**What they need from DS pipeline:**
- Clean, well-labeled outputs
- Business KPIs computed (not raw model metrics)
- Trend visualizations with annotations
- Simple, interpretable models (linear regression, decision tree)
- Narrative report explaining findings

**Model preference:** Interpretable over accurate — a logistic regression they can explain beats a neural net they cannot
**Deployment:** Streamlit dashboard or PDF report
**Skip:** Deep hyperparameter tuning, complex ensembles, production APIs

---

### 2. ML Engineer

**Core question they're answering:** "How do we serve this reliably at scale?"

**Success criteria:** Model in production with low latency, monitored, with CI/CD
**Output format:** API endpoints, benchmark tables, monitoring dashboards
**Tools they use:** PyTorch/TF, scikit-learn, FastAPI, Docker, MLflow, Airflow
**What they need from DS pipeline:**
- Best-performing model (not most interpretable)
- Serving latency profiling
- Production-ready artifacts (model.pkl, requirements.txt, API schema)
- Drift monitoring setup
- Feature store integration plan

**Model preference:** Performance-first — XGBoost, LightGBM, neural networks
**Deployment:** FastAPI endpoint + Docker
**Skip:** Extensive business narrative, exploratory storytelling, dashboard

---

### 3. Product Data Scientist

**Core question they're answering:** "Did this change/feature/experiment cause an improvement?"

**Success criteria:** Statistically valid causal conclusions with confidence intervals
**Output format:** Experiment reports with p-values, confidence intervals, effect sizes
**Tools they use:** Python (statsmodels, causalml), SQL, A/B testing frameworks
**What they need from DS pipeline:**
- Causal inference techniques (not just correlation)
- A/B test validity checks (SRM, power analysis, MDE)
- Funnel analysis (conversion, drop-off per stage)
- Retention and cohort analysis
- Uplift modeling if applicable

**Model preference:** Interpretable + causally valid — treatment effect models, logistic for propensity
**Deployment:** Notebook or lightweight internal dashboard
**Skip:** Production serving, complex infrastructure, hyperparameter depth

---

### 4. Applied Scientist / Researcher

**Core question they're answering:** "Does this novel approach work and is the evidence rigorous?"

**Success criteria:** Statistically valid, reproducible, well-documented methodology
**Output format:** Statistical report with methodology, ablations, confidence intervals
**Tools they use:** PyTorch/JAX, statsmodels, scipy, Jupyter, LaTeX
**What they need from DS pipeline:**
- Full cross-validation with variance reporting (not just mean)
- Ablation studies (feature ablation, model ablation)
- Statistical significance testing
- Uncertainty quantification (confidence intervals, credible intervals)
- Reproducibility: random seeds, full configuration logged

**Model preference:** Methodological rigor — whatever the research question demands
**Deployment:** None (research output)
**Skip:** Production serving, dashboards, business narrative

---

### 5. Analytics Engineer

**Core question they're answering:** "Is our data correct, well-modeled, and trustworthy?"

**Success criteria:** Clean, tested, documented data pipeline with lineage
**Output format:** Data quality report, schema documentation, pipeline audit
**Tools they use:** dbt, Airflow, Spark, SQL, Great Expectations
**What they need from DS pipeline:**
- Data quality checks at each transformation stage
- Schema validation and type checking
- Null rate monitoring, uniqueness checks
- Lineage tracking (what transformation produced what)
- Anomaly detection on data pipeline outputs

**Model preference:** Minimal modeling — focus is data correctness, not predictive power
**Deployment:** None (data pipeline)
**Skip:** Complex ML modeling, hyperparameter tuning, dashboard creation

---

## Role Detection Signals

| Signal Phrase | Most Likely Role |
|--------------|-----------------|
| "understand", "why did", "what happened", "trend" | data_analyst |
| "production", "serve", "API", "deploy", "scale", "real-time" | ml_engineer |
| "A/B test", "conversion", "funnel", "retention", "experiment", "causal" | product_ds |
| "novel", "research", "hypothesis", "statistical test", "ablation" | researcher |
| "pipeline", "dbt", "warehouse", "schema", "ETL", "data quality" | analytics_engineer |

## Role × Domain Common Combinations

| Role | Domain | Typical Problems |
|------|--------|-----------------|
| product_ds | marketing | churn prediction, A/B testing, retention curves, CLV |
| ml_engineer | finance | fraud detection system, real-time scoring API |
| researcher | healthcare | survival analysis, clinical trial evaluation |
| data_analyst | retail | sales trend, inventory KPI dashboard |
| ml_engineer | manufacturing | predictive maintenance serving API |
| product_ds | ecommerce | conversion optimization, recommendation evaluation |
| analytics_engineer | logistics | demand pipeline, inventory data quality |

## Pipeline Adjustments by Role

| Role | EDA Depth | Feature Style | Model Bias | Deployment |
|------|-----------|--------------|------------|------------|
| data_analyst | standard | business_features | interpretable | streamlit |
| ml_engineer | quick_profile | ml_features | performance | fastapi |
| product_ds | deep_statistical | business_features | interpretable | notebook |
| researcher | deep_statistical | statistical_transforms | rigorous | none |
| analytics_engineer | standard | minimal | minimal | none |
