# dataforge-report

Generates polished HTML/PDF reports from DataForge project results. Assembles all generated artifacts (EDA plots, model leaderboard, SHAP charts, evaluation plots) into a single-file report with embedded images.

## Usage

```
/dataforge-report <project-dir>                     # Full report (EDA + models + SHAP + evaluation)
/dataforge-report eda <project-dir>                 # EDA-only report
```

Or via the router:

```
/dataforge report <project-dir>
```

## What it does

- Scans the project for all generated artifacts (plots, leaderboard, SHAP charts, confusion matrices, ROC curves)
- Assembles them into a Jinja2-based HTML report with embedded base64 images
- Optionally converts to PDF using WeasyPrint (if installed)
- The report is self-contained — a single HTML file you can share or open in any browser

## Output

```
<project>/reports/final_report.html     # Full report
<project>/reports/final_report.pdf      # PDF (if WeasyPrint is available)
```
