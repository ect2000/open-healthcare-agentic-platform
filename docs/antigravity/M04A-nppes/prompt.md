PROJECT: open-healthcare-agentic-platform
MILESTONE: M4A — Live NPPES Provider Discovery
TAG: v0.4.0-m04a
BRANCH: main ONLY

Read AGENTS.md and previous milestone documentation.

OBJECTIVE
Replace synthetic provider retrieval in the existing
LangGraph Provider Agent with real public NPPES
provider discovery.

Preserve the Gemma 4 + Ollama and LangGraph
implementations from M1–M3.

Do not implement PubMed, CMS, or MedlinePlus
live integrations yet.

STEP 1 — INSPECT
- Verify main branch and clean working tree.
- Review retrieval interfaces, fixtures, workflow
  state, Provider Agent and validator.
- Inspect current test coverage and CI.
- Review official NPPES API 2.1 documentation.

STEP 2 — NPPES CONNECTOR
Implement an async-capable or synchronous HTTP
client consistent with current architecture.

Use:
https://npiregistry.cms.hhs.gov/api/

Support:
- NPI lookup
- Specialty/taxonomy search
- City and state search
- Pagination within documented API limits
- Timeout handling
- Bounded retry with backoff
- Rate-limit awareness
- Empty results and malformed responses
- Configurable request limits
- Source URL and retrieval timestamp

Use API version 2.1 where supported.
Confirm actual API behavior with live tests.

Do not require an API key.

STEP 3 — NORMALIZE REAL PROVIDER DATA
Implement typed provider records capturing:
- NPI
- Name
- Individual/organization classification
- Specialty/taxonomy
- Practice location
- Address and available contact details
- Source
- Retrieval timestamp
- Explicitly unknown or unavailable fields

Differentiate practice and mailing addresses.

Never invent ratings, services, insurance coverage,
board certification, licensing status, or experience.

IMPORTANT:
An NPI is not proof of professional licensure,
credentialing, clinical competence, or quality.

STEP 4 — LANGGRAPH INTEGRATION
Connect the existing Provider Agent to the NPPES
client through the retrieval abstraction.

Add configurable retrieval mode:

RETRIEVAL_MODE=live
RETRIEVAL_MODE=fixture

Default normal application behavior should use
live NPPES retrieval when configured.

Offline tests must use isolated fixtures.

Preserve the same LangGraph workflow and existing
Gemma 4 model adapter.

Keep PubMed and MedlinePlus evidence fixtures
clearly labeled as simulated.

STEP 5 — VALIDATION
Ensure:
- Real and synthetic records cannot be confused.
- Source identifiers are preserved.
- NPI values are checked for appropriate format.
- Duplicate NPIs are removed.
- Missing data remains unknown.
- Unsupported provider claims are not generated.
- No provider is called licensed or verified merely
  because the NPI exists.

If live NPPES fails, report a retrieval failure.
Do not silently substitute synthetic providers
in a production-style response.

STEP 6 — CLI DEMO
Support:

healthcare-agents search \
  --query "Find pediatric dentists in Houston"

Add a clear display showing:
- Live NPPES provider results
- Real NPI identifiers
- Provider name and specialty
- Practice address
- Source provenance
- Retrieval timestamp
- Which evidence remains simulated

Preserve all M1–M3 CLI functionality.

STEP 7 — TESTING
Add offline tests for:
- Search parameters
- Provider normalization
- Address selection
- Pagination
- Invalid and missing fields
- NPI lookup
- Duplicate detection
- Empty results
- Timeouts and HTTP failures
- Malformed API responses
- Live/fixture mode switching
- LangGraph integration
- Evidence provenance

Add opt-in LIVE NPPES integration tests.

Execute a real pediatric dentistry query for
Houston, Texas, and record actual results.

Run a live end-to-end LangGraph query using
Gemma 4 and real NPPES retrieval.

Do not claim any provider-specific expertise
that NPPES does not establish.

Run all previous tests and ensure no regression.

Maintain >=90% offline code coverage.

STEP 8 — DOCUMENTATION
Create:

docs/antigravity/M04A-nppes/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save the complete original prompt in prompt.md.

Also create:
docs/milestones/M04A-nppes.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md

Save architecture/workflow changes as versioned
diagram assets under docs/images/ and embed
them in README.md.

Document:
- Actual NPPES endpoint behavior
- Normalized record schema
- Search examples
- Live test results
- API limitations
- Source verification boundaries
- Failure behavior

Never commit real patient information or secrets.

STEP 9 — QUALITY & RELEASE
Work directly on main ONLY.

Run:
- pytest with coverage
- Ruff lint and format checks
- mypy
- Python package build
- Clean wheel installation
- Existing CLI smoke tests
- Live NPPES tests
- Live Gemma 4 + LangGraph + NPPES workflow

Review all staged files.

If local verification passes:
1. Commit code and docs to main.
2. Push main.
3. Verify GitHub Actions CI succeeds.
4. Create annotated tag v0.4.0-m04a.
5. Push the tag.
6. Verify the remote tag and commit.

Never force-push or overwrite existing tags.

STEP 10 — FINAL REPORT
Report:
1. Implementation summary
2. Actual NPPES query and response summary
3. Number of real providers retrieved
4. Provider normalization and validation
5. Live LangGraph execution results
6. Test counts and coverage
7. Ruff/mypy/build results
8. CLI demo output
9. Commit SHA and annotated tag
10. GitHub Actions status
11. Known limitations
12. Whether M4A is COMPLETE

Do not start M4B until M4A is verified.
