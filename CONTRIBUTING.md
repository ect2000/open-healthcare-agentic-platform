# Contributing to Open Healthcare Agentic Platform

Thank you for your interest in contributing to the **Open Healthcare Agentic Platform**! We welcome contributions from developers, clinicians, researchers, and open-source advocates.

---

## 1. Project Purpose & Architecture

The Open Healthcare Agentic Platform is a vendor-neutral, evidence-grounded healthcare search and agentic AI platform. It combines open-weight models (Gemma 4 via native Ollama) with multi-agent orchestration (LangGraph), public authoritative data sources (NPPES, PubMed, MedlinePlus, CMS), and full-stack observability (OpenTelemetry, Prometheus, Grafana Tempo, Grafana).

### Core Principles
- **Evidence-Grounded**: Every factual claim must be backed by verifiable citations from authoritative public registries.
- **Vendor-Neutral**: Built on open standards (OpenTelemetry, W3C TraceContext, Prometheus, Docker, Kubernetes) without proprietary cloud lock-in.
- **Fail-Safe & Privacy-First**: OpenTelemetry failures never interrupt clinical discovery; Protected Health Information (PHI) and raw queries are never exported to telemetry.
- **Preserve Existing Milestones**: New contributions must preserve all completed M1–M8 functionality without regressions.

---

## 2. Development Prerequisites

- **Python**: 3.12 or newer
- **uv**: Fast Python package manager ([docs.astral.sh/uv](https://docs.astral.sh/uv/))
- **Docker & Docker Compose**: Docker Desktop (or engine) active for containerized stacks
- **Ollama**: Running natively on the host workstation (`localhost:11434`)
- **Gemma 4**: Pulled and available locally:
  ```bash
  ollama pull gemma4:e2b
  ```

---

## 3. Local Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hastimal/open-healthcare-agentic-platform.git
   cd open-healthcare-agentic-platform
   ```

2. **Sync virtual environment & dependencies using `uv`:**
   ```bash
   uv sync
   ```

3. **Configure environment settings:**
   ```bash
   cp .env.example .env
   ```

---

## 4. One-Command Demonstration & Local Stack

The platform includes a permanent, unified developer launcher that verifies Docker, tests native Ollama connectivity, checks model installation, starts the containerized stack, verifies service health, and opens the application in your browser:

```bash
uv run python scripts/run_demo.py
```

### Headless or Automated Environments:
```bash
uv run python scripts/run_demo.py --no-browser
```

### Local Service Ports & Endpoints:
- **Streamlit Web UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Gateway & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana Dashboards**: [http://localhost:3000/d/healthcare-observability](http://localhost:3000/d/healthcare-observability)
- **Prometheus Metrics Engine**: [http://localhost:9090](http://localhost:9090)
- **Grafana Tempo Trace Explorer**: [http://localhost:3000/explore](http://localhost:3000/explore)
- **OpenTelemetry Collector**: `localhost:4318` (HTTP), `localhost:4317` (gRPC)

---

## 5. Code Quality Requirements & Running Tests

All contributions must pass strict quality gates before being accepted.

### Quality Checks
```bash
# 1. Linting
uv run ruff check .

# 2. Formatting verification
uv run ruff format --check .

# 3. Static type checking (strict mode)
uv run mypy src tests

# 4. Full pytest suite with code coverage (Target: >=90%)
uv run pytest --cov=healthcare_agents --cov-report=term-missing
```

### Auto-formatting Code:
```bash
uv run ruff check --fix .
uv run ruff format .
```

---

## 6. How to Find Contributor-Friendly Issues

Check the repository [Issues page](https://github.com/hastimal/open-healthcare-agentic-platform/issues) to find open tasks:
- **`good first issue`**: Well-defined, self-contained tasks ideal for newcomers (e.g., developer experience improvements, documentation guides).
- **`help wanted`**: Important features and enhancements seeking community contributions (e.g., Kubernetes manifests, performance benchmarks, evaluation frameworks).

---

## 7. Branch Naming & Pull Request Process

1. **Branch Naming**:
   - Features: `feature/<issue-number>-<short-description>` (e.g. `feature/12-developer-diagnostics`)
   - Bugfixes: `fix/<issue-number>-<short-description>`
   - Documentation: `docs/<short-description>`

2. **Commit Conventions**:
   Use conventional commits:
   - `feat(...)`: New feature or capability
   - `fix(...)`: Bug fix
   - `docs(...)`: Documentation changes
   - `test(...)`: Adding or updating tests
   - `refactor(...)`: Code changes that neither fix a bug nor add a feature

3. **Submitting a Pull Request**:
   - Ensure all quality checks and tests pass locally.
   - Fill out all sections of the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).
   - Link the relevant issue (e.g., `Closes #12`).
   - Include updated screenshots if UI changes were introduced.
   - Wait for automated GitHub Actions CI to pass.
