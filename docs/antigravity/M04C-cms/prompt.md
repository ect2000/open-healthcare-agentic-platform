```
PROJECT: open-healthcare-agentic-platform

MILESTONE: M4C — CMS Provider Data Integration
TARGET TAG: v0.4.2-m04c
BRANCH: main ONLY

Read AGENTS.md and all previous milestone reports.

OBJECTIVE:
Integrate real CMS Provider Data Catalog datasets
into the existing evidence-grounded healthcare
discovery workflow.

Preserve M1–M4B functionality.

Do not begin live MedlinePlus integration (M4D).

==================================================
1. VERIFY CURRENT STATE
==================================================

Confirm:
- Main branch and clean working tree
- M4B tag v0.4.1-m04b
- Existing NPPES and PubMed integrations
- LangGraph workflow and typed schemas
- Existing test suite and CI

==================================================
2. DISCOVER CMS DATASETS
==================================================

Use official CMS Provider Data Catalog:

https://data.cms.gov/provider-data/

API documentation:
https://data.cms.gov/provider-data/docs

Inspect available datasets and their dictionaries.

Identify relevant datasets for:
- Doctors and clinicians
- Provider enrollment information
- Facility affiliations, where applicable
- Public quality measures, where applicable

Do not assume that pediatric dentists have
individual CMS quality ratings.

Select actual supported datasets, documenting:
- Dataset ID
- Dataset name
- Version/update date
- Entity type
- Available identifiers
- Available fields
- Data limitations

If no dataset supports a given measure or provider,
return "not available" instead of inventing a value.

==================================================
3. IMPLEMENT CMS CLIENT
==================================================

Create:
src/healthcare_agents/retrieval/cms_client.py

Implement:
- Dataset discovery
- Configurable dataset selection
- Dataset metadata retrieval
- Querying and pagination
- Typed normalized records
- Timeouts and bounded retries
- Error handling
- Retrieval timestamps
- Source URLs and provenance

Use official current Provider Data Catalog endpoints.
Do not confuse these endpoints with NPPES or the
separate data.cms.gov Public API.

Do not hardcode unstable distribution identifiers.

==================================================
4. IDENTIFIER MATCHING
==================================================

Support reliable data matching against NPPES.

Use exact NPI matching only where:
- The CMS dataset actually contains NPI
- The identifier refers to the correct entity type
- The match is unambiguous

For facilities, respect facility-specific identifiers.

Never infer that a clinician works at a facility
just because names or addresses look similar.

Keep unmatched CMS records separate.

Never create fabricated provider affiliations.

==================================================
5. RESEARCH RELEVANCE CORRECTION
==================================================

M4B retrieved PMID 39046104 (dementia research)
for a pediatric dental anxiety query.

Investigate why.

Implement deterministic relevance safeguards:
- Clinical topic matching
- Title and abstract relevance checks
- Bounded query refinement
- Rejection of unrelated studies
- Explicit exclusion reasons
- Tests for irrelevant-but-valid PMIDs

Do not use keyword overlap alone as proof of
clinical relevance.

Preserve valid research records and provenance.

Never fabricate replacement publications.

==================================================
6. LANGGRAPH INTEGRATION
==================================================

Integrate CMS retrieval into the existing workflow.

Keep:
- Live NPPES provider retrieval
- Live PubMed evidence retrieval
- Local Gemma 4 planning and synthesis
- Deterministic validation
- MedlinePlus fixtures clearly identified

Add CMS data only where a reliable join is possible.

Preserve provider identity, enrollment data,
research evidence and quality measures as distinct
data categories.

Never translate missing quality data into low quality.

==================================================
7. CLI DEMONSTRATION
==================================================

Run:

healthcare-agents search \
  --query "Find pediatric dentists in Houston" \
  --verbose

Show:
- Live NPPES data
- Live PubMed evidence
- Relevant CMS records, if available
- Unmatched CMS records handled safely
- Provenance and retrieval status
- Explicit unknown fields
- MedlinePlus still simulated

Also demonstrate a provider or facility category
with confirmed CMS dataset coverage so that the
new CMS client is exercised with real records.

==================================================
8. TESTING
==================================================

Add offline tests for:
- Dataset discovery
- Dataset metadata and schemas
- Pagination
- Record normalization
- NPI/entity matching
- Missing identifiers
- Unmatched providers
- Invalid or absent quality fields
- HTTP failures and timeouts
- Research topical relevance regression
- LangGraph workflow integration
- Provenance preservation

Add opt-in live integration tests against actual CMS
dataset endpoints.

Execute an end-to-end Gemma 4 + LangGraph workflow
with live NPPES, PubMed and applicable CMS data.

Maintain >=90% offline coverage.

Run all existing M1–M4B regression tests.

==================================================
9. DOCUMENTATION AND PNG DIAGRAM
==================================================

Create:

docs/antigravity/M04C-cms/
    prompt.md
    commands.md
    implementation.md
    verification.md

Create:
docs/milestones/M04C-cms.md

Update:
- README.md
- docs/architecture/README.md
- docs/antigravity/README.md
- .env.example

Create:
docs/images/m4c_workflow.png

Use the preferred M4A/M4B architecture design.

PNG must be the embedded README format.
Preserve an editable source separately.

Clearly distinguish:
- NPPES provider identities
- PubMed clinical research
- CMS supported provider/facility data
- MedlinePlus simulated fixtures

Verify the PNG is readable and renders on GitHub.

==================================================
10. QUALITY GATES AND RELEASE
==================================================

Run:
- pytest and coverage
- Ruff lint
- Ruff format check
- mypy
- Python package build
- Clean wheel installation
- CLI smoke tests
- Live CMS API tests
- Full live LangGraph tests

Document actual results.

Work on main ONLY.

After ALL checks pass:
1. Commit to main.
2. Push main.
3. Verify GitHub Actions CI succeeds.
4. Create annotated tag v0.4.2-m04c.
5. Push and verify remote tag.

Never force-push or overwrite old tags.

==================================================
FINAL REPORT
==================================================

Include:
1. Actual CMS datasets selected and dataset IDs
2. Fields and identifiers supported
3. Live API sample results
4. Matching and nonmatching cases
5. PubMed relevance correction results
6. Live LangGraph execution
7. Tests and coverage
8. Ruff, mypy and build outcomes
9. PNG architecture verification
10. Git commit and annotated tag
11. GitHub CI status
12. Limitations and unavailable data
13. M4C complete/incomplete decision

Do not begin M4D until M4C passes all gates.
```
