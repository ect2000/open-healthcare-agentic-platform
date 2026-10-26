# M10-4: Helm OCI Packaging & GHCR Registry Distribution

> **Tracking:** Issue #22 (Epic #18)  
> **Status:** Implemented & Verified  
> **Target OCI Registry:** `oci://ghcr.io/hastimal/charts/open-healthcare`  
> **Chart Version:** `0.10.0` (AppVersion: `0.10.0`)

---

## 1. Overview & Objective

The objective of Issue #22 is to implement a production-grade, secure continuous delivery pipeline for packaging the Open Healthcare Agentic Platform Helm chart as an **Open Container Initiative (OCI)** compliant artifact and publishing it to **GitHub Container Registry (GHCR)**.

This enables Kubernetes developers and platform engineers to install the platform without cloning the GitHub repository:

```bash
helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare --version 0.10.0
```

> **Availability Note:**  
> The `helm install oci://...` command is available immediately following an authorized release workflow execution. For local testing prior to release tag creation, local chart installations via directory (`helm install healthcare charts/open-healthcare`) or local package archive are supported.

---

## 2. Helm OCI Architecture & Registry Layout

### OCI Registry Target
- **Registry Provider:** GitHub Container Registry (`ghcr.io`)
- **Repository URI:** `oci://ghcr.io/hastimal/charts/open-healthcare`
- **OCI Media Types:**
  - `application/vnd.cncf.helm.config.v1+json`
  - `application/vnd.cncf.helm.chart.content.v1.tar+gzip`
- **Chart Name:** `open-healthcare`
- **Packaging Format:** `open-healthcare-0.10.0.tgz`

---

## 3. GitHub Actions CI/CD Pipeline

The dedicated release and validation workflow is defined in [`.github/workflows/publish-helm-chart.yml`](../../../.github/workflows/publish-helm-chart.yml):

### Triggers & Security Safeguards
1. **Pull Requests (PR):**
   - Triggers when files under `charts/**` change.
   - Runs `helm lint --strict`, full template rendering tests, metadata validation, and dry-run packaging (`helm package`).
   - **Never pushes or publishes artifacts** during PR validation.
2. **Release (`published` event):**
   - Automatically triggered upon GitHub release publication.
   - Packages chart, authenticates to GHCR via ephemeral `GITHUB_TOKEN`, pushes chart to `oci://ghcr.io/hastimal/charts`, and executes an OCI pull verification step.
3. **Manual Dispatch (`workflow_dispatch`):**
   - Requires explicit `publish: true` input to prevent accidental pushes.

### Minimal Permissions
```yaml
permissions:
  contents: read
  packages: write
  id-token: write
```

---

## 4. Quality Gates & Regression Verification

### A. Python Quality & Unit Tests
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest -m "not live" --cov=healthcare_agents --cov-report=term-missing
```
- **Ruff & Mypy:** Clean with 0 errors across 173 files and 80 source modules.
- **Pytest:** 201 passed, 15 skipped, 0 failed.
- **Coverage:** **90.26%** (exceeds 90.0% threshold).

### B. Helm Chart Linting & Template Rendering
```bash
helm lint charts/open-healthcare --strict
helm template test-release charts/open-healthcare > /dev/null
helm package charts/open-healthcare -d /tmp/helm-test-pkg
```
- Linting passed with 0 errors.
- Template rendering passed with default values and with full observability enabled.
- Packaging produced verified tarball `open-healthcare-0.10.0.tgz` (9.4 KB).

---

## 5. Deployment Instructions

### Installing from OCI Registry (Post-Release)
```bash
# 1. Pull chart artifact from GHCR
helm pull oci://ghcr.io/hastimal/charts/open-healthcare --version 0.10.0

# 2. Install chart onto target Kubernetes cluster
helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare \
  --version 0.10.0 \
  --namespace healthcare \
  --create-namespace
```

### Installing from Local Source (Available Now)
```bash
helm install healthcare charts/open-healthcare \
  --namespace healthcare \
  --create-namespace
```
