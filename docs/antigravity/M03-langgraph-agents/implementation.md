# Milestone M03: Implementation Details

## 1. Overview & Objectives

Milestone M03 establishes the multi-agent orchestration architecture for the Open Healthcare Agentic Platform. Using **LangGraph** (`langgraph>=0.2.0`), a typed cyclic graph coordinates planning, provider candidate retrieval, clinical research gathering, rule-based verification, and grounded answer synthesis.

In accordance with the M3 specification:
- Retrieval is powered by **deterministic synthetic fixtures** with explicit test-data indicators (`is_simulated=True`), preparing standard interfaces for NPPES, PubMed, CMS, and MedlinePlus live connectors in M4.
- Fact checking is enforced by **deterministic Python verification**, not delegated to LLM hallucinations.
- Local inference is served through the existing **Gemma 4 (`gemma4:e2b`) + Ollama** adapter implemented in M2.

---

## 2. Package Architecture & Created Modules

### Package Structure
```
src/healthcare_agents/
    agents/
        __init__.py           # Clean agent component exports
        planner.py            # Gemma 4 intent & search plan generation with fallback heuristics
        provider.py           # Provider candidate retrieval & citation tracking
        evidence.py           # Clinical studies & patient education retrieval
        validator.py          # Deterministic Python validation rules (NPI, deduplication, claims)
        answer.py             # Grounded response synthesis with evidence constraints
    retrieval/
        __init__.py           # Retrieval interfaces & fixture exports
        base.py               # Abstract BaseProviderRetriever, BaseEvidenceRetriever, data models
        fixtures.py           # Deterministic test fixtures for Houston/Austin specialties
    workflows/
        __init__.py           # Export run_healthcare_workflow & compile graph
        state.py              # TypedDict graph state (HealthcareWorkflowState, SearchPlan, ValidationResults)
        healthcare_graph.py   # LangGraph StateGraph coordination and execution pipeline
```

---

## 3. Detailed Component Architecture

### A. Graph State (`workflows/state.py`)
Tracks the end-to-end multi-agent execution context:
- `request_id`: Unique invocation UUID
- `original_query`: Original user text prompt
- `search_plan`: Structured `SearchPlan` (intent, location, specialty, queries, evidence needs)
- `provider_candidates`: List of retrieved `ProviderRecord` objects
- `clinical_evidence`: List of retrieved `ClinicalEvidenceRecord` objects
- `patient_education_evidence`: List of patient guidance records
- `citations`: List of formatted citation strings
- `validation_results`: Structured `ValidationResults` with deduplication and integrity flags
- `unsupported_claims`: Detected discrepancies or claims lacking provider evidence
- `final_answer`: Grounded Markdown response synthesized from evidence
- `errors`: List of caught non-fatal agent errors
- `execution_metadata`: Stage timestamps, durations, and model runtime metadata

### B. Planner Agent (`agents/planner.py`)
- Employs local Gemma 4 (`gemma4:e2b`) to parse natural language healthcare queries into a structured JSON `SearchPlan`.
- Robust parsing extracts JSON payloads even when the model includes conversational prefixes or markdown code fences.
- Deterministic fallback heuristics dynamically detect locations (e.g. Houston, Austin, Dallas) and specialties (pediatric dentistry, cardiology, oncology) if model output is malformed or offline.

### C. Provider & Evidence Retrieval Abstractions (`retrieval/base.py` & `retrieval/fixtures.py`)
- `BaseProviderRetriever`: Defines abstract `search_providers(specialty, location, limit)`.
- `BaseEvidenceRetriever`: Defines `search_clinical_evidence(topic, limit)` and `search_patient_education(condition, limit)`.
- `FixtureProviderRetriever`: Deterministic mock provider data with verified NPIs, CMS facility ratings, and practice metadata.
- `FixtureEvidenceRetriever`: Deterministic peer-reviewed PubMed and MedlinePlus guidance fixtures.
- Every fixture clearly declares `is_simulated = True`.

### D. Deterministic Validator (`agents/validator.py`)
- **Zero Hallucinated Trust**: Does not use an LLM to declare facts verified.
- Checks required NPI and provider name fields.
- Deduplicates provider records by NPI.
- Validates source provenance and builds citation registries.
- Flags missing evidence or unsupported provider credentials.

### E. Answer Agent (`agents/answer.py`)
- Prompts Gemma 4 to synthesize a patient/clinician summary strictly adhering to supplied records.
- Injects explicit disclaimers:
  - Clear notification that retrieval results are simulated demonstration fixtures.
  - Mandatory medical disclaimer that the platform is for research/education only.
- Deterministic Markdown fallback generator ensures reliable CLI and API output even under inference failures.

### F. LangGraph Workflow Graph (`workflows/healthcare_graph.py`)
- Builds an executable `StateGraph[HealthcareWorkflowState]`.
- Linear, bounded execution flow:
  `START -> planner -> provider_retrieval -> evidence_retrieval -> validator -> answer_synthesis -> END`
- Wraps execution in `run_healthcare_workflow(query, model_adapter, timeout_seconds=60)`.

---

## 4. CLI Extension (`src/healthcare_agents/cli.py`)

Added the `search` subcommand:
```bash
healthcare-agents search --query "Find pediatric dentists in Houston" [--verbose]
```
- Injects local model adapter automatically.
- Live-renders workflow execution stages with Rich console styling.
- Renders synthesized answers, formatted citations, and clear demonstration disclaimers.
- Preserves all M1 and M2 commands (`--version`, `health`, `model status`, `model chat`).

---

## 5. Architectural Decisions & Guardrails

1. **Deterministic Verification Over LLM Self-Evaluation**:
   In healthcare search, LLM self-evaluation is prone to hallucination loops. Deterministic Python validation guarantees 100% adherence to schema, deduplication, and provenance rules.
2. **Fixture Grounding in M3**:
   Isolating multi-agent graph mechanics from external network dependencies (NPPES, PubMed) ensures fast, deterministic testing and reproducible CI builds. Live API integration is cleanly reserved for M4A–M4E.
3. **Opt-in Live Tests (`HEALTHCARE_AGENTS_LIVE_TESTS`)**:
   Enables 100% offline, zero-dependency testing on cloud CI (GitHub Actions) while enforcing live local verification against real Ollama inference before milestone tagging.
