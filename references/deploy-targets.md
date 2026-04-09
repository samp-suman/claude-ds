# DataForge — Deployment Target Reference

Reference for `deploy_detect.py` and the `df-deploy` agent.

## Decision Matrix

| Condition | Target | Reason |
|-----------|--------|--------|
| Default (exploratory) | **Streamlit** | Best for demos, dashboards, interactive exploration |
| `--production` flag | **FastAPI** | REST API, scalable, production-ready |
| Time series problem | **Streamlit** | Interactive time-series charts with Plotly |
| Clustering problem | **Streamlit** | Cluster visualization, segment explorer |
| Model > 500MB | **FastAPI** | Efficient serving with model pre-loaded |
| Explicit `--flask` flag | **Flask** | Minimal footprint for simple single-endpoint APIs |

## Streamlit App

**Best for:** Data science demos, internal tools, stakeholder presentations

**Generated app features:**
- Sidebar with feature input sliders/dropdowns
- Real-time prediction as user changes inputs
- Confidence gauge (classification) or prediction value (regression)
- SHAP feature contribution bar chart
- Batch prediction via CSV upload
- Download predictions as CSV

**Run:**
```bash
cd app && streamlit run app.py
```

**Access:** `http://localhost:8501`

**Dependencies:**
```
streamlit>=1.28.0
joblib, pandas, numpy, matplotlib
```

## FastAPI App

**Best for:** Production REST API, microservices, mobile/web frontend integration

**Generated endpoints:**
- `POST /predict` — Single prediction
- `POST /predict/batch` — Batch predictions (CSV upload)
- `GET /health` — Health check
- `GET /model/info` — Model metadata
- `GET /docs` — Auto-generated Swagger UI

**Run:**
```bash
cd app && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Access:** `http://localhost:8000/docs`

**Dependencies:**
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6  # For file upload
joblib, pandas, numpy
```

## Flask App (Minimal)

**Best for:** Simple single-endpoint API, legacy Python environments

**Generated endpoints:**
- `POST /predict`
- `GET /health`

**Run:**
```bash
cd app && python app.py
```

**Access:** `http://localhost:5000`

## Dockerfile Reference

All deployment targets include a production-ready Dockerfile:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
# Streamlit: CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
# FastAPI:   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build & run:**
```bash
docker build -t {project_name} ./app
docker run -p {port}:{port} {project_name}
```

## Cloud Deployment Notes

### Streamlit Cloud
1. Push project to GitHub
2. Connect at share.streamlit.io
3. Set app path to `app/app.py`

### FastAPI on Railway/Render
1. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
2. Add requirements.txt to app/

### Docker + Any Cloud
1. `docker build -t {project_name}:latest ./app`
2. Push to Docker Hub / ECR / GCR
3. Deploy to ECS / GKE / Azure Container Apps
