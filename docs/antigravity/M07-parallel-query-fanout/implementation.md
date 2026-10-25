# Milestone M7: Implementation Details

## Summary of Code Changes

### 1. Fix M6.1 Observability Inconsistencies
- **Count Semantics (Issue A)**:
  - Updated `processor_node` in `healthcare_graph.py` to differentiate raw input items (`Input retrieved: N total (...)`) from normalized and ranked output items (`Retained: M items (...)`).
  - Added structured counts to `execution_metadata` and UI tabs.
- **Fixture vs Live Mode (Issue B)**:
  - Updated `ANSWER_SYSTEM_PROMPT` and `synthesize_answer` in `src/healthcare_agents/agents/answer.py`: eliminated hardcoded prompt directives instructing Gemma 4 to claim records are fixtures during live mode.
  - Added `retrieval_mode` to `SearchResponse` in `src/healthcare_agents/api/schemas.py` and passed from `service.py`.
  - Updated `render_disclaimer_banner` in `src/healthcare_agents/ui/components.py` to display the verified mode dynamically.

### 2. Intelligent Query Fan-Out
- Created `src/healthcare_agents/planning/fanout_schema.py`:
  - `PlannedQuery`: Encapsulates `query_id`, `parent_request_id`, `source`, `query_text`, `search_params`, `intent_category`, `priority`, `status`, `duration_ms`, `error_message`, and `dependency_ids`.
  - `FanOutPlan`: Aggregates queries with deduplication and parameter validation.
- Created `src/healthcare_agents/planning/fanout.py`:
  - `generate_fanout_plan`: Decomposes inquiries using Gemma 4 with deterministic fallback.
  - `build_deterministic_fanout`: Generates targeted queries for NPPES, PubMed, MedlinePlus, and dependent CMS queries without requiring LLM calls.

### 3. Parallel Multi-Source Retrieval
- Created `src/healthcare_agents/retrieval/parallel_retriever.py`:
  - Concurrent dispatch of independent retrieval operations (NPPES, PubMed, MedlinePlus) using `concurrent.futures.ThreadPoolExecutor(max_workers=4)`.
  - Dependent phase execution: CMS Quality retrieval waits for candidate provider NPIs discovered in NPPES.
  - Resilient partial failure handling: If a single source fails or times out, surviving source records and citation integrity are preserved.
- Updated `src/healthcare_agents/workflows/healthcare_graph.py`:
  - Replaced sequential retrieval nodes with `retrieval_orchestrator` node executing the parallel engine.

### 4. Relevance Optimization & Guardrails
- Updated `src/healthcare_agents/evidence/relevance.py`:
  - Implemented specific condition guardrails in `assess_medlineplus_relevance`: excludes unrelated conditions (e.g., eating disorders, substance use, dementia) when processing dental inquiries.
  - Returns clear `exclusion_reason` recorded in `excluded_items`.

### 5. Agent Workflow & Fan-Out Visualization
- Updated `src/healthcare_agents/ui/components.py`:
  - Implemented `render_agent_workflow_and_fanout`: renders Mermaid workflow graph, planned vs. dispatched queries table with status badges and parameters, and parallel execution timeline.
- Updated `src/healthcare_agents/ui/app.py`:
  - Added "⚡ Agent Workflow & Query Fan-Out" tab to the application interface.

### 6. OpenTelemetry Readiness
- Extended `ExecutionEvent` schema in `api/schemas.py` with `query_id` and `dependency_ids` alongside existing `trace_id`, `span_id`, and `parent_span_id`.
