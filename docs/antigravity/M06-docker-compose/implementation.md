# Milestone M6 Implementation: Docker Compose Containerization

## Architectural Overview

Milestone M6 introduces production-oriented containerization for the entire Open Healthcare Agentic Platform, supporting dual deployment profiles:
1. **Profile A (Recommended Apple Silicon Development Profile)**:
   - Containerized FastAPI Gateway (`open-healthcare-api:latest`) and Streamlit UI (`open-healthcare-ui:latest`).
   - Connects to native macOS host Ollama via `host.docker.internal:11434`.
   - Utilizes Apple Silicon unified memory and Metal GPU hardware acceleration with full `gemma4:e2b` and `gemma4:12b` performance.
2. **Profile B (Fully Containerized Demonstration Profile)**:
   - Runs all services in Docker containers (`api`, `ui`, and `ollama`), plus an automated model bootstrapper container (`ollama-bootstrap`).
   - Uses persistent named volume `open-healthcare-ollama-models` to retain model files across lifecycle teardowns.
   - Operates with CPU-only inference inside Linux Docker containers on macOS (documenting CPU latency characteristics).

```
+---------------------------------------------------------------------------------------------------+
|                                 Milestone M6 Container Architecture                               |
+---------------------------------------------------------------------------------------------------+
|  1. Streamlit Interactive Web Application Container (`Dockerfile.ui`)                            |
|     • Base: python:3.12-slim-bookworm (Multi-stage build, unprivileged user 10001:appgroup)       |
|     • Size: ~198 MB runtime image                                                                 |
|     • Exposed Port: 8501                                                                          |
|     • Internal Healthcheck: curl -f http://localhost:8501/_stcore/health                          |
|     • Service DNS Ingress: http://api:8000                                                        |
|                                                                                                   |
|  2. FastAPI Gateway & Search Service Container (`Dockerfile.api`)                                 |
|     • Base: python:3.12-slim-bookworm (Multi-stage build, unprivileged user 10001:appgroup)       |
|     • Size: ~198 MB runtime image                                                                 |
|     • Exposed Port: 8000                                                                          |
|     • Internal Healthcheck: curl -f http://localhost:8000/health                                  |
|     • Deep Readiness: /ready (probes model availability and all 4 federal endpoints)              |
|                                                                                                   |
|  3. Model Serving Layer (Dual Execution Profiles)                                                 |
|     • Profile A (Default): Host Ollama via host.docker.internal:11434 (Apple Silicon Metal GPU)   |
|     • Profile B (--profile container-ollama): ollama/ollama:latest container with persistent       |
|       named volume `open-healthcare-ollama-models` and `scripts/bootstrap_model.sh`               |
|                                                                                                   |
|  4. Security, Isolation, & Cleanliness Standards                                                  |
|     • Strict .dockerignore excluding .git, .env, caches, virtualenvs, and model weights           |
|     • Zero credentials, PHI, or local machine host paths embedded in container images             |
|     • Explicit bridge network `open-healthcare-network` with DNS resolution                       |
+---------------------------------------------------------------------------------------------------+
```

## Key Files Created and Modified

### Created Files
- `Dockerfile.api`: Production multi-stage Dockerfile for FastAPI gateway.
- `Dockerfile.ui`: Production multi-stage Dockerfile for Streamlit web application.
- `.dockerignore`: Exclusion rules for Git history, virtualenvs, local caches, wheels, and model weights.
- `docker-compose.yml`: Multi-profile Compose configuration for API, UI, containerized Ollama, and model bootstrapper.
- `scripts/bootstrap_model.sh`: Automated model pull and readiness verification script for containerized Ollama.
- `tests/test_docker.py`: Unit and configuration tests for Dockerfiles, Compose specs, container environment variables, and readiness edge cases.
- `docs/images/m6_workflow.svg` & `docs/images/m6_workflow.png`: System container architecture diagram.
- `docs/images/m6_container_ui.png`: Playwright browser screenshot of the live containerized Streamlit UI.
- `docs/images/m6_container_results.png`: Playwright browser screenshot of live multi-agent search results in container.

### Modified Files
- `pyproject.toml`: Bumped version to `0.6.0`.
- `src/healthcare_agents/__init__.py`: Bumped `__version__ = "0.6.0"`.
- `src/healthcare_agents/config.py`: Added support for `OLLAMA_MODEL` environment variable alias.
- `src/healthcare_agents/ui/app.py`: Added support for `API_BASE_URL` environment variable alias.
- `.env.example`: Documented Docker Compose port mappings, host vs container networking, and profile options.
- `tests/test_package.py` & `tests/test_cli.py`: Updated version assertions to `0.6.0`.
