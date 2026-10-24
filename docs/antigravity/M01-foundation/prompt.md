# Milestone M01: Original Prompt & Instructions

The following is the complete, verbatim original prompt and instructions provided for Milestone M1:

```markdown
You are working in my existing, locally cloned GitHub repository:

open-healthcare-agentic-platform

PROJECT GOAL
Build a vendor-neutral, open-source, evidence-grounded healthcare search and agentic AI platform using Python, Gemma 4, Ollama, LangGraph, MCP, Docker, Kubernetes, vLLM, and OpenTelemetry.

The platform will eventually integrate four public healthcare data sources:
1. NPPES — healthcare provider discovery
2. PubMed — biomedical research
3. CMS Provider Data — clinician and facility information
4. MedlinePlus — trusted patient education

IMPORTANT:
This task is ONLY Milestone M1: Repository Foundation, Python & CI.

Do NOT implement Gemma 4 inference, LangGraph agents, MCP integrations, APIs, Streamlit, Docker, or Kubernetes in M1.

MILESTONE
M1 — Repository Foundation, Python & CI
Target Git tag: v0.1.0-m01
Feature branch: feature/m01-foundation

STEP 1 — INSPECT THE EXISTING REPOSITORY
- Verify the current Git branch, remote, and working tree.
- Inspect all existing files before changing anything.
- Preserve existing README, LICENSE, and other useful content.
- Do not delete existing files or overwrite user changes unnecessarily.
- Confirm that this is the correct repository.
- Create and switch to feature/m01-foundation.
- If there are uncommitted changes or Git conflicts, report them and preserve them.

STEP 2 — PYTHON PROJECT FOUNDATION
- Target Python 3.12 and newer compatible versions.
- Use the src-layout Python packaging convention.
- Create pyproject.toml with appropriate project metadata.
- Use Hatchling or another lightweight PEP 517 build backend.
- Project package: healthcare_agents
- Define a simple CLI entry point:
  healthcare-agents
- Add a --version command.
- Add a health/status command that confirms project configuration can load.
- Keep dependencies minimal.
- Do not add large AI frameworks yet.
- Do not add fake provider data or fake AI implementations.

STEP 3 — CREATE .GITIGNORE
Create a comprehensive .gitignore containing:

Python:
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

Virtual environments:
.venv/
venv/
env/

Secrets and environment:
.env
.env.*
!.env.example
*.pem
*.key
secrets/

IDE and OS:
.DS_Store
.idea/
.vscode/
*.swp

Runtime and model artifacts:
logs/
*.log
models/
checkpoints/
*.gguf
*.safetensors

Never commit API keys, credentials, model weights,
local datasets, or generated runtime artifacts.

Keep .env.example tracked.

STEP 4 — CONFIGURATION
- Create src/healthcare_agents/config.py.
- Use standard environment variables.
- Provide explicit defaults for nonsecret settings.
- Create .env.example with documented placeholder values.
- Include future configuration placeholders for:
  MODEL_PROVIDER=ollama
  MODEL_NAME=<documented model placeholder>
  OLLAMA_BASE_URL=http://localhost:11434
- Do not connect to Ollama yet.
- Avoid unnecessary dependencies and premature configuration complexity.

STEP 5 — CODE QUALITY
Configure:
- pytest
- pytest-cov
- Ruff
- mypy

Add configuration in pyproject.toml.

Use Python type hints.
Keep implementation simple, maintainable, and readable.

STEP 6 — AUTOMATED TESTS
Create meaningful tests for:
- Package imports
- Package version
- CLI --version behavior
- CLI health/status behavior
- Configuration defaults
- Environment variable overrides
- Invalid configuration handling where applicable

Tests must run offline.
No network access, model installation, Docker, or API keys required.

STEP 7 — GITHUB ACTIONS CI
Create .github/workflows/ci.yml.

CI must:
- Trigger on pushes and pull requests.
- Use Python 3.12.
- Install the package and development dependencies.
- Run Ruff lint checks.
- Run Ruff formatting checks.
- Run mypy.
- Run pytest.
- Build a distributable Python package.
- Verify the package can be installed and imported.

Use least-privilege workflow permissions.
Do not require secrets.
Do not upload sensitive information.

STEP 8 — PROJECT DOCUMENTATION
Create or update:
- README.md
- CONTRIBUTING.md
- SECURITY.md
- LICENSE (Apache 2.0, if not already present)
- docs/architecture/README.md
- docs/milestones/M01-foundation.md

README must explain:
- Project purpose
- Open-source healthcare discovery concept
- Planned technology stack
- Four planned healthcare data sources
- Six-phase roadmap
- Local developer setup
- Installation
- CLI smoke test
- Running tests
- Current implemented functionality
- Future milestone status
- License
- Non-clinical/research disclaimer

Do not claim planned functionality is already implemented.

ARCHITECTURE:
Include a Mermaid architecture diagram in the architecture documentation.

Planned flow:
Streamlit UI
  -> FastAPI
  -> LangGraph multi-agent workflow
  -> MCP healthcare tools
  -> NPPES / PubMed / CMS / MedlinePlus

The agents also use an interchangeable model adapter:
  -> Ollama + Gemma 4 (local)
  -> vLLM + Gemma 4 (Kubernetes)

Infrastructure:
  -> Docker Compose
  -> Kubernetes + Helm

Observability:
  -> OpenTelemetry
  -> Prometheus
  -> Grafana
  -> Tempo

Clearly mark the diagram as TARGET ARCHITECTURE.

STEP 9 — VALIDATE IMPLEMENTATION
Work incrementally.

After each meaningful implementation step:
- Run relevant tests.
- Verify imports.
- Run linting and type checks.
- Fix errors before continuing.

At final validation, run:
- pytest
- ruff check .
- ruff format --check .
- mypy src
- python -m build
- pip install -e .
- healthcare-agents --version
- healthcare-agents health

Verify installation from the built wheel in a clean
temporary virtual environment as well.

Report actual test results.
Do not invent successful results.

STEP 10 — MILESTONE ACCEPTANCE REPORT
Create docs/milestones/M01-foundation.md.

Record:
- Milestone objectives
- Files created/modified
- Actual commands executed
- Test results and counts
- Package build results
- CLI verification
- CI configuration status
- Known limitations
- Remaining work
- Acceptance checklist
- Exact Git commit and tag information when available

Do not claim GitHub Actions CI passed until its GitHub run
has actually completed successfully.

STEP 11 — GIT COMMIT, TAG, AND PUSH
Only after all required LOCAL checks pass:

1. Review git diff and git status.
2. Verify no secrets or generated files are staged.
3. Commit changes on feature/m01-foundation.
4. Push the feature branch.
5. Merge into main without overwriting remote changes.
6. Push main.
7. Create an annotated tag on the verified main commit:

   v0.1.0-m01

8. Push the tag.
9. Verify the remote branch and tag exist.
10. Check GitHub Actions results.

If GitHub CI fails:
- Fix the issue.
- Re-run validation.
- Do not mark M1 complete until required checks pass.
- Do not silently move or overwrite a published tag.

If any Git operation cannot be completed safely,
stop that operation and report the blocker.
Do not force-push.
```
