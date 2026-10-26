# M10-3: One-Command PyPI Installation and Launcher

> **Tracking:** Issue #21 (Epic #18)  
> **Status:** Implemented & Verified  
> **Distribution Target:** `open-healthcare-agentic-platform` (`healthcare-agents`)

---

## 1. Overview & Objective

The objective of Issue #21 is to enable developers, clinicians, and researchers to install and run the Open Healthcare Agentic Platform via a modern one-command execution flow without needing to manually clone the Git repository:

```bash
uvx open-healthcare-agentic-platform
```

Or via standard installation:
```bash
pip install open-healthcare-agentic-platform
healthcare-agents check
healthcare-agents start
```

---

## 2. CLI Commands Implemented

| Command | Description |
|:---|:---|
| `healthcare-agents --help` | Show command overview, available flags, and subcommands. |
| `healthcare-agents --version` | Output current platform version. |
| `healthcare-agents check` | Run local preflight diagnostic checks (Python $\ge 3.12$, ports 8000/8501, Ollama endpoint, Gemma 4 model, Docker). |
| `healthcare-agents start` (alias: `run`) | Start FastAPI backend and Streamlit UI in Native mode with automated readiness polling and clean PID tracking. |
| `healthcare-agents stop` | Safely terminate platform processes launched and tracked by the CLI instance without affecting unrelated system processes. |
| `healthcare-agents status` | Inspect runtime port occupancy and active managed PIDs. |
| `healthcare-agents demo` | One-command launcher executing preflight diagnostics and launching the interactive platform. |
| `healthcare-agents` (bare invocation) | Default one-command entrypoint for `uvx open-healthcare-agentic-platform` that runs diagnostics and launches native services. |

---

## 3. Package Structure & PyPI Readiness

- **Package Distribution Name:** `open-healthcare-agentic-platform`
- **CLI Executable Names:** `healthcare-agents` and `open-healthcare-agentic-platform`
- **PyPI Name Availability:** Checked against PyPI JSON API (`https://pypi.org/pypi/open-healthcare-agentic-platform/json`) &rarr; HTTP 404 (Name is confirmed available).
- **Self-Contained Wheel:** The wheel builds with `hatchling` and bundles all modules under `healthcare_agents.*` (including Streamlit app at `healthcare_agents.ui.app`). It does not require Git clone artifacts or relative repository path assumptions.

---

## 4. Verification & Quality Gates

### A. Code Standards & Linting
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```
- **Ruff:** 172 files checked, 0 errors, all formatted.
- **Mypy:** 80 source files checked, 0 errors.

### B. Unit & Integration Test Suite
```bash
uv run pytest -m "not live" --cov=healthcare_agents --cov-report=term-missing
```
- **Passed:** 201 passed, 15 skipped (live tests disabled by default), 0 failed.
- **Coverage:** **90.26%** (exceeds the 90.0% requirement).

### C. Isolated Wheel Installation & Execution
```bash
uv build
uv pip install --python /tmp/test-cli-env/bin/python dist/open_healthcare_agentic_platform-0.10.0-py3-none-any.whl
/tmp/test-cli-env/bin/healthcare-agents --help
/tmp/test-cli-env/bin/healthcare-agents --version
/tmp/test-cli-env/bin/healthcare-agents check --api-port 9000 --ui-port 9501
```
- All commands execute cleanly outside the repository directory.

### D. Playwright Browser Acceptance
- Started native services on ports 9000 & 9501 using the installed wheel binary.
- Executed headless Playwright session:
  - Verified Streamlit UI title: `Open Healthcare Agentic Platform`.
  - Verified demonstration presets present and interactive.
  - Selected Preset 1 ("1. Pediatric Dentist Discovery").
  - Triggered multi-agent search workflow.
  - Verified grounded evidence returned with federal citations.
- Ran `healthcare-agents stop`: verified child processes (PIDs 38001 and 38002) were cleanly terminated and ports 9000 and 9501 freed.

---

## 5. Distinction: Available Now vs. After Release

- **AVAILABLE NOW:**
  - Installation from source: `pip install .` or `uv pip install -e .`
  - Installation from local wheel: `pip install dist/open_healthcare_agentic_platform-0.10.0-py3-none-any.whl`
  - Local `uvx` testing: `uvx --from ./dist/open_healthcare_agentic_platform-0.10.0-py3-none-any.whl open-healthcare-agentic-platform`
- **AVAILABLE AFTER M10 RELEASE:**
  - Direct zero-install execution from public PyPI:
    ```bash
    uvx open-healthcare-agentic-platform
    ```
