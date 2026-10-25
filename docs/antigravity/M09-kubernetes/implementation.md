# Milestone M9: Implementation Details

## Architectural Overview
Milestone M9 implements a complete declarative Kubernetes infrastructure architecture under `deploy/kubernetes/`:

### Manifests Created
- `deploy/kubernetes/base/`:
  - `namespace.yaml`: Defines dedicated namespace `open-healthcare`.
  - `configmap.yaml`: Configures API URLs, retrieval modes, timeouts, and OTel parameters.
  - `secret.yaml`: Secure secret references for optional provider keys.
  - `api-deployment.yaml` & `api-service.yaml`: FastAPI multi-agent backend deployment with liveness/readiness probes.
  - `ui-deployment.yaml` & `ui-service.yaml`: Streamlit discovery interface.
  - `observability/otel-collector.yaml`: OpenTelemetry Collector deployment and pipeline routing.
  - `observability/prometheus.yaml`: Prometheus time-series metrics server.
  - `observability/tempo.yaml`: Grafana Tempo distributed trace backend.
  - `observability/grafana.yaml`: Provisioned Grafana deployment with datasources and dashboard definitions.
- `deploy/kubernetes/overlays/local/`:
  - `kustomization.yaml`: Local overlay configuration.
  - `kind-config.yaml`: Kind cluster definition with port mappings to host (`8000`, `8501`, `3000`, `9090`, `3200`).
  - `nodeports.yaml`: NodePort service definitions.
  - `host-ollama-bridge.yaml`: Lightweight in-cluster Nginx reverse proxy routing requests to macOS host Ollama.
  - `configmap-patch.yaml`: Configures in-cluster workloads to communicate via `host-ollama-bridge:11434`.

### Operational Automation Scripts
- `scripts/k8s_deploy.py`: Reproducible one-command Kind cluster lifecycle and rollout manager.
- `scripts/k8s_smoke_test.py`: Comprehensive smoke and acceptance testing suite.
- `scripts/k8s_cleanup.py`: Scoped teardown script for namespace or cluster cleanup.
- `scripts/generate_k8s_architecture_diagram.py`: Generator for high-resolution architecture diagram.
- `scripts/capture_m9_screenshots.py`: Playwright automated browser test and screenshot capture script.
