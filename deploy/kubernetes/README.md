# Kubernetes Deployment Architecture (Open Healthcare Platform)

This directory contains declarative Kubernetes manifests structured using **Kustomize** for local and production deployment.

## Directory Structure

```
deploy/kubernetes/
├── base/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── ui-deployment.yaml
│   ├── ui-service.yaml
│   └── observability/
│       ├── otel-collector.yaml
│       ├── prometheus.yaml
│       ├── tempo.yaml
│       └── grafana.yaml
└── overlays/
    └── local/
        ├── kustomization.yaml
        ├── kind-config.yaml
        ├── nodeports.yaml
        └── host-aliases.yaml
```

## Workloads & Services

| Workload | Kind | Port | Description |
|---|---|---|---|
| `open-healthcare-api` | Deployment + Service | 8000 | FastAPI Gateway & Multi-Agent Engine |
| `open-healthcare-ui` | Deployment + Service | 8501 | Streamlit Interactive Evidence & Presets UI |
| `otel-collector` | Deployment + Service | 4317 / 4318 / 8889 | OpenTelemetry Collector (traces & metrics) |
| `prometheus` | Deployment + Service | 9090 | Prometheus Metrics Engine |
| `tempo` | Deployment + Service | 3200 / 4317 / 4318 | Grafana Tempo Distributed Tracing Backend |
| `grafana` | Deployment + Service | 3000 | Grafana Dashboards & Trace Explorer |

## Local Cluster Deployment (Kind)

For local development and testing, use the automated management scripts:

```bash
# 1. Deploy local Kind cluster and workloads
uv run python scripts/k8s_deploy.py

# 2. Run verification and smoke tests
uv run python scripts/k8s_smoke_test.py

# 3. Clean up cluster and resources
uv run python scripts/k8s_cleanup.py
```
