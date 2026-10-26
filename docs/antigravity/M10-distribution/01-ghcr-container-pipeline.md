# M10-01: Multi-Architecture GHCR Container Pipeline

**Issue:** [#20](https://github.com/hastimal/open-healthcare-agentic-platform/issues/20)  
**Milestone:** [M10 — Helm, Packaging & Distribution](https://github.com/hastimal/open-healthcare-agentic-platform/milestone/1)  
**Parent Epic:** [#18](https://github.com/hastimal/open-healthcare-agentic-platform/issues/18)  
**Branch:** `feat/m10-ghcr-container-pipeline`  

---

## 1. Overview
This implementation introduces a multi-architecture container build, security scanning, and automated publishing pipeline targeting GitHub Container Registry (`ghcr.io/hastimal/`).

### Target OCI Images:
- `ghcr.io/hastimal/open-healthcare-api` (FastAPI backend and multi-agent service)
- `ghcr.io/hastimal/open-healthcare-ui` (Streamlit web application)

### Architectures Supported:
- `linux/amd64` (Standard x86_64 cloud instances and developer workstations)
- `linux/arm64` (Apple Silicon M1/M2/M3/M4 and ARM cloud instances such as AWS Graviton)

---

## 2. CI/CD Workflow Architecture

The workflow is defined in [`.github/workflows/publish-containers.yml`](file:///.github/workflows/publish-containers.yml).

### Pipeline Stages:
1. **Triggering Rules**:
   - `pull_request`: Runs build validation and security scanning without publishing (push disabled).
   - `release (published)`: Builds multi-arch images and publishes to GHCR with semver tags.
   - `workflow_dispatch`: Manual trigger with a `publish` boolean flag for authorized ad-hoc runs.
2. **QEMU & Docker Buildx**:
   - `docker/setup-qemu-action@v3` enables emulation for multi-architecture builds.
   - `docker/setup-buildx-action@v3` provisions the Buildx builder instance with GitHub Actions layer caching (`type=gha`).
3. **Least-Privilege Security**:
   - `contents: read`
   - `packages: write` (only when publishing is confirmed)
   - `id-token: write` (for build provenance attestations)
4. **Supply Chain Security**:
   - **Provenance & SBOM**: `provenance: true` and `sbom: true` attached as OCI attestations to container manifests.
   - **Vulnerability Scanning**: Automated Trivy vulnerability scans (`aquasecurity/trivy-action`) running against single-architecture loaded test images.
   - **Container Startup Smoke Test**: Automates running a container instance, issuing health probe curls, inspecting container logs, and ensuring non-root exit status.

---

## 3. Container Security Hardening Review

- **Zero Hardcoded Secrets**: Verified `.dockerignore` prevents `.env`, `.git`, `.venv`, credentials, and temporary build caches from being added to image contexts.
- **Non-Root Execution**: Both `Dockerfile.api` and `Dockerfile.ui` configure dedicated non-root users (`appuser:appgroup`, UID/GID `10001`).
- **Minimal Runtime Footprint**: Multi-stage builds compile wheels in a builder stage and install only the minimal wheel bundle and `curl` for container health checks in `python:3.12-slim-bookworm`.
- **Public Cloud Registry Neutrality**: Images conform to OCI image specifications with standard labels (`org.opencontainers.image.*`).

---

## 4. Local Build & Test Verification

| Test Suite / Quality Gate | Command | Result |
|---|---|---|
| **Ruff Linter** | `uv run ruff check .` | PASSED (0 errors) |
| **Ruff Formatter** | `uv run ruff format --check .` | PASSED (168 files) |
| **Mypy Type Checking** | `uv run mypy src tests` | PASSED (78 source files) |
| **Unit & Integration Tests** | `uv run pytest --cov=healthcare_agents` | 179 passed, 15 skipped, 0 failures |
| **Test Coverage** | `pytest --cov` | **90.36%** ($\ge 90\%$) |
| **Local Container Build & Health** | `docker build --platform linux/arm64` | Image built; container started; `/health` HTTP 200 OK |
| **Kubernetes Smoke Test Suite** | `uv run python scripts/k8s_smoke_test.py` | 8/8 PASSED on live Kind cluster |

---

## 5. Release Publication Procedure

To publish container images upon milestone release:
1. When a GitHub Release is published (e.g. `v0.10.0-m10`), `.github/workflows/publish-containers.yml` triggers automatically.
2. The workflow verifies semver tags, builds multi-arch manifests, attaches SBOMs, and pushes to GHCR.
3. Once published, the images can be pulled publicly:
   ```bash
   docker pull ghcr.io/hastimal/open-healthcare-api:latest
   docker pull ghcr.io/hastimal/open-healthcare-ui:latest
   ```

---

## 6. Known Limitations
- Local emulation for `linux/amd64` builds on macOS Apple Silicon is significantly slower than native ARM64; multi-arch builds are optimized for CI runners with QEMU caching.
