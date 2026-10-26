# M10-5: Final Acceptance, Release Verification & Tagging Readiness

> **Tracking:** Issue #23 (Epic #18)  
> **Status:** Stage A Pre-Release Acceptance Complete — Ready for Stage B Release Execution  
> **Target Release Tag:** `v0.10.0-m10`  
> **Target Version:** `0.10.0`

---

## 1. Executive Summary & Objective

Milestone 10 delivers comprehensive packaging, multi-architecture containerization, production-grade Helm orchestration, OCI registry distribution, and a zero-install one-command Python CLI launcher for the **Open Healthcare Agentic Platform**.

Stage A Pre-Release Acceptance has been executed across all platform surfaces:
- **Repository Integrity:** Clean tree, unified `0.10.0` SemVer, synchronized dependencies.
- **Packaging:** Verified PEP 517 wheel and sdist builds with bundled Streamlit UI and zero-Docker native mode.
- **Local Native Launcher:** Validated `healthcare-agents` CLI (`check`, `start`, `stop`, `status`, `demo`) and bare invocation.
- **Docker Multi-Arch Containerization:** Multi-arch amd64/arm64 GHCR pipelines, non-root security context (`appuser:10001`), and Docker Compose profiles.
- **Kubernetes & Helm:** Fully linted, templated, and verified Helm chart with local Kind deployment, `host-ollama-bridge`, and Prometheus/Tempo/Grafana observability.
- **Helm OCI Packaging:** OCI pipeline to `oci://ghcr.io/hastimal/charts/open-healthcare` with strict release protection and minimal permissions.
- **Quality Gates:** 100% passing tests (201 passed, 15 skipped, 0 failed), **90.26% test coverage** ($\ge 90\%$), strict Ruff formatting, and strict Mypy typing.
- **Security:** Ephemeral `GITHUB_TOKEN`, no hardcoded secrets, no PHI collection/logging, read-only Grafana anonymous viewer, and pull request publication protection.

---

## 2. Stage A Verification Evidence

### A. Python Quality & Packaging Gates
```bash
uv run ruff check .               # Pass (0 errors)
uv run ruff format --check .      # Pass (174 files formatted)
uv run mypy src tests             # Pass (80 source files verified)
uv run pytest -m "not live" --cov=healthcare_agents --cov-report=term-missing
# Result: 201 passed, 15 skipped, 0 failed, 90.26% coverage
```

### B. Isolated Wheel Execution & Browser Acceptance
- Built distribution: `open_healthcare_agentic_platform-0.10.0-py3-none-any.whl` (186 KB) and `open_healthcare_agentic_platform-0.10.0.tar.gz` (181 KB).
- Installed in isolated virtual environment `/tmp/test-cli-env` completely outside the repository source tree.
- Tested:
  - `healthcare-agents --help` $\rightarrow$ Exit 0
  - `healthcare-agents --version` $\rightarrow$ Exit 0
  - `healthcare-agents check --api-port 9000 --ui-port 9501` $\rightarrow$ Exit 0 (All prerequisites passed)
  - Headless Playwright test against wheel-launched instance verified Streamlit UI rendering, quick presets, and live grounded multi-agent search execution.
  - `healthcare-agents stop` cleanly terminated managed PIDs (API: 38001, UI: 38002) and freed ports.

### C. Kubernetes & Observability Smoke Test
Executed `python scripts/k8s_smoke_test.py` against active cluster `open-healthcare`:
```text
[k8s-smoke-test]   [PASS] Pods Running (API, UI, bridge, collector, Prometheus, Tempo, Grafana)
[k8s-smoke-test]   [PASS] FastAPI Health Probe (HTTP 200)
[k8s-smoke-test]   [PASS] Streamlit Health Probe (HTTP 200)
[k8s-smoke-test]   [PASS] Tempo Readiness (HTTP 200)
[k8s-smoke-test]   [PASS] Grafana Health (HTTP 200)
[k8s-smoke-test]   [PASS] Host Ollama Connectivity via Gateway (SUCCESS)
[k8s-smoke-test]   [PASS] End-to-End Multi-Agent Search (Trace ID: e86019653ebc50f47bb44c59e658c235)
[k8s-smoke-test]   [PASS] Prometheus Healthcare Metrics Ingestion (SUCCESS)
```

### D. Helm Validation
```text
helm lint charts/open-healthcare --strict --> 1 chart(s) linted, 0 failed
helm template open-healthcare charts/open-healthcare --> Valid manifest rendering
helm package charts/open-healthcare -d /tmp/helm-test-pkg --> open-healthcare-0.10.0.tgz (9.4 KB)
```

---

## 3. Stage B Release Checklist (To be executed upon approval)

1. [ ] **Git Tagging:**
   Create annotated tag on verified `main`:
   ```bash
   git tag -a v0.10.0-m10 -m "Release v0.10.0-m10: Helm, Packaging & One-Command Distribution"
   git push origin v0.10.0-m10
   ```
2. [ ] **GitHub Release:**
   Publish GitHub Release `v0.10.0-m10` targeting tag `v0.10.0-m10`.
3. [ ] **Automated CI/CD Triggers:**
   - Multi-arch container build triggers and publishes:
     - `ghcr.io/hastimal/open-healthcare-api:0.10.0`
     - `ghcr.io/hastimal/open-healthcare-ui:0.10.0`
   - Helm OCI publishing triggers and pushes:
     - `oci://ghcr.io/hastimal/charts/open-healthcare:0.10.0`
4. [ ] **PyPI Publication (Authorized Manual Step):**
   Publish built wheel and sdist to PyPI for `open-healthcare-agentic-platform`.
5. [ ] **Post-Release Sanity Verification:**
   - `uvx open-healthcare-agentic-platform`
   - `helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare --version 0.10.0`
