# M7 Milestone Prompt & Requirements

**Milestone:** M7 — Intelligent Query Fan-Out, Parallel Retrieval, Relevance Optimization & Agent Workflow Visualization  
**Target Branch:** `feature/m07-parallel-query-fanout`  
**Baseline:** M6 release (`v0.6.0-m06`), M6.1 feature branch (`feature/m06-1-ui-observability` at commit `0a3846a`)

## Objectives & Core Directives

1. **Fix M6.1 Observability Inconsistencies:**
   - **Issue A (Count Semantics):** Resolve discrepancies between raw retrieved records, normalized records, deduplicated records, and final displayed records across UI and execution events.
   - **Issue B (Fixture vs. Live Mode):** Ensure retrieval mode is tracked per request and displayed accurately; eliminate hardcoded prompt directives in `answer.py` claiming records are fixtures when operating in live mode.

2. **Intelligent Query Fan-Out:**
   - Decompose single user healthcare queries into multi-query targeted retrieval plans across NPPES, PubMed, MedlinePlus, and CMS.
   - Schema `PlannedQuery` and `FanOutPlan` with priority, parameters, execution status, and dependency IDs.
   - Preserve original patient intent; deterministic fallback when LLM output is malformed; prevent PHI exposure.

3. **Parallel Healthcare Retrieval:**
   - Concurrently execute independent retrieval requests (NPPES, PubMed, MedlinePlus) using a bounded worker pool (`ThreadPoolExecutor`).
   - Enforce dependent execution (CMS Quality lookups wait for discovered provider NPIs).
   - Graceful partial failure tolerance and non-blocking retry/timeout behavior.

4. **Evidence Relevance Optimization:**
   - Transparent scoring and explicit exclusion reasons.
   - Exclude peripheral or unrelated medical conditions (e.g., eating disorders or dementia on dental inquiries).

5. **Agent Workflow Visualization:**
   - Add "Agent Workflow & Query Fan-Out" tab in Streamlit displaying the executed pipeline graph, query fan-out table, and concurrency timeline.

6. **Performance Benchmarking:**
   - Measure retrieval latency under sequential vs. parallel profiles, targeting $\ge 25\%$ reduction.

7. **OpenTelemetry Readiness:**
   - Incorporate `trace_id`, `span_id`, `parent_span_id`, `query_id`, and `dependency_ids` in telemetry events.

8. **Testing, Verification & Packaging:**
   - Full test suite, coverage $\ge 90\%$, Ruff, Mypy, Docker Compose, Playwright browser automation, and feature branch CI.
