PROJECT: open-healthcare-agentic-platform

MILESTONE: M6 — Docker Compose Containerization
TARGET VERSION: 0.6.0
TARGET TAG: v0.6.0-m06
BRANCH: main ONLY

Read AGENTS.md and all M1–M5 milestone documentation.

OBJECTIVE
Containerize the existing FastAPI + Streamlit +
LangGraph healthcare discovery application.

Support two execution profiles:

A. Recommended Apple Silicon development profile:
   Dockerized API + Streamlit with native host Ollama.

B. Fully containerized demonstration profile:
   Dockerized API + Streamlit + Ollama.

Do not assume macOS Docker Desktop provides
GPU acceleration to Linux Ollama containers.

Preserve all existing functionality.

Do not start M7, Kubernetes, Helm or vLLM.

==================================================
1. BASELINE VERIFICATION
==================================================

Verify:
- main branch
- clean working tree
- tag v0.5.0-m05
- successful baseline tests
- existing CLI, API and Streamlit functionality

Inspect Docker Desktop status.

Do not delete Docker volumes or reset Docker
Desktop without explicit user approval.

==================================================
2. DOCKERFILES
==================================================

Create production-oriented Dockerfiles for:

- FastAPI backend
- Streamlit frontend

Requirements:
- Python runtime compatible with pyproject.toml
- Reproducible dependency installation
- Multi-stage builds where beneficial
- Non-root application user
- Minimal runtime dependencies
- Health checks
- Correct signal handling
- No development credentials in images
- No model weights embedded in images
- No PHI or local machine paths
- .dockerignore excluding secrets, caches,
  virtual environments and build artifacts

Ensure the Python package installs correctly.

==================================================
3. DOCKER COMPOSE
==================================================

Create a Compose configuration supporting:

API service:
- Internal port 8000
- Configurable host port
- Health/readiness checks
- Connection to Ollama
- Public healthcare API access

Streamlit service:
- Internal port 8501
- Configurable host port
- Backend API address via environment variable
- Health check
- Correct service dependencies

Ollama service:
- Optional Compose profile
- Persistent named volume for model files
- Model bootstrap instructions
- Explicit CPU resource considerations

Use Docker Compose service DNS names
rather than localhost for container-to-container
communication.

Never hardcode host-specific paths.

==================================================
4. APPLE SILICON OLLAMA SUPPORT
==================================================

For the recommended macOS profile:

- Run Ollama natively on the host.
- Run FastAPI and Streamlit in Docker.
- Use host.docker.internal to reach host Ollama.
- Verify Ollama binds to an interface reachable
  from Docker without exposing it unnecessarily
  to the public network.
- Preserve existing gemma4:e2b configuration.

For the fully containerized profile:

- Use the official Ollama container image.
- Mount persistent model storage.
- Provide an explicit model pull/bootstrap step.
- Wait until the model is actually available.
- Do not claim the container is ready merely
  because the Ollama HTTP service responds.

Test both profiles where the environment permits.

If CPU inference is too slow for a practical demo,
document the limitation accurately.

==================================================
5. ENVIRONMENT CONFIGURATION
==================================================

Update .env.example.

Support:
- RETRIEVAL_MODE
- OLLAMA_BASE_URL
- OLLAMA_MODEL
- API_BASE_URL
- API_PORT
- STREAMLIT_PORT
- Request timeout settings
- Healthcare API configuration

Use safe defaults.

Never commit real secrets.

Document host versus container networking.

==================================================
6. HEALTH AND READINESS
==================================================

Implement or preserve:

FastAPI:
- /health
- /ready

Streamlit:
- /_stcore/health

Ollama:
- API availability check
- Required model availability check

Clearly distinguish:
- Process alive
- Service ready
- Model ready
- External source available

Use bounded retries and startup timeouts.

Do not create infinite wait loops.

==================================================
7. END-TO-END CONTAINER TESTING
==================================================

Test:

1. Build both application images.
2. Start services using Compose.
3. Confirm healthy containers.
4. Open Streamlit in browser.
5. Execute fixture-mode healthcare query.
6. Confirm Streamlit calls FastAPI.
7. Confirm API calls LangGraph.
8. Confirm LangGraph calls Ollama.
9. Verify evidence cards and citations.
10. Execute real live healthcare query.
11. Verify NPPES, PubMed, CMS, MedlinePlus.
12. Confirm missing CMS data is not interpreted
    as poor provider quality.
13. Verify source failures are visible.
14. Restart containers.
15. Confirm application recovers.
16. Confirm existing model storage persists.

Use Playwright to test the actual browser UI.

Capture real screenshots.

Do not use mock screenshots as evidence.

==================================================
8. AUTOMATED TESTS
==================================================

Add tests for:
- Dockerfile configuration
- Compose configuration
- Environment variable handling
- Container networking
- API readiness
- Streamlit readiness
- Ollama readiness
- Model unavailable
- Backend unavailable
- Restart behavior
- Source failure reporting
- Existing M1–M5 regressions

Use mocked dependencies for offline CI.

Add opt-in Docker integration tests.

Maintain >=90% Python code coverage.

Do not include Docker tests as passing if
Docker is unavailable or tests are skipped.

==================================================
9. DOCUMENTATION
==================================================

Create:

docs/antigravity/M06-docker-compose/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save this complete prompt in prompt.md.

Create:
docs/milestones/M06-docker-compose.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md
.env.example

Create:
docs/images/m6_workflow.png

Use polished M4A–M5 diagram style.

Preserve editable source.
Embed PNG in README.

Include actual Docker and Streamlit screenshots.

Document:
- Apple Silicon setup
- Host Ollama profile
- Container Ollama profile
- CPU limitations
- Port configuration
- Model bootstrap
- Troubleshooting
- Container health checks
- Exact commands used

==================================================
10. QUALITY GATES
==================================================

Run:
- pytest >=90% coverage
- Ruff lint
- Ruff formatting
- mypy strict
- Package build
- Clean wheel installation
- Docker image builds
- Docker Compose config validation
- Container startup
- Health/readiness checks
- Fixture-mode end-to-end tests
- Live healthcare retrieval
- Real Gemma 4 inference
- Browser acceptance testing

Do not report unexecuted tests as passed.

==================================================
11. GIT AND RELEASE
==================================================

Work on main only.

After all required checks pass:

1. Review git diff.
2. Verify no secrets, PHI or model weights.
3. Commit verified changes.
4. Push main.
5. Wait for successful GitHub Actions CI.
6. Create annotated tag v0.6.0-m06.
7. Push tag.
8. Verify tag target.

Never force-push or overwrite existing tags.

Do not publish Docker Hub images yet.
Public distribution is reserved for M17.

Do not start M7.

==================================================
FINAL ACCEPTANCE REPORT
==================================================

Provide:

1. Container architecture
2. Dockerfiles and Compose services
3. Host Ollama profile verification
4. Container Ollama profile verification
5. Exact Docker commands and outputs
6. Health and readiness results
7. Real browser screenshots
8. Live four-source healthcare query
9. Gemma 4 inference results
10. Offline and Docker test results
11. Coverage and quality checks
12. Docker image sizes
13. Apple Silicon limitations
14. Git commit SHA
15. Annotated tag verification
16. GitHub Actions CI run
17. M6 COMPLETE/INCOMPLETE decision

Do not start M7.
