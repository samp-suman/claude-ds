---
name: dataforge-kaggle
description: >
  DataForge extension for Kaggle dataset download. Downloads a dataset from
  Kaggle by slug (owner/dataset-name) and passes it to the main DataForge
  pipeline. Requires the kaggle Python package and API credentials.
user-invokable: false
---

# DataForge Kaggle Extension

Downloads a Kaggle dataset and feeds it into the DataForge pipeline.

## Setup (one-time)

1. Install: `pip install kaggle`
2. Get API key from kaggle.com → Account → API → Create New Token
3. Place `kaggle.json` in `~/.kaggle/kaggle.json`

## Usage

```
/dataforge run kaggle:titanic/titanic <target_column>
/dataforge run kaggle:owner/dataset-name <target_column>
```

The `kaggle:` prefix triggers this extension.

## Process

```bash
python3 ~/.claude/skills/dataforge/extensions/kaggle/scripts/kaggle_fetch.py \
  --dataset "titanic/titanic" \
  --output-dir "{OUTPUT_DIR}"
```

After download, passes the downloaded CSV path to `scripts/ingest.py`.
