# Milestone M4D Prompt: Live MedlinePlus Patient Education

```text
PROJECT: open-healthcare-agentic-platform

MILESTONE: M4D — Live MedlinePlus Patient Education
TARGET TAG: v0.4.3-m04d
BRANCH: main ONLY

Read AGENTS.md and all M1–M4C documentation.
Follow all permanent project rules.

OBJECTIVE
Integrate real, authoritative patient education
information from the U.S. National Library of
Medicine's MedlinePlus services.

Replace simulated MedlinePlus fixtures in the
existing LangGraph healthcare discovery workflow.

Preserve all completed M1–M4C capabilities.

Do not begin M4E.

==================================================
STEP 1 — VERIFY EXISTING PROJECT
==================================================

1. Confirm main branch and clean working tree.
2. Verify v0.4.2-m04c exists.
3. Inspect current workflow, schemas and agents.
4. Review NPPES, PubMed and CMS clients.
5. Inspect existing patient education fixtures.
6. Run baseline tests.
7. Read official MedlinePlus API documentation.

Official documentation:

https://medlineplus.gov/about/developers/webservices/

https://medlineplus.gov/medlineplus-connect/web-service/

Do not confuse keyword-based MedlinePlus search
with MedlinePlus Connect's code-based API.

==================================================
STEP 2 — IMPLEMENT LIVE MEDLINEPLUS CLIENT
==================================================

Create:

src/healthcare_agents/retrieval/
    medlineplus_client.py

Implement the official keyword-based MedlinePlus
Web Service.

Support:
- Keyword search
- English and Spanish
- Relevant health-topic discovery
- Search result titles
- Official topic URLs
- Health-topic summaries when returned
- Search result snippets
- Source attribution
- Retrieval timestamps
- Topic identifiers when available
- Pagination only if officially supported
- Empty-result handling
- XML parsing
- Request timeouts
- Bounded retries
- Explicit HTTP failure handling

Do not assume a JSON endpoint exists for the
keyword-based Web Service.

Do not scrape MedlinePlus web pages.

Do not fabricate missing summaries or metadata.

==================================================
STEP 3 — RATE LIMITS AND CACHING
==================================================

Respect MedlinePlus Web Service acceptable use:

Maximum 85 requests per minute per IP address.

Implement:
- Conservative client-side rate limiting
- Configurable cache TTL
- Recommended 12–24 hour caching
- Bounded retries
- No unbounded request loops

Cache only public, non-personalized content.

Avoid storing patient queries or sensitive
health information in shared caches.

If the service is unavailable, report an error.
Do not silently replace live data with fixtures.

==================================================
STEP 4 — NORMALIZED PATIENT EDUCATION RECORDS
==================================================

Create typed records for:
- Topic title
- Topic identifier when provided
- Official URL
- Summary/snippet
- Language
- Source = MedlinePlus
- Retrieval timestamp
- Source attribution
- Live/fixture status

Ensure official URLs are preserved.

Use explicit unknown values for missing fields.

Patient education content must not be treated
as a research publication or provider credential.

Do not invent medical advice.

==================================================
STEP 5 — LANGGRAPH INTEGRATION
==================================================

Connect the existing Evidence Agent to
MedlinePlus patient education retrieval.

The workflow must now coordinate:

1. Live NPPES provider records
2. Live PubMed research publications
3. Live CMS data where applicable
4. Live MedlinePlus educational resources

Keep data categories separate and clearly typed.

Allow deterministic fixture mode for offline tests.

Do not silently mix fixture and live records.

Preserve the Gemma 4 + Ollama model adapter.

Preserve deterministic validation.

Do not invent additional autonomous agent
roles unless the architecture requires them.

==================================================
STEP 6 — HEALTHCARE SAFETY AND GROUNDING
==================================================

Enhance validation to ensure:

- MedlinePlus URLs are official.
- Topic titles and language metadata match
  retrieved records.
- Duplicate topics are removed.
- Missing content is disclosed.
- Educational summaries are not represented
  as original scientific research.
- Provider-specific claims require appropriate
  provider-specific evidence.
- NPI existence is not treated as licensure.
- CMS missing data is not treated as poor quality.
- PubMed topical relevance filters remain active.
- Unsupported clinical conclusions are rejected.

The final answer should clearly separate:

A. Healthcare provider discovery
B. Clinical research evidence
C. Applicable public CMS performance data
D. Patient education resources

Use citations and source labels for each category.

Do not provide personalized diagnosis or treatment
recommendations based solely on retrieved content.

==================================================
STEP 7 — OPTIONAL MEDLINEPLUS CONNECT
==================================================

Inspect the official MedlinePlus Connect service:

https://connect.medlineplus.gov/service

If adding a small, independently tested code-based
lookup fits the milestone safely, implement it as
a separate adapter.

Supported code systems may include:
- ICD-10-CM / SNOMED CT diagnoses
- RxCUI / NDC medication identifiers
- LOINC laboratory test identifiers
- Supported procedure code systems

Do not infer or fabricate clinical codes from a
free-text healthcare query.

Do not allow this optional capability to block
the main keyword-based integration.

Document any code-based functionality accurately.

==================================================
STEP 8 — LIVE CLI DEMO
==================================================

Run:

RETRIEVAL_MODE=live \
uv run healthcare-agents search \
  --query "Find pediatric dentists in Houston
  and research on pediatric dental anxiety" \
  --verbose

The demonstration must show:

- Real NPPES providers
- Real PubMed studies and PMIDs
- Applicable CMS information or explicit absence
- Real MedlinePlus patient education links
- Gemma 4 answer synthesis
- Actual provenance and citations
- No simulated patient education in live mode

Also test direct MedlinePlus keyword retrieval
with a relevant child dental health topic.

If no relevant MedlinePlus topic exists, show
the true no-result outcome rather than a fixture.

==================================================
STEP 9 — TESTING
==================================================

Add offline tests covering:

- Keyword encoding
- XML parsing
- Multiple topic records
- Missing summary elements
- English and Spanish results
- Source attribution
- Invalid URLs
- Duplicate topics
- Empty results
- HTTP errors
- Timeouts and retries
- Rate-limit behavior
- Cache behavior
- Live/fixture mode separation
- LangGraph integration
- Clinical source classification
- Previous M1–M4C regressions

Use mocked API responses for offline CI.

Add opt-in live tests for:
- Actual MedlinePlus keyword search
- Valid returned topic URLs
- English and Spanish requests
- Real end-to-end LangGraph workflow
- Gemma 4 synthesis across all live sources

Run all earlier live tests.

Maintain >=90% offline code coverage.

Never label skipped tests as passing.

==================================================
STEP 10 — DOCUMENTATION
==================================================

Create:

docs/antigravity/M04D-medlineplus/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save this complete original prompt in prompt.md.

Create:
docs/milestones/M04D-medlineplus.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md
.env.example

Document:
- Official API behavior
- Actual live topic results
- Language behavior
- Rate limits and caching
- Source provenance
- Clinical limitations
- Error handling
- Tests and verification
- Commands actually executed

Create:
docs/images/m4d_workflow.png

Design requirements:
- Use the polished M4A–M4C visual style.
- PNG in README, not SVG.
- Preserve editable diagram source.
- Clear separation of four live data sources.
- Large readable labels.
- No overlapping text or clipped arrows.
- Verify the real rendered PNG.

==================================================
STEP 11 — QUALITY GATES
==================================================

Run:
- pytest with coverage
- Ruff lint
- Ruff format check
- mypy strict
- Python package build
- Clean wheel installation
- CLI smoke tests
- Actual MedlinePlus live tests
- Full real LangGraph + Gemma 4 execution

Preserve previous functionalities.

Maintain >=90% offline coverage.

Do not fabricate test results.

==================================================
STEP 12 — COMMIT AND TAG
==================================================

Work directly on main ONLY.

When all requirements pass:

1. Review git diff and status.
2. Verify no secrets, PHI or model weights.
3. Commit code and documentation.
4. Push main.
5. Verify GitHub Actions CI succeeds.
6. Create annotated tag:

   v0.4.3-m04d

7. Push and verify the remote tag.
8. Confirm tag points to verified commit.

Never force-push or overwrite existing tags.

Do not start M4E.

==================================================
FINAL REPORT
==================================================

Provide:

1. Implementation summary
2. MedlinePlus API endpoints used
3. Actual health topics retrieved
4. English/Spanish test results
5. Live NPPES + PubMed + CMS + MedlinePlus
   LangGraph execution results
6. Evidence provenance checks
7. Test counts and coverage
8. Ruff, mypy and build results
9. README PNG diagram verification
10. Commit SHA and tag verification
11. GitHub Actions CI run
12. Remaining limitations
13. M4D COMPLETE or INCOMPLETE decision

Do not begin M4E until all gates pass.
```
