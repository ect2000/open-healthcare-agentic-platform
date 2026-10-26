# M10-02: Kubernetes Helm Chart Architecture & Verification

**Issue:** [#19](https://github.com/hastimal/open-healthcare-agentic-platform/issues/19)  
**Milestone:** [M10 — Helm, Packaging & Distribution](https://github.com/hastimal/open-healthcare-agentic-platform/milestone/1)  
**Parent Epic:** [#18](https://github.com/hastimal/open-healthcare-agentic-platform/issues/18)  
**Branch:** `feat/m10-helm-chart`  

---

## 1. Overview
This milestone delivery introduces a production-oriented, vendor-neutral Helm v2 chart for the Open Healthcare Agentic Platform, packaged under `charts/open-healthcare/`. It provides single-command deployment across local development (Kind) and enterprise Kubernetes environments.

---

## 2. Helm Chart Architecture

```
charts/open-healthcare/
├── Chart.yaml                  # Chart metadata (v0.10.0, appVersion 0.10.0)
├── values.yaml                 # Production-ready defaults (GHCR images, ClusterIP, OTel, probes)
├── values-local.yaml           # Kind cluster overlay with NodePort mappings & host Ollama gateway
├── values-production.yaml      # Multi-replica production configuration with Ingress & TLS
├── .helmignore                 # Package exclusions
├── dashboards/
│   └── healthcare_observability.json # Bundled Grafana dashboard definition
└── templates/
    ├── _helpers.tpl            # Standardized labels, naming, and selector templates
    ├── api-deployment.yaml     # FastAPI backend & multi-agent service deployment
    ├── api-service.yaml        # API Service (ClusterIP / NodePort)
    ├── ui-deployment.yaml      # Streamlit web frontend deployment
    ├── ui-service.yaml         # UI Service (ClusterIP / NodePort)
    ├── configmap.yaml          # Unified environment variables & telemetry configuration
    ├── host-ollama-bridge.yaml # In-cluster reverse proxy for local native Ollama
    ├── otel-collector.yaml     # OpenTelemetry Collector (OTLP gRPC/HTTP to Prometheus & Tempo)
    ├── prometheus.yaml         # In-chart Prometheus deployment, scrape configs & TSDB
    ├── tempo.yaml              # In-chart Grafana Tempo distributed trace engine
    ├── grafana.yaml            # Grafana deployment, pre-provisioned datasources & dashboards
    ├── serviceaccount.yaml     # Dedicated ServiceAccount with non-root security context
    ├── ingress.yaml            # Ingress template with TLS and path-based routing
    └── NOTES.txt               # Post-installation instructions & port-forwarding helpers
```

---

## 3. Inference & Observability Configuration Modes

### Inference Modes:
1. `local-ollama` (Default in `values-local.yaml`): Deploys an internal `host-ollama-bridge` nginx proxy routing container traffic to `host.docker.internal:11434`, enabling native Apple Silicon GPU acceleration for `gemma4:e2b`.
2. `external`: Bypasses the local gateway and points directly to any remote or shared inference endpoint (`inference.baseUrl`).
3. `kubernetes`: Prepared for in-cluster inference services (e.g., vLLM or Kubernetes cluster models).

### Observability Modes:
1. `bundled` (Default): Deploys in-chart OTel Collector, Prometheus, Tempo, and Grafana. Configures datasources automatically and mounts pre-configured dashboards.
2. `external`: Sends OTLP metrics and traces to an existing cluster telemetry collector without deploying duplicate instances.
3. `disabled`: Disables telemetry export entirely for lightweight edge footprints.

---

## 4. Security Hardening

- **No Hardcoded Credentials**: Integrates with existing Kubernetes Secrets (`healthcare-secrets`). Grafana admin user/password and API keys are referenced via `secretKeyRef`.
- **Role Isolation**: Grafana anonymous user role is locked to `Viewer` (`GF_AUTH_ANONYMOUS_ORG_ROLE="Viewer"`).
- **Non-Root Execution**: Workloads run with `runAsNonRoot: true`, `runAsUser: 10001`, and dropped capabilities.
- **Internal Gateway Only**: The `host-ollama-bridge` is exposed strictly as a `ClusterIP` service.
- **Privacy Assurance**: Telemetry spans and logs contain zero Patient Health Information (PHI) or secret tokens.

---

## 5. Verification & Acceptance Results

### Static & Lint Validation:
- `helm lint charts/open-healthcare`: **PASSED** (0 failures).
- `helm template healthcare charts/open-healthcare`: **PASSED** (valid default manifests rendered).
- `helm template healthcare charts/open-healthcare -f charts/open-healthcare/values-local.yaml`: **PASSED**.
- `helm template healthcare charts/open-healthcare -f charts/open-healthcare/values-production.yaml`: **PASSED**.

### Live Cluster Lifecycle Validation (Isolated Namespace `test-helm-acceptance`):
1. **Installation (`helm install`)**:
   - 7/7 pods reached `Running` phase (`api`, `ui`, `host-ollama-bridge`, `otel-collector`, `prometheus`, `tempo`, `grafana`).
   - FastAPI `/health` returned HTTP 200 OK.
   - Ollama bridge successfully communicated with native host `gemma4:e2b`.
2. **End-to-End Multi-Agent Search**:
   - Executed live search request for `"pediatric cardiologist in Chicago"`.
   - Parallel query fan-out completed across NPPES (2 providers), PubMed (5 citations), and MedlinePlus (3 topics).
   - Answer synthesis and deterministic validation completed; grounded response returned with full citations.
3. **Upgrade (`helm upgrade`)**:
   - Scaled API deployment to 2 replicas cleanly without downtime.
4. **Rollback (`helm rollback`)**:
   - Reverted release revision 2 back to revision 1; successfully restored 1 API replica.
5. **Uninstall (`helm uninstall`)**:
   - Chart release uninstalled cleanly with zero orphaned pods, services, or configmaps.

### Platform Quality Gates:
- `uv run ruff check .`: PASSED
- `uv run ruff format --check .`: PASSED (169 files formatted cleanly)
- `uv run mypy src tests`: PASSED (78 source files checked, 0 errors)
- `uv run pytest --cov=healthcare_agents --cov-report=term-missing`: 179 passed, 15 skipped, 0 failures; **90.36% coverage**.
- `uv run python scripts/k8s_smoke_test.py`: 8/8 smoke tests passed on Kind cluster.
- `kubectl kustomize`: Both `deploy/kubernetes/base` and `deploy/kubernetes/overlays/local` verified regression-free.
