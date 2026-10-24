PROJECT: open-healthcare-agentic-platform

MILESTONE: M3 — LangGraph Multi-Agent Orchestration
TARGET TAG: v0.3.0-m03
BRANCH: main ONLY

Read AGENTS.md and all previous milestone
documentation before modifying anything.

Follow all permanent testing, documentation,
Git and release rules.

==================================================
OBJECTIVE
==================================================

Build a working, testable, multi-agent healthcare
discovery workflow using LangGraph and the existing
Gemma 4 + Ollama model adapter from M2.

The workflow must coordinate planning, provider
retrieval, research evidence, validation, and
grounded answer synthesis.

IMPORTANT:
M3 focuses on agent orchestration, NOT live
healthcare API connectivity.

NPPES, PubMed, CMS and MedlinePlus connectors
will be implemented in M4A–M4E.

==================================================
STEP 1 — INSPECT EXISTING IMPLEMENTATION
==================================================

- Confirm main branch and clean working tree.
- Inspect existing model adapter and CLI.
- Verify the v0.2.0-m02 tag exists.
- Review pyproject.toml, tests and architecture.
- Preserve all M1 and M2 functionality.
- Reuse existing typed model interfaces.
- Do not download additional models unnecessarily.

==================================================
STEP 2 — LANGGRAPH FOUNDATION
==================================================

Add compatible LangGraph dependencies.

Create an organized agent workflow package:

src/healthcare_agents/
    agents/
        __init__.py
        planner.py
        provider.py
        evidence.py
        validator.py
        answer.py
    workflows/
        __init__.py
        healthcare_graph.py
        state.py
    retrieval/
        __init__.py
        base.py
        fixtures.py

Use explicit typed graph state.

State should track:
- request_id
- original_query
- search_plan
- provider_candidates
- clinical_evidence
- patient_education_evidence
- citations
- validation_results
- unsupported_claims
- final_answer
- errors
- execution_metadata

Only include state fields that are actually
needed and implemented.

==================================================
STEP 3 — IMPLEMENT FIVE AGENT COMPONENTS
==================================================

1. PLANNER AGENT

Use Gemma 4 to:
- Understand healthcare search intent.
- Extract location and specialty.
- Identify evidence requirements.
- Produce a validated structured search plan.

Handle invalid or incomplete model output.

2. PROVIDER AGENT

Create a provider retrieval abstraction.

For M3, use deterministic synthetic fixtures
with explicit test-data identifiers.

Do not invent real healthcare providers.

Prepare the interface for NPPES and CMS connectors.

3. EVIDENCE AGENT

Create a research retrieval abstraction.

Use controlled synthetic or explicitly labeled
test fixtures representing research evidence.

Prepare the interface for PubMed and MedlinePlus.

4. VALIDATION COMPONENT

Use deterministic Python checks for:
- Required fields
- Source provenance
- Duplicate records
- Citation references
- Unsupported provider-specific claims
- Missing evidence

Do not rely on an LLM to declare facts verified.

5. ANSWER AGENT

Use Gemma 4 to synthesize information from
validated records.

Ensure:
- Only supplied evidence may support claims.
- Citations refer to actual retrieved records.
- Missing or uncertain information is disclosed.
- No unsupported provider expertise is invented.
- Clearly identify demonstration fixture data.

==================================================
STEP 4 — LANGGRAPH EXECUTION
==================================================

Build a real executable LangGraph workflow.

Flow:

User Query
    |
Planner
    |
Provider + Evidence Retrieval
    |
Validation
    |
Answer Synthesis
    |
Structured Result

Implement:
- Explicit state transitions
- Bounded execution
- Error propagation
- Timeouts where appropriate
- Structured output
- Useful workflow execution metadata

Do not create unnecessary microservices.

Do not add Docker or Kubernetes yet.

==================================================
STEP 5 — CLI DEMONSTRATION
==================================================

Extend existing CLI with:

healthcare-agents search \
  --query "Find pediatric dentists in Houston"

Optional:

healthcare-agents search \
  --query "Find pediatric dentists in Houston" \
  --verbose

The CLI should:
- Execute the actual LangGraph workflow.
- Use the existing Gemma 4 model adapter.
- Display planning and execution stages.
- Show provider/evidence fixture records.
- Display citations and limitations.
- Clearly identify simulated retrieval results.

Preserve existing commands:
- healthcare-agents --version
- healthcare-agents health
- healthcare-agents model status
- healthcare-agents model chat

==================================================
STEP 6 — TESTING
==================================================

Create comprehensive offline tests for:
- Planner structured output
- Provider retrieval abstraction
- Evidence retrieval abstraction
- Duplicate detection
- Provenance preservation
- Unsupported claim detection
- Missing evidence
- Agent failures
- Malformed model responses
- Graph transitions
- Graph termination
- Final response schema
- Existing model adapter behavior
- CLI integration

Mock model inference for offline CI.

Add opt-in real integration tests using
local Gemma 4 and Ollama.

Live tests must execute the actual LangGraph
workflow, not merely call the model directly.

Verify:
- Planner uses real Gemma 4 inference.
- Agents pass state correctly.
- Validation runs.
- Answer generation executes.
- Workflow terminates.
- Output citations refer to fixture sources.
- Unsupported claims are not presented as facts.

Keep live tests optional for cloud CI, but
mandatory for M3 local milestone acceptance.

If live inference cannot run, do not mark M3
complete.

Run existing M1/M2 tests and prevent regressions.

==================================================
STEP 7 — DOCUMENTATION
==================================================

Create:

docs/antigravity/M03-langgraph-agents/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save:
- The complete original prompt
- Actual executed commands
- Test outputs and counts
- Architecture decisions
- Actual live model execution
- Failures, fixes and limitations

Create:
docs/milestones/M03-langgraph-agents.md

Update:
- README.md
- docs/architecture/README.md
- docs/antigravity/README.md

Add a workflow diagram under docs/images/
and embed the image in README.md.

Explain that M3 retrieval uses fixtures.
Do not claim live healthcare API integration.

==================================================
STEP 8 — QUALITY GATES
==================================================

Run:
- pytest with coverage
- Ruff lint
- Ruff format check
- mypy
- Python package build
- Wheel installation test
- CLI smoke tests
- Real Ollama + LangGraph integration tests

Record actual results.

Maintain at least the existing 90% coverage
threshold without weakening quality gates.

==================================================
STEP 9 — GIT & RELEASE
==================================================

Work directly on main only.

Do not create branches.

After all local checks pass:

1. Review Git diff and status.
2. Check for secrets and generated files.
3. Commit code and documentation.
4. Push main.
5. Verify GitHub Actions CI passes.
6. Create annotated tag v0.3.0-m03.
7. Push and verify tag.
8. Do not move or overwrite existing tags.

Update Python package version consistently
with the verified M3 release.

Do not tag if mandatory verification fails.

==================================================
FINAL REPORT
==================================================

Provide:
1. Implementation summary
2. Actual LangGraph architecture
3. Files created and modified
4. Live Gemma 4 workflow execution results
5. Test count and coverage
6. Ruff, mypy and build results
7. CLI demonstration
8. Git commit SHA
9. Annotated tag verification
10. GitHub Actions CI status
11. Known limitations
12. M3 complete/incomplete decision

Do not begin M4A until M3 is verified.
