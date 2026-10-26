# M10.1: PyPI README Images Fix, CLI Version Correction & Release Polish

> **Tracking:** Milestone 10.1 Patch Release Polish  
> **Status:** Verification Complete — Ready for Review & Approval  
> **Baseline Release:** `v0.10.0-m10` / PyPI `0.10.0`  
> **Proposed Patch Version:** `0.10.1`  
> **Proposed Release Tag:** `v0.10.1-m10.1`  

---

## 1. Executive Summary

Milestone 10 delivered the complete distribution release (`v0.10.0-m10`), publishing the package to PyPI, multi-arch container images to GHCR, and Helm charts to GHCR OCI.

Post-release audit and user testing identified two non-functional polish issues and verified external distribution reachability:
1. **Broken PyPI README Images:** PyPI's package renderer cannot resolve relative repository paths (e.g., `docs/images/arch.png`). All 22 image references in `README.md` have been updated to absolute raw GitHub URLs pointing to `https://raw.githubusercontent.com/hastimal/open-healthcare-agentic-platform/main/docs/images/`.
2. **CLI Version Mismatch:** `uvx --from open-healthcare-agentic-platform==0.10.0 healthcare-agents --version` reported `0.6.0` due to a legacy hardcoded `__version__ = "0.6.0"` string in `src/healthcare_agents/__init__.py`. This has been corrected to dynamically extract the installed distribution version using `importlib.metadata.version()`.
3. **GHCR Public Access Verification:** All three GHCR distribution endpoints (`open-healthcare-api`, `open-healthcare-ui`, `charts/open-healthcare`) were confirmed to be public and freely accessible anonymously without credentials.
4. **Generalized Release Tag Mapping:** Hardcoded `0.10.0` assumptions in `.github/workflows/publish-containers.yml` were generalized using regex matchers so that subsequent tags (such as `v0.10.1-m10.1`) automatically extract `0.10.1` and `0.10` container tags.

---

## 2. Phase-by-Phase Audit & Root Cause Analysis

### Phase 2: Broken PyPI README Images

- **Root Cause:** When PyPI packages are published, `pyproject.toml` references `readme = "README.md"`. The markdown content is rendered on PyPI's web portal (`https://pypi.org/project/open-healthcare-agentic-platform/`). PyPI does not host local repository assets, causing all relative markdown image links (`![caption](docs/images/...)`) to 404 on PyPI.
- **Audited Images:** Exactly 22 image links were identified across `README.md`:
  - Architecture overview diagram: `architecture_m08.png`
  - Streamlit UI screenshots (Main Search, Presets, Agent Reasoning, Patient Education, Clinical Evidence, Provenance): `m08_platform_overview.png`, `m08_query_presets.png`, `m08_agent_reasoning.png`, `m08_patient_education.png`, `m08_clinical_evidence.png`, `m08_provenance.png`
  - Grafana Observability Dashboards (Full Platform, Agent Performance, Retrieval Latency, Model Metrics): `m08_grafana_overview.png`, `m08_grafana_agent_performance.png`, `m08_grafana_retrieval_latency.png`, `m08_grafana_model_metrics.png`
  - Tempo Distributed Tracing (Span Graph, Trace Waterfall): `m08_tempo_trace_graph.png`, `m08_tempo_trace_detail.png`
  - Prometheus Metric Visualizations: `m08_prometheus_targets.png`, `m08_prometheus_agent_invocations.png`, `m08_prometheus_retrieval_duration.png`
  - Kubernetes Kind Deployment & Observability: `m09_k8s_pods.png`, `m09_grafana_dashboard.png`, `m09_tempo_trace.png`, `m09_prometheus_targets.png`, `m09_k8s_services.png`
- **Resolution:** All 22 relative links were converted to absolute raw GitHub URLs:
  `https://raw.githubusercontent.com/hastimal/open-healthcare-agentic-platform/main/docs/images/<filename>.png`
- **Verification:** All 22 assets exist in Git. Remote HTTP `HEAD` checks verified every URL returns `HTTP 200` with `Content-Type: image/png`.

### Phase 4: CLI Version Mismatch

- **Root Cause:** In earlier milestones (M6), `src/healthcare_agents/__init__.py` declared `__version__ = "0.6.0"`. `healthcare_agents.cli:build_parser` called:
  ```python
  from healthcare_agents import __version__

  parser.add_argument("--version", action="version", version=f"healthcare-agents {__version__}")
  ```
  While `pyproject.toml` was properly bumped to `0.10.0` in M10, `__init__.py` retained the hardcoded `0.6.0`.
- **Resolution:** Updated `src/healthcare_agents/__init__.py` to resolve version dynamically:
  ```python
  from importlib.metadata import PackageNotFoundError, version

  try:
      __version__ = version("open-healthcare-agentic-platform")
  except PackageNotFoundError:
      try:
          __version__ = version("healthcare-agents")
      except PackageNotFoundError:
          __version__ = "0.10.0"
  ```
  Updated `src/healthcare_agents/observability/config.py` to import `__version__` from `healthcare_agents`.
- **Verification:** Fresh wheel installation in a clean outside virtual environment reports:
  ```text
  $ healthcare-agents --version
  healthcare-agents 0.10.1
  ```

