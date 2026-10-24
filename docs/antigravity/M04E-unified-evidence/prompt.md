```markdown
PROJECT: open-healthcare-agentic-platform

MILESTONE: M4E — Unified Evidence Normalization,
Ranking, Deduplication & Provenance

TARGET TAG: v0.4.4-m04e
BRANCH: main ONLY

Read AGENTS.md and all M1–M4D milestone documentation.

Follow all permanent implementation, testing,
documentation and Git release rules.

==================================================
OBJECTIVE
==================================================

Build a unified evidence-processing layer over the
four existing live public healthcare sources:

1. NPPES — Provider Registry
2. PubMed — Biomedical Research
3. CMS Provider Data — Applicable Public Metrics
4. MedlinePlus — Patient Education

Improve evidence relevance, normalization,
deduplication, ranking and citation integrity.

Preserve all existing capabilities.

Do not begin M5, Docker, Kubernetes or publishing.

Do not add unrelated new external data sources.

==================================================
STEP 1 — BASELINE INSPECTION
==================================================

Confirm:
- Branch = main
- Clean working tree
- v0.4.3-m04d exists
- All four live sources work
- Gemma 4 + Ollama inference works
- LangGraph workflow works
- Existing offline and live tests pass

Inspect:
- Typed provider records
- Clinical evidence records
- Patient education records
- CMS quality records
- Search plans
- Validation logic
- LangGraph state
- CLI presentation

Record baseline test counts and coverage.

==================================================
STEP 2 — UNIFIED EVIDENCE SCHEMA
==================================================

Create a reusable evidence package:

src/healthcare_agents/evidence/
    __init__.py
    schemas.py
    normalization.py
    deduplication.py
    relevance.py
    ranking.py
    provenance.py

Define typed structures capturing:
- Stable evidence identifier
- Source type
- External source identifier
- Title or provider name
- Source URL
- Retrieved timestamp
- Published or updated date if available
- Query relevance
- Source-specific metadata
- Citation identifier
- Evidence status
- Live/fixture status
- Known limitations

Maintain source-specific record distinctions.

Do not flatten a clinician, hospital,
scientific publication and educational topic
into one semantically interchangeable object.

Preserve original source records and their metadata.

==================================================
STEP 3 — NORMALIZATION AND DEDUPLICATION
==================================================

Normalize:
- NPPES provider records
- PubMed publications
- CMS clinician/facility records
- MedlinePlus educational topics

Implement deterministic deduplication:

NPPES:
- Exact NPI
- Relevant specialty taxonomy
- Practice location matching

PubMed:
- Exact PMID
- DOI where present
- Avoid merging distinct publications

CMS:
- Dataset ID
- Entity type
- Appropriate source identifier
- Reporting period

MedlinePlus:
- Canonical official URL
- Topic identifier
- Language
- Preserve separate English/Spanish resources

Never merge unrelated entity types.

Document exact deduplication keys.

==================================================
STEP 4 — RELEVANCE AND RANKING
==================================================

Implement explainable relevance checks and ranking.

For provider discovery:
- Requested specialty match
- Requested practice location match
- Identity/provenance completeness
- Source record validity

Do not rank by invented clinical quality.
Do not infer clinical experience from NPI.

For PubMed:
- Match clinical intent
- Title/abstract topical relevance
- Publication type when available
- Publication date when relevant
- Explicit rejection of unrelated research

Regression case:
PMID 39046104 must not appear as evidence
supporting pediatric dental anxiety.

For MedlinePlus:
- Match patient education topic to query
- Prefer directly relevant dental health topics
- Reject unrelated returned educational topics
- Distinguish English and Spanish content

For CMS:
- Relevant entity type
- Correct identifiers
- Reporting period
- Measure availability and scope
- No fake ratings for providers lacking measures

Do not build a misleading universal provider
quality score.

Define explainable per-source relevance scores,
not an uncalibrated single clinical quality score.

Store why evidence was selected or excluded.

==================================================
STEP 5 — PROVENANCE AND CITATION INTEGRITY
==================================================

Create a source provenance layer.

Every supported factual claim should have
a traceable source record where applicable.

Store:
- Source name
- External ID
- Canonical URL
- Retrieval timestamp
- Source record type
- Citation ID
- Associated claim references

Validate:
- Citation exists in retrieved evidence
- Source URL is consistent with source type
- Citation IDs are not duplicated
- Claims do not cross inappropriate
  evidence boundaries

NPPES cannot establish licensure or competence.
PubMed research cannot establish an individual
provider's credentials.
CMS facility ratings are not individual dentist
ratings.
MedlinePlus education is not primary research.

Never allow the model to invent citation IDs,
publication titles or evidence sources.

==================================================
STEP 6 — LANGGRAPH INTEGRATION
==================================================

Integrate the unified evidence layer into the
existing LangGraph workflow.

Expected conceptual flow:

User Query
    |
Planner Agent (Gemma 4)
    |
Four Source Retrieval
    |
Normalization
    |
Deduplication
    |
Relevance / Ranking
    |
Deterministic Validation
    |
Answer Agent (Gemma 4)
    |
Grounded Response + Provenance

Use bounded execution and clear error handling.

Preserve source-specific statuses when:
- No results exist
- Source is unavailable
- A dataset does not cover the provider
- Evidence is incomplete
- Only partially relevant evidence exists

Do not silently replace failed live sources
with synthetic fixtures.

==================================================
STEP 7 — STRUCTURED OUTPUT
==================================================

Create a stable result schema containing:

- User query
- Interpreted search intent
- Provider candidates
- Clinical research evidence
- Applicable CMS data
- Patient education resources
- Source provenance
- Relevance explanations
- Missing information
- Source errors and limitations
- Grounded answer text

Ensure each evidence item can be traced back to
the source response.

Separate raw evidence, selected evidence and
generated narrative.

The narrative must not be considered validated
solely because the source records are valid.

Use deterministic claim/citation checks where
possible and explicitly document remaining
limitations of semantic claim verification.

==================================================
STEP 8 — CLI DEMONSTRATION
==================================================

Preserve all existing CLI commands.

Run:

RETRIEVAL_MODE=live uv run healthcare-agents search \
  --query "Find pediatric dentists in Houston and \
research on pediatric dental anxiety" \
  --verbose

Demonstrate:
- Four live source queries
- Normalized source records
- Deduplication
- Relevant provider filtering
- Publication relevance
- Patient education topic relevance
- Source-specific rankings
- Valid citations
- Missing CMS data explanation
- Grounded Gemma 4 response
- No fabricated providers or research

Show meaningful source counts and reasons
for exclusions in verbose output.

Do not invent successful retrieval results.

==================================================
STEP 9 — TESTING
==================================================

Add comprehensive offline tests for:

- Evidence normalization
- Provider matching and deduplication
- PubMed duplicate PMIDs
- DOI handling
- CMS identifier isolation
- Reporting period preservation
- MedlinePlus canonical URLs
- Language-specific topic handling
- Relevance scoring
- Irrelevant research rejection
- Irrelevant patient education rejection
- Unsupported claim handling
- Citation integrity
- Missing source records
- Partial retrieval failures
- Empty evidence
- Live/fixture separation
- LangGraph state integration
- CLI result presentation

Include adversarial tests for:
- Valid but irrelevant PubMed publications
- Valid but irrelevant MedlinePlus topics
- General dentistry vs pediatric dentistry
- Out-of-area provider practice addresses
- Provider quality claims unsupported by data
- Citation identifiers not in retrieved records

Run previous M1–M4D regression tests.

Add opt-in full four-source live integration tests
with real local Gemma 4 inference.

Maintain >=90% offline test coverage.

If live execution fails, do not mark M4E complete.

==================================================
STEP 10 — DOCUMENTATION
==================================================

Create:

docs/antigravity/M04E-unified-evidence/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save the COMPLETE original prompt in prompt.md.

Create:
docs/milestones/M04E-unified-evidence.md

Update:
README.md
docs/architecture/README.md
docs/antigravity/README.md

Document:
- Unified schemas
- Data flow
- Source-specific normalization
- Ranking methods
- Exclusion reasons
- Citation/provenance guarantees
- Remaining semantic limitations
- Live examples
- Real commands and outputs
- Test results

Create:
docs/images/m4e_workflow.png

Use the professional M4A–M4D visual style.

PNG must be embedded in README.
Keep editable source separately.
Verify visually:
- Readable text
- Correct architecture
- No clipping
- Proper arrows
- Clear four-source distinction

Do not substitute a plain Mermaid block for
the README PNG diagram.

==================================================
STEP 11 — QUALITY GATES
==================================================

Run:
- pytest with coverage
- Ruff lint
- Ruff format check
- mypy strict
- Python build
- Clean wheel installation
- Existing CLI smoke tests
- Four-source live API tests
- Real Gemma 4 + LangGraph integration test

Record exact results.

Ensure no regression from M1–M4D.

==================================================
STEP 12 — GIT AND RELEASE
==================================================

Work directly on main only.

After all required checks pass:

1. Review git status and diff.
2. Verify no secrets, PHI or model weights.
3. Commit all verified code and documentation.
4. Push main.
5. Verify GitHub Actions CI passes.
6. Create annotated tag v0.4.4-m04e.
7. Push tag.
8. Verify remote tag points to verified commit.

Never force-push.
Never overwrite existing tags.

Do not start M5.

==================================================
FINAL REPORT
==================================================

Provide:

1. Implementation summary
2. Unified evidence architecture
3. Source normalization details
4. Ranking and relevance validation
5. PubMed and MedlinePlus relevance results
6. Citation/provenance verification
7. Real four-source LangGraph execution
8. Tests passed and actual coverage
9. Ruff, mypy and build results
10. README PNG rendering verification
11. Git commit SHA
12. Annotated tag verification
13. GitHub Actions CI status
14. Remaining limitations
15. M4E COMPLETE/INCOMPLETE decision

Do not begin M5 until M4E passes every gate.
```
