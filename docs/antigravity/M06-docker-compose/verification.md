# Verification & Quality Gate Results: Milestone M6

## 1. Test Suite & Coverage Metrics

Full test suite execution passed with zero errors:

```text
================================ tests coverage ================================
TOTAL: 2956 Stmts, 267 Miss, 91% (Actual: 90.97%)
Required test coverage of 90.0% reached. Total coverage: 90.97%
=========================== short test summary info ============================
141 passed, 15 skipped, 1 warning in 51.74s
```

All 8 new Docker containerization and environment tests in `tests/test_docker.py` passed:
- `test_dockerfile_api_structure`
- `test_dockerfile_ui_structure`
- `test_dockerignore_excludes_sensitive_and_ephemeral_files`
- `test_docker_compose_config_validity`
- `test_container_environment_variable_resolution`
- `test_readiness_model_unavailable_scenario`
- `test_backend_unavailable_handling`
- `test_bootstrap_script_attributes`

## 2. Static Analysis & Type Checking

- **Ruff Linter**:
  ```bash
  uv run ruff check .
  # All checks passed!
  ```
- **Ruff Formatter**:
  ```bash
  uv run ruff format --check .
  # 116 files already formatted
  ```
- **Mypy Strict Type Checking**:
  ```bash
  uv run mypy src tests
  # Success: no issues found in 63 source files
  ```

## 3. Package Build & Wheel Clean Installation

```bash
uv build
# Successfully built dist/healthcare_agents-0.6.0.tar.gz
# Successfully built dist/healthcare_agents-0.6.0-py3-none-any.whl
```

## 4. Container Health & Readiness Verification

- **FastAPI Container Liveness (`http://localhost:8000/health`)**:
  - Status: 200 OK
  - Response: `{"status":"healthy","version":"0.6.0","environment":"development","timestamp":"2026-10-25T14:11:39.883699+00:00"}`
- **FastAPI Container Readiness (`http://localhost:8000/ready`)**:
  - Status: 200 OK
  - Probed: Ollama service online (`http://host.docker.internal:11434`), model `gemma4:e2b` verified, four federal sources configured.
- **Streamlit Container Health (`http://localhost:8501/_stcore/health`)**:
  - Status: 200 OK (`ok`)
- **Docker Compose Status**: Both `open-healthcare-api` and `open-healthcare-ui` reported `Up (healthy)`.

## 5. End-to-End Query Execution & Model Inference in Container

1. **Fixture Mode Multi-Agent Query**:
   - Dispatched `Find pediatric dentists in Houston and research on pediatric dental anxiety` via HTTP POST to container.
   - Result: Successful LangGraph multi-agent execution with grounded narrative and 5 unified evidence records.
2. **Live 4-Source Healthcare Query**:
   - Dispatched live query to container, querying public CMS NPPES, NCBI PubMed, CMS Provider Data, and NLM MedlinePlus APIs from within the Linux container network.
   - Result: Successful retrieval across all four sources, NPI format validation, and grounded narrative synthesis with 13 unified evidence items.
3. **Container Restart & Recovery**:
   - Ran `docker compose restart`.
   - Verified clean recovery and transition back to `healthy` state within 7 seconds.

## 6. Playwright Browser Automation & UI Screenshots

- Captured initial container UI: `docs/images/m6_container_ui.png`.
- Automated search submission via browser button click and captured discovery results: `docs/images/m6_container_results.png`.

## 7. Container Profile Verification (Apple Silicon vs Full Container)

- **Profile A (Recommended Host Ollama)**:
  - Docker containers connected seamlessly to native host Ollama via `host.docker.internal:11434`.
  - Full Apple Silicon Metal GPU acceleration and sub-second token generation observed.
- **Profile B (Containerized Ollama)**:
  - Official `ollama/ollama:latest` container started on port 11435.
  - Persistent volume `open-healthcare-ollama-models` verified.
  - Documented limitation: CPU-only inference in Linux containers on macOS exhibits significantly higher latency compared to native host execution.
