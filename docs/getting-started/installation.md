# Platform Installation & Quick Start Guide

> **Target:** Get running from zero to a live demonstration in ~10 minutes.  
> **Prerequisites:** Python 3.12+ (and optional local Ollama for real AI inference).  

---

## Installation Pathways

Select the pathway that matches your environment:

1. **Pathway A (Zero-Install / PyPI):** Recommended for developers who want to run the platform immediately with Python.
2. **Pathway B (Docker Compose):** Recommended for containerized local workflows with full observability.
3. **Pathway C (Kubernetes & Kind):** Recommended for cloud-native Kubernetes development.
4. **Pathway D (Helm OCI Chart):** Recommended for deploying to an existing Kubernetes cluster.

---

## Pathway A: One-Command Zero-Install (PyPI / `uvx`)

You do not need to clone the repository or manually manage virtual environments. You can run directly via `uvx` or `pip`:

### 1. Check Version & Preflight
```bash
# Direct execution via uvx (zero installation)
uvx --from open-healthcare-agentic-platform healthcare-agents --version

# Run local diagnostic preflight checks
uvx --from open-healthcare-agentic-platform healthcare-agents check
```

### 2. Start Platform Services
```bash
# Launches FastAPI (8000) and Streamlit UI (8501)
uvx --from open-healthcare-agentic-platform healthcare-agents start
```
The CLI automatically launches your web browser to `http://localhost:8501`.

### 3. Alternative: Global Install with `pip`
```bash
pip install open-healthcare-agentic-platform
healthcare-agents check
healthcare-agents start
```

### 4. Stopping Services
```bash
healthcare-agents stop
```

---

## Pathway B: Docker Compose Deployment

The containerized setup packages FastAPI and Streamlit into lightweight, non-root multi-stage images.

### 1. Prerequisites
- Docker Engine 24.0+ & Docker Compose v2.20+
- Host Ollama running locally (for Metal / CUDA acceleration) OR use Profile B for fully containerized Ollama.

### 2. Profile A: Host Ollama (Recommended for Apple Silicon & Workstations)
Connects containers to host Ollama (`host.docker.internal:11434`) for full hardware acceleration:
```bash
# Build and launch backend API and frontend UI
docker compose up -d --build

# Verify container status
docker compose ps

# Open Streamlit
open http://localhost:8501
```

### 3. Profile B: Fully Containerized Ollama
Runs the complete stack including an Ollama container with persistent model volume:
```bash
docker compose --profile container-ollama up -d --build
```

### 4. Teardown
```bash
docker compose down
```

---

## Pathway C: Local Kubernetes (Kind)

Deploy the complete platform including in-cluster reverse proxy (`host-ollama-bridge`) and observability stack into a local Kind cluster:

### 1. Prerequisites
- `kubectl`, `kind`, and `kustomize` installed.
- Docker running.

### 2. Deploy Cluster
```bash
# Create Kind cluster and apply declarative Kustomize manifests
python scripts/k8s_deploy.py
```

### 3. Verify Deployment
```bash
kubectl get pods -n healthcare
```

### 4. Access Services via Port Forwarding
```bash
# UI (Streamlit)
kubectl port-forward -n healthcare svc/open-healthcare-ui 8501:8501 &

# API (FastAPI)
kubectl port-forward -n healthcare svc/open-healthcare-api 8000:8000 &

# Grafana Observability Dashboard
kubectl port-forward -n healthcare svc/open-healthcare-grafana 3000:3000 &
```

### 5. Cleanup
```bash
python scripts/k8s_cleanup.py
```

---

## Pathway D: Helm OCI Chart Installation

Deploy to any Kubernetes cluster using the official OCI artifact published to GitHub Container Registry:

### 1. Install Chart from GHCR OCI
```bash
helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare \
  --version 0.10.1 \
  --namespace healthcare \
  --create-namespace
```

### 2. Verify Release
```bash
helm list -n healthcare
kubectl get all -n healthcare
```

### 3. Configuration & Custom Values
Custom values can be passed during install:
```bash
helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare \
  --version 0.10.1 \
  --namespace healthcare \
  --set api.replicaCount=2 \
  --set observability.enabled=true
```

### 4. Uninstall
```bash
helm uninstall healthcare -n healthcare
```

---

## External Prerequisites: Local Ollama & Gemma 4

While the platform includes deterministic test fixtures and offline fallback modes, running live AI inference requires Ollama:

1. **Install Ollama:** Visit [ollama.com](https://ollama.com/) or run:
   ```bash
   brew install ollama  # macOS
   ```
2. **Start Ollama Service:**
   ```bash
   ollama serve
   ```
3. **Download Gemma 4 Model:**
   ```bash
   ollama pull gemma4:e2b
   ```
4. **Verify Model Installation:**
   ```bash
   healthcare-agents model status
   ```
