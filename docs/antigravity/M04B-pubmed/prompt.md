# Milestone M04B: Prompt Requirements

This document captures the complete original prompt and instructions for Milestone M04B.

```markdown
PROJECT: open-healthcare-agentic-platform

MILESTONE: M4B — Live PubMed Research Retrieval
TARGET TAG: v0.4.1-m04b
BRANCH: main ONLY

Read AGENTS.md and all previous milestone reports.
Follow every permanent documentation, testing,
Git and release rule.

OBJECTIVE:
Integrate real PubMed biomedical research into the
existing Gemma 4 + LangGraph healthcare discovery
workflow using NCBI E-utilities.

Keep all existing M1–M4A functionality operational.

Do not implement CMS Provider Data or MedlinePlus
live integrations yet.

==================================================
STEP 1 — INSPECT AND VERIFY
==================================================

- Confirm clean main branch and correct remote.
- Verify v0.4.0-m04a exists.
- Inspect current Evidence Agent, Provider Agent,
  NPPES client, schemas, validator, CLI, and tests.
- Review official NCBI E-utilities documentation.
- Inspect existing retrieval mode configuration.
- Preserve the NPPES live integration.

==================================================
STEP 2 — BUILD PUBMED CLIENT
==================================================

Create:
src/healthcare_agents/retrieval/pubmed_client.py

Use official NCBI E-utilities:

https://eutils.ncbi.nlm.nih.gov/entrez/eutils/

Implement:
- ESearch for PubMed discovery
- EFetch for article metadata and abstracts
- PubMed ID lookup
- Query term construction
- Configurable result limits
- Relevance and publication-date sorting
- Request timeouts
- Bounded retries and backoff
- Rate-limit awareness
- Robust XML/JSON parsing
- Empty result handling
- Graceful API error handling

Default to no required API key.

Support optional:
NCBI_API_KEY
NCBI_EMAIL
NCBI_TOOL

Respect NCBI usage policies.

Do not log API keys.

==================================================
STEP 3 — NORMALIZED RESEARCH SCHEMA
==================================================

Define typed research evidence records with:

- PMID
- Article title
- Authors
- Journal
- Publication date
- Abstract text when available
- DOI when available
- PubMed URL
- Retrieval timestamp
- Source type = PubMed
- Evidence availability/status
- Simulated vs live source status

Handle missing authors, abstracts and DOIs.

Use actual PubMed identifiers and URLs.

Never invent:
- Publication titles
- Authors
- Study findings
- DOI values
- Clinical conclusions

A PubMed citation establishes that a publication
exists, not that its conclusions are universally valid.

==================================================
STEP 4 — LANGGRAPH INTEGRATION
==================================================

Connect the existing Evidence Agent to PubMed.

Use the Planner's clinical topic/search plan to
construct a bounded research search query.

Support configurable retrieval selection:
- Live PubMed for real application execution
- Synthetic fixtures for offline tests

Keep independently configurable source modes
where necessary.

Important:
Live NPPES must remain live by default.
PubMed must use real records in live mode.
MedlinePlus remains a clearly labeled fixture.

Do not silently substitute fabricated studies if
PubMed fails or returns no records.

Return a visible source error or no-evidence status.

==================================================
STEP 5 — EVIDENCE VALIDATION
==================================================

Enhance deterministic validation to check:

- PMID format
- Source provenance
- Valid publication URLs
- Missing metadata
- Duplicate PMIDs
- Evidence-to-claim citation mapping
- Distinction between general research findings
  and provider-specific claims

Never treat a general research article as evidence
that an individual dentist has a certain qualification
or experience.

Avoid asserting that a specific treatment is
clinically appropriate for an individual patient.

The final answer must disclose missing evidence
and avoid unsupported recommendations.

==================================================
STEP 6 — M4A DATA-QUALITY CORRECTION
==================================================

The prior M4A report showed that Houston pediatric
dentistry searches could contain providers whose
practice location was outside Houston, or whose
taxonomy was general dentistry.

Inspect and address these issues:

- Validate requested city/state against the
  normalized PRACTICE address, not mailing address.
- Validate relevant provider taxonomy codes.
- Exclude or clearly separate nonmatching candidates.
- Document matching rules and any limitations.
- Add regression tests for out-of-area providers
  and unrelated taxonomies.

Do not alter original NPPES source records.
Do not change or overwrite the M4A Git tag.

==================================================
STEP 7 — CLI INTEGRATION
==================================================

Preserve the existing CLI.

Run:

healthcare-agents search \
  --query "Find pediatric dentists in Houston" \
  --verbose

The output should show:

1. Planner query decomposition
2. Live NPPES provider discovery
3. Live PubMed article retrieval
4. Evidence and provenance validation
5. Gemma 4 grounded answer
6. Actual PubMed citations and URLs
7. Clear status of still-simulated MedlinePlus data

For the live demo, use a query addressing pediatric
dentistry and dental anxiety research.

Show the real retrieved publications.

==================================================
STEP 8 — TESTING
==================================================

Add offline tests covering:

- Query construction
- PMID search and parsing
- EFetch XML parsing
- Article metadata normalization
- Missing abstracts
- Duplicate PMIDs
- Empty results
- HTTP errors and timeouts
- Retry behavior
- Rate-limit handling
- Evidence citation mapping
- LangGraph integration
- Live/fixture source isolation
- Provider location/taxonomy regression cases

Mock network calls for offline CI.

Add opt-in live tests for:
- Actual PubMed query
- Actual article retrieval
- Valid PubMed links
- Real NPPES + PubMed LangGraph workflow
- Real Gemma 4 answer synthesis

Run all existing tests and prevent regressions.

Maintain >=90% offline coverage.

Do not report skipped live tests as successful.

==================================================
STEP 9 — DOCUMENTATION
==================================================

Create:

docs/antigravity/M04B-pubmed/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save the COMPLETE original prompt.

Create:
docs/milestones/M04B-pubmed.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md
.env.example

Create a professional workflow diagram:

docs/images/m4b_workflow.png

Requirements:
- Use PNG in README, not SVG.
- Match the preferred M4A visual design.
- Show live NPPES and PubMed integrations.
- Show MedlinePlus remains simulated.
- Preserve an editable diagram source.
- Verify actual readability and GitHub rendering.
- Do not invent architecture components.

Document real commands, tests, article records,
limitations, failures and fixes.

==================================================
STEP 10 — VALIDATE AND RELEASE
==================================================

Run:
- pytest with coverage
- Ruff lint and format checks
- mypy
- Python package build
- Clean wheel installation
- CLI smoke tests
- Live NPPES tests
- Live PubMed tests
- Real Gemma 4 + LangGraph integration tests

Work on main only.

After all local checks pass:

1. Review Git diff and status.
2. Ensure no secrets or model weights are staged.
3. Commit code and documentation to main.
4. Push main.
5. Verify GitHub Actions CI passes.
6. Create annotated tag v0.4.1-m04b.
7. Push the tag to origin.
8. Verify tag and commit SHA.

Do not force-push or move existing tags.

==================================================
FINAL REPORT
==================================================

Provide:

1. Implementation summary
2. PubMed API implementation details
3. Actual articles retrieved with PMIDs
4. Live LangGraph workflow execution
5. NPPES filtering correction results
6. Test count and coverage
7. Ruff/mypy/build results
8. Architecture PNG and README rendering
9. Git commit SHA
10. Annotated tag verification
11. GitHub Actions CI status
12. Remaining limitations
13. M4B complete/incomplete decision

Do not begin M4C until M4B passes all gates.
```