### Phase 5: GHCR Public Access Verification

Direct unauthenticated anonymous token exchanges against `ghcr.io` confirmed:
1. `ghcr.io/hastimal/open-healthcare-api:0.10.0` $\rightarrow$ `HTTP 200` (Public Multi-Arch OCI Index)
2. `ghcr.io/hastimal/open-healthcare-ui:0.10.0` $\rightarrow$ `HTTP 200` (Public Multi-Arch OCI Index)
3. `oci://ghcr.io/hastimal/charts/open-healthcare:0.10.0` $\rightarrow$ `HTTP 200` (Public OCI Helm Chart Manifest)

No authentication credentials were used, confirming that all three GHCR packages are publicly accessible without authentication.
Furthermore, checked `0.10.1` tags across PyPI and GHCR to confirm no conflicting artifacts exist:
- PyPI `0.10.1`: `HTTP 404` (not yet published)
- GHCR `open-healthcare-api:0.10.1`: `HTTP 404` (not yet published)
- GHCR `open-healthcare-ui:0.10.1`: `HTTP 404` (not yet published)
- GHCR `charts/open-healthcare:0.10.1`: `HTTP 404` (not yet published)

---

## 3. Automated Validation & Quality Gates

### Automated README Image Tests (`tests/test_readme_images.py`)
1. `test_all_local_images_exist_in_git`: Confirms all 22 referenced image files exist on disk in `docs/images/`.
2. `test_readme_contains_no_relative_image_paths`: Enforces that no relative `docs/images/*.png` links remain in `README.md`.
3. `test_remote_raw_github_image_urls_return_http_200` (`@pytest.mark.live`): Performs live HTTP requests verifying all raw URLs respond with HTTP 200 and image mime-types.

### Test Results Summary
- **Ruff Lint:** `uv run ruff check .` $\rightarrow$ `All checks passed!`
- **Ruff Format:** `uv run ruff format --check .` $\rightarrow$ `178 files already formatted`
- **Mypy Type Check:** `uv run mypy src tests` $\rightarrow$ `Success: no issues found in 82 source files`
- **Unit & Integration Tests:** `uv run pytest -m "not live"` $\rightarrow$ `206 passed, 15 skipped, 1 deselected, 1 warning in 118s`
- **Code Coverage:** **90.16%** ($\ge 90.0\%$ threshold maintained)
- **Helm Lint:** `helm lint charts/open-healthcare` $\rightarrow$ `0 chart(s) failed`
- **Helm Template:** `helm template test charts/open-healthcare` $\rightarrow$ Valid Kubernetes manifests referencing `0.10.1` images
- **Release Tag Mapping:** `tests/test_release_tag_mapping.py` $\rightarrow$ 3 passed (verified `v0.10.0-m10` $\rightarrow$ `0.10.0` and `v0.10.1-m10.1` $\rightarrow$ `0.10.1`)
- **Package Metadata:** `twine check dist/*` $\rightarrow$ `PASSED` for both wheel and sdist

---

## 4. Release Safety & Workflow Triggers

All three publishing workflows trigger automatically upon `release: [published]`:
1. `.github/workflows/publish-pypi.yml`: Builds package and publishes to PyPI using OIDC Trusted Publishing.
2. `.github/workflows/publish-containers.yml`: Builds multi-arch AMD64/ARM64 container images and pushes `0.10.1` & `0.10` tags to GHCR.
3. `.github/workflows/publish-helm-chart.yml`: Packages chart version `0.10.1` and pushes OCI artifact to `oci://ghcr.io/hastimal/charts/open-healthcare:0.10.1`.

### Failure Recovery Procedures

1. **PyPI Publication Failure:**
   - Check GitHub environment `pypi` logs.
   - If network glitch occurs, trigger manually via `workflow_dispatch` (`publish=true`) after addressing the transient failure.
   - If version `0.10.1` was already partially uploaded, PyPI forbids re-uploading the same version; bump to `0.10.2`.
2. **GHCR Container Publication Failure:**
   - Inspect GitHub Actions job logs for buildx or Trivy errors.
   - Re-run the failed workflow directly or via `workflow_dispatch` (`publish=true`).
3. **Helm OCI Publication Failure:**
   - Check if GHCR authentication or tag alignment failed.
   - Fix any discrepancy and trigger the pipeline via `workflow_dispatch` (`publish=true`).
4. **Private GHCR Package Recovery:**
   - If GHCR packages revert to private visibility, navigate to GitHub Profile $\rightarrow$ Packages $\rightarrow$ `Package Settings` $\rightarrow$ `Danger Zone` $\rightarrow$ `Change visibility` $\rightarrow$ `Public`.

---

## 5. Next Steps for Release (Upon Approval)

1. Review and merge PR targeting `main`.
2. Create annotated tag:
   ```bash
   git checkout main && git pull origin main
   git tag -a v0.10.1-m10.1 -m "Release v0.10.1-m10.1: Fix broken PyPI README images and CLI version reporting"
   git push origin v0.10.1-m10.1
   ```
3. Publish GitHub Release `v0.10.1-m10.1` pointing to `v0.10.1-m10.1`.
4. Monitor and verify all three automated publishing pipelines (PyPI, GHCR containers, Helm OCI).

