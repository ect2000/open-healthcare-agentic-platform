```markdown
PROJECT: open-healthcare-agentic-platform

MILESTONE: M5 — FastAPI + Streamlit Web Application
TARGET TAG: v0.5.0-m05
BRANCH: main ONLY

Read AGENTS.md and all M1–M4E documentation.
Preserve every completed milestone.

OBJECTIVE:
Build a professional browser-based demonstration
for the existing LangGraph healthcare discovery
platform, backed by a reusable FastAPI service.

M5 is an application/UI milestone.
Do not implement Docker, Kubernetes, Helm,
vLLM, production authentication, or observability
infrastructure yet.

==================================================
1. INSPECT AND VALIDATE BASELINE
==================================================

- Confirm main branch and clean working tree.
- Verify M4E tag v0.4.4-m04e.
- Review CLI, LangGraph state, unified evidence
  schemas and structured output.
- Review four-source retrieval and model adapter.
- Run existing offline baseline tests.
- Preserve the existing CLI functionality.

==================================================
2. FASTAPI BACKEND
==================================================

Create:
src/healthcare_agents/api/
    __init__.py
    app.py
    routes.py
    schemas.py
    service.py

Implement:
- GET /health
- GET /ready
- GET /api/v1/status
- POST /api/v1/search

Use request and response schemas with Pydantic.

Search request:
- Query
- Optional result limit
- Explicit permitted retrieval mode if supported
- Request ID / correlation ID

Search response:
- Request ID
- Parsed search intent
- Provider candidates
- PubMed research evidence
- CMS applicable metrics
- MedlinePlus patient education
- Source provenance
- Relevance and exclusion information
- Generated grounded answer
- Source errors, unknowns and limitations
- Execution metadata

Reuse the existing LangGraph workflow.
Do not duplicate search logic in the API.

Add:
- Input validation
- Structured exception responses
- Configurable timeouts
- Bounded request execution
- Safe logging without patient-sensitive content
- Correct HTTP status codes
- Automatic OpenAPI documentation

Do not claim a health endpoint proves that
all external services are available.

==================================================
3. STREAMLIT APPLICATION
==================================================

Create:
src/healthcare_agents/ui/
    __init__.py
    app.py
    components.py
    api_client.py

Build a polished, compact, responsive interface.

Application title:
Open Healthcare Agentic Platform

Subtitle:
Evidence-Grounded Healthcare Discovery
with Open Models and Cloud-Native AI

Include:

A. SEARCH AREA
- User healthcare query
- Search button
- Helpful example presets
- Clear retrieval source status
- Simple indication of local model/backend

B. EXECUTION TRACKER
- Planning
- Provider and evidence retrieval
- Validation / ranking
- Answer generation

Do not show fictitious real-time progress.
If stage-by-stage progress is displayed,
it must correspond to actual backend events.
Otherwise display honest loading status.

C. RESULTS
- Provider discovery cards
- Specialty and practice location
- NPI and official source link
- PubMed articles and canonical citations
- CMS data only where genuinely applicable
- MedlinePlus education links
- Evidence ranking explanations
- Generated answer with provenance
- Source failures and missing data

D. TRUST & LIMITATIONS
- Clearly distinguish confirmed source fields
  from AI-generated narrative.
- NPI does not prove clinical credentials.
- PubMed publication != provider expertise.
- Hospital ratings != individual dentist ratings.
- Missing CMS metrics != poor quality.
- Do not present results as medical advice.
- Show fixture/demo labels in fixture mode.

Avoid oversized cards, blank thumbnails,
decorative images, and crowded sections.

Use compact navigation and readable layouts.

==================================================
4. EXAMPLE DEMOS
==================================================

Include presets:

1. Find pediatric dentists in Houston.
2. Pediatric dental anxiety and evidence.
3. Compare publicly available provider data.
4. Find patient education for child dental health.

Only display sources actually retrieved.

Make the demo easy to explain in:
- CNCF community talks
- Docker community workshops
- University hands-on labs
- Open-source project demonstrations

Do not expose secrets or private records.

==================================================
5. API / UI INTEGRATION
==================================================

Streamlit must call the real FastAPI backend
through a configurable endpoint.

Do not create a separate fake UI workflow.

Handle:
- Backend unavailable
- Ollama/model unavailable
- No provider results
- PubMed unavailable
- CMS missing data
- MedlinePlus unavailable
- Partial source failures
- Invalid requests
- Request timeout

Keep the application useful when one public
source is unavailable, while accurately reporting
what succeeded and failed.

Do not silently substitute synthetic data
in live mode.

==================================================
6. LOCAL DEVELOPER EXPERIENCE
==================================================

Provide documented commands to launch:

- Ollama with Gemma 4
- FastAPI service
- Streamlit UI

Provide health and readiness checks.

Do not hardcode credentials or local user paths.

Add convenient cross-platform development
commands where practical.

Docker Compose and one-command packaged
deployment are reserved for M6–M7.

==================================================
7. TESTING
==================================================

Add automated tests for:

- FastAPI endpoints
- Pydantic validation
- Search request/response serialization
- Error status codes
- Timeouts
- Partial source failures
- Fixture/live isolation
- API client behavior
- Streamlit UI initialization
- Result display
- Citation links
- Provider data limitations
- Previously implemented LangGraph behavior

Use offline mocks for CI.

Add opt-in live tests for:
- Real local Gemma 4
- Real FastAPI search request
- All four public healthcare sources
- Structured source-grounded response
- Streamlit-to-FastAPI end-to-end workflow

Where available, use Streamlit AppTest and a
browser acceptance test to validate actual UI.

A passing test of Python components alone is
not equivalent to a verified browser demo.

Preserve all M1–M4E regression tests.
Maintain >=90% offline coverage.

==================================================
8. DOCUMENTATION & VISUALS
==================================================

Create:

docs/antigravity/M05-fastapi-streamlit/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save the complete original prompt verbatim.

Create:
docs/milestones/M05-fastapi-streamlit.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md
.env.example

Create:
docs/images/m5_workflow.png

Use the professional architecture visual style
established in M4A–M4E.

Keep an editable source asset separately.
Use PNG in README, not SVG.

Add actual UI screenshots to docs/images/
after visually verifying the working application.

Do not use generated/mock screenshots as
evidence of working software.

==================================================
9. QUALITY GATES
==================================================

Run:
- pytest with coverage >=90%
- Ruff lint
- Ruff format check
- mypy strict
- Package build
- Clean wheel installation
- CLI regression tests
- API integration tests
- Streamlit UI tests
- Real end-to-end local workflow
- Browser acceptance where available

Document exact commands, outputs and failures.

Verify API / UI still work with:
- Valid results
- Empty results
- Source failures
- Slow model inference

Do not claim tests passed if they were skipped.

==================================================
10. GIT & RELEASE
==================================================

Work on main only.
Never create feature branches.

Once all required checks pass:

1. Review git diff and status.
2. Verify no secrets, PHI or model weights.
3. Commit implementation and documentation.
4. Push main.
5. Verify GitHub Actions CI succeeds.
6. Create annotated tag v0.5.0-m05.
7. Push and verify tag.
8. Confirm tag points to the verified commit.

Never force-push or overwrite existing tags.

Do not begin M6 until M5 is accepted.

==================================================
FINAL ACCEPTANCE REPORT
==================================================

Provide:

1. FastAPI endpoint implementation summary
2. Actual API request/response examples
3. Streamlit features implemented
4. Screenshots of real running UI
5. Local startup commands
6. Live four-source search results
7. Gemma 4 + LangGraph execution verification
8. Offline and live test results
9. Coverage, Ruff, mypy and build results
10. README PNG diagram verification
11. Git commit and annotated tag
12. GitHub Actions CI status
13. Known limitations
14. M5 COMPLETE/INCOMPLETE decision

Do not start M6.
```
