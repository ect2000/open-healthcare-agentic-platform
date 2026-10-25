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

### 7. UI/UX Polish & Visual Acceptance Enhancements
- **Compact Sidebar Status Panel**:
  - Replaced stacked notification banners with a unified, dark-slate (`#1e293b`) status badge container.
  - Dynamically renders actual runtime statuses (`Live Federal` vs `Fixture`, `Online`, `Available`) with zero hardcoded values.
- **Removed Excessive Sidebar Spacing**:
  - Eliminated duplicate `st.markdown("---")` dividers and extra vertical container margins.
  - Placed "Quick Demonstrations" directly below the status panel with clean, subtle border divider (`#334155`).
- **Synchronized Search Input**:
  - Bound preset selection to both `session_state["query_input_text"]` and `session_state["search_query_field"]`.
  - Clicking any of the 6 presets immediately displays the editable query in the primary search field without auto-executing search.
- **High-Contrast Mermaid Workflow Diagram**:
  - Injected explicit CSS classes with dark fills and `#ffffff` font styling across all pipeline stages:
    - User Inquiry: `#0f172a` (stroke: `#38bdf8`)
    - Planner & Synthesis: `#1e3a8a` (stroke: `#60a5fa`)
    - Query Fan-Out: `#581c87` (stroke: `#c084fc`)
    - Retrieval Sources: `#065f46` (stroke: `#34d399`)
    - Dependent CMS: `#78350f` (stroke: `#fbbf24`)
    - Evidence Processing & Validator: `#1e293b` (stroke: `#94a3b8`)
  - Guaranteed high contrast and readability across dark and light themes and varying viewports (1440px, 1280px, 768px).

### 8. Patient Education Bounded Fallback & Educational Tier Classification
- **Root Cause Analysis**:
  - MedlinePlus Web Service API uses an exact multi-word index. When Gemma 4 synthesized complex academic queries like `"managing dental anxiety in children"`, the API returned 0 records because no topic by that exact multi-clause name exists in MedlinePlus.
  - The system has authoritative consumer health topics covering this domain: `"child dental health"`, `"dental health"`, `"tooth decay"`, and `"anxiety"`.
- **Bounded Fallback Execution**:
  - Updated `run_medline_query` in `parallel_retriever.py`: If the primary keyword yields 0 items, bounded consumer-health fallback terms are queried based on detected domain entities (e.g. child dental health, tooth decay, anxiety/phobias).
  - Preserves exact user inquiry; does not alter query text.
- **Explainable Relevance Scoring**:
  - Updated `assess_medlineplus_relevance` in `evidence/relevance.py`:
    - Word-boundary matching to prevent incidental substring collisions (e.g., `'oral'` inside `'behavioral'`).
    - Stopword filtering for conversational query prefixes (`'find'`, `'best'`, `'research'`).
    - Clear distinction between **Directly relevant education** (e.g. `Child Dental Health`) and **Related general dental-health / anxiety education** (`Tooth Decay`, `Dental Health`, `Anxiety`).
    - Strict exclusion guardrail for unrelated conditions (`scleroderma`, `sleep disorders`, `eating disorders`, `diabetes complications`).
- **Regression Testing**:
  - Added `test_parallel_retrieval_medlineplus_bounded_fallback` to `tests/test_parallel_retrieval.py`.
  - Full suite passes: 162 passed, 15 skipped; total coverage 90.60%.
