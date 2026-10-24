# Milestone M01: Instructions & Requirements

## Project Goal
Build a vendor-neutral, open-source, evidence-grounded healthcare search and agentic AI platform using Python, Gemma 4, Ollama, LangGraph, MCP, Docker, Kubernetes, vLLM, and OpenTelemetry.

The platform will eventually integrate four public healthcare data sources:
1. NPPES — healthcare provider discovery
2. PubMed — biomedical research
3. CMS Provider Data — clinician and facility information
4. MedlinePlus — trusted patient education

## Target Milestone
- **Milestone**: M1 — Repository Foundation, Python & CI
- **Target Tag**: `v0.1.0-m01`
- **Scope Restriction**: Only implement repository foundation, Python packaging, CLI, configuration scaffolding, tests, and CI. Do NOT implement Gemma 4 inference, LangGraph agents, MCP integrations, APIs, Streamlit, Docker, or Kubernetes in M1.

## Required Steps
1. **Inspect Existing Repository**:
   - Verify Git branch, remote, and tree.
   - Inspect existing files before changing anything.
   - Preserve existing LICENSE and README content.
2. **Python Project Foundation**:
   - Target Python 3.12+.
   - Use `src`-layout packaging convention.
   - Create `pyproject.toml` with Hatchling PEP 517 build backend.
   - Package name: `healthcare_agents`.
   - CLI entrypoint: `healthcare-agents` with `--version` and `health`/`status` command.
   - Minimal dependencies.
3. **Comprehensive .gitignore**:
   - Python caches, build artifacts, venv, secrets (`.env*`, `*.pem`, `*.key`), IDE files, logs, models/checkpoints (`*.gguf`, `*.safetensors`).
   - Keep `.env.example` tracked.
4. **Configuration Scaffolding**:
   - Create `src/healthcare_agents/config.py` with standard environment variables.
   - Safe defaults for non-secret settings.
   - Documented `.env.example` with future placeholders (`MODEL_PROVIDER=ollama`, `MODEL_NAME=gemma:4b`, `OLLAMA_BASE_URL=http://localhost:11434`).
   - Do not connect to Ollama yet.
5. **Code Quality**:
   - Configure pytest, pytest-cov, Ruff, and mypy in `pyproject.toml`.
   - Strict typing and docstrings.
6. **Automated Tests**:
   - Tests for package imports, version, CLI behavior, defaults, overrides, and invalid config.
   - Offline only (no network or secrets).
7. **GitHub Actions CI**:
   - `.github/workflows/ci.yml` running on Python 3.12 for push and PR.
   - Run Ruff, mypy, pytest, build, and package install check.
   - Least privilege permissions.
8. **Documentation**:
   - README, CONTRIBUTING, SECURITY, LICENSE.
   - Target architecture documentation with Mermaid diagram under `docs/architecture/README.md`.
   - Milestone report.
9. **Validation & Release**:
   - Execute tests, build wheel, test in clean venv.
   - Commit, tag `v0.1.0-m01`, push to remote, and verify GitHub Actions CI.
