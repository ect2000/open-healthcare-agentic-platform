# Milestone M10.2: Public Release v0.10.2 Verification & Report

## Executive Summary
This document records the official verification and artifact inventory for **Milestone M10.2 (Final Release v0.10.2)** of the Open Healthcare Agentic Platform.

- **Release Date**: October 26, 2026
- **Release Version**: `0.10.2`
- **Release Tag**: `v0.10.2-m10.2` (Annotated Git Tag: `9265f2a1b9b18d2d6655c2f8df41bb5271eb5219`)
- **Tagged Commit (`main`)**: `cf3fafd0b8fbcde34dceb3c4becce9fdd55e7817`
- **GitHub Release URL**: [https://github.com/hastimal/open-healthcare-agentic-platform/releases/tag/v0.10.2-m10.2](https://github.com/hastimal/open-healthcare-agentic-platform/releases/tag/v0.10.2-m10.2)
- **PyPI URL**: [https://pypi.org/project/open-healthcare-agentic-platform/0.10.2/](https://pypi.org/project/open-healthcare-agentic-platform/0.10.2/)
- **GHCR API Image**: `ghcr.io/hastimal/open-healthcare-api:0.10.2`
- **GHCR UI Image**: `ghcr.io/hastimal/open-healthcare-ui:0.10.2`
- **Helm OCI Chart**: `oci://ghcr.io/hastimal/charts/open-healthcare:0.10.2`

---

## 1. Merged Pull Requests Verification

| PR | Title | State | Merged At | Merge Commit SHA |
| :--- | :--- | :---: | :---: | :--- |
| **#32** | M10.2 CNCF Documentation Overhaul | `MERGED` | 2026-10-26T12:51:45Z | `c82f8a957b98954639e74b420db70980ce096032` |
| **#33** | chore(release): prepare v0.10.2 release with complete CNCF documentation | `MERGED` | 2026-10-26T14:01:19Z | `cf3fafd0b8fbcde34dceb3c4becce9fdd55e7817` |

---

## 2. Release Workflows & CI Audit

| Workflow | Run ID | Event | Elapsed | Conclusion | URL |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Helm OCI Packaging & GHCR Publishing Pipeline** | `40341628012` | `release` | 10s | `success` | [Run 40341628012](https://github.com/hastimal/open-healthcare-agentic-platform/actions/runs/40341628012) |
| **Publish Python Package to PyPI** | `40341628131` | `release` | 44s | `success` | [Run 40341628131](https://github.com/hastimal/open-healthcare-agentic-platform/actions/runs/40341628131) |
| **Multi-Arch Container Build & GHCR Pipeline** | `40341628475` | `release` | 9m11s | `success` | [Run 40341628475](https://github.com/hastimal/open-healthcare-agentic-platform/actions/runs/40341628475) |

---

## 3. Public Artifact Inventory & Acceptance Matrix

| Artifact | Version | Reference / URL | Digest / Details | Public | Verified Command | Result |
| :--- | :---: | :--- | :--- | :---: | :--- | :---: |
| **GitHub Release** | `0.10.2` | `https://github.com/hastimal/open-healthcare-agentic-platform/releases/tag/v0.10.2-m10.2` | Tag: `v0.10.2-m10.2` | YES | `gh release view v0.10.2-m10.2` | **PASS** |
| **PyPI Wheel** | `0.10.2` | `https://pypi.org/project/open-healthcare-agentic-platform/0.10.2/` | `open_healthcare_agentic_platform-0.10.2-py3-none-any.whl` (120,313 B) | YES | `curl -s https://pypi.org/pypi/.../json` | **PASS** |
| **PyPI Source Distribution** | `0.10.2` | `https://pypi.org/project/open-healthcare-agentic-platform/0.10.2/` | `open_healthcare_agentic_platform-0.10.2.tar.gz` (93,101 B) | YES | `curl -s https://pypi.org/pypi/.../json` | **PASS** |
| **GHCR API Image (Index)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-api:0.10.2` | Multi-arch OCI Image Index | YES | `docker manifest inspect ...` | **PASS** |
| **GHCR API (AMD64)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-api:0.10.2` | `sha256:670e1c266ee1a4e4cbde8c0d0f1fc8c7226c832e7f8a4335e2a9544448865931` | YES | `docker manifest inspect ...` | **PASS** |
| **GHCR API (ARM64)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-api:0.10.2` | `sha256:6ba3d0c7fd970f6d511a5189e70090381f5b053bf551b8f451f58a165e6abe9c` | YES | `docker manifest inspect ...` | **PASS** |
| **GHCR UI Image (Index)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-ui:0.10.2` | Multi-arch OCI Image Index | YES | `docker manifest inspect ...` | **PASS** |
| **GHCR UI (AMD64)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-ui:0.10.2` | `sha256:4d7a98c09fdf02d18b79e3da313509b5a489c75d8ec4347fa70e2de4e2f9e786` | YES | `docker manifest inspect ...` | **PASS** |
| **GHCR UI (ARM64)** | `0.10.2` | `ghcr.io/hastimal/open-healthcare-ui:0.10.2` | `sha256:11738d62492cbb30e8f43b88f75783d7b478b27096965993f61d1e58fb2c26b9` | YES | `docker manifest inspect ...` | **PASS** |
| **Helm OCI Chart** | `0.10.2` | `oci://ghcr.io/hastimal/charts/open-healthcare:0.10.2` | `sha256:6cbb213cd74d2190c8b155078c8be8f9c9bdcad2789ea671e3d1a7b94536bb48` | YES | `helm pull ... --version 0.10.2` | **PASS** |
| **Python CLI via uvx** | `0.10.2` | CLI command `healthcare-agents` | Isolated run outside repository | YES | `uvx --from ... healthcare-agents --version` | **PASS** |

---

## 4. Quality Gates & Test Results

1. **Ruff Linter & Formatter**:
   - `uv run ruff check .` passed with 0 errors.
   - `uv run ruff format --check .` passed with 210 files formatted.
2. **Mypy Static Typing**:
   - `uv run mypy src tests` passed with 0 errors across 83 source files.
3. **Automated Pytest Suite**:
   - Executed `uv run pytest -m "not live"`: **210 passed, 15 skipped (live), 0 failures**.
   - Coverage: **90.09%** ($\ge 90.0\%$ gate requirement satisfied).
4. **Helm Validation**:
   - `helm lint charts/open-healthcare` passed (0 charts failed).
   - `helm template test charts/open-healthcare` cleanly rendered Kubernetes manifests.
5. **Twine Metadata**:
   - `twine check dist/*` verified both wheel and sdist distributions.
   - Wheel `METADATA` contains dedicated PyPI README content without broken relative markdown paths.
6. **Docker Pull & Run**:
   - Verified multi-arch pull of both `ghcr.io/hastimal/open-healthcare-api:0.10.2` and `ghcr.io/hastimal/open-healthcare-ui:0.10.2`.
   - Verified `--entrypoint healthcare-agents --version` returns `healthcare-agents 0.10.2`.
