# dataforge-deploy

Generates a complete, runnable deployment application for the best trained model. Outputs a ready-to-run `app/` directory with application code, dependencies, and Docker configuration.

## Usage

```
/dataforge-deploy <project-dir>                     # Generate Streamlit app (default)
/dataforge-deploy <project-dir> --production        # Generate FastAPI app with Docker
```

Or via the router:

```
/dataforge deploy <project-dir>
/dataforge deploy <project-dir> --production
```

## What it does

- Detects the best model from the leaderboard
- Generates `app/app.py` (Streamlit for interactive use, FastAPI for production APIs)
- Generates `app/requirements.txt` and `app/Dockerfile`
- The deploy app loads the fitted sklearn Pipeline and model pickle directly — no reimplementation of preprocessing logic

## Output

```
<project>/app/
├── app.py              # Streamlit or FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
└── Makefile            # Build/run shortcuts
```

## Running the generated app

```bash
cd <project>/app
pip install -r requirements.txt
streamlit run app.py            # Streamlit
# or
uvicorn app:app --reload        # FastAPI
```
