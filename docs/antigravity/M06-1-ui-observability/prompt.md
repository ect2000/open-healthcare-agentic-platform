PROJECT: open-healthcare-agentic-platform

MILESTONE: M6.1 — UI Experience & Agent Execution Visibility

BASELINE:
M6 Docker Compose is complete.
Release tag: v0.6.0-m06

GOAL:
Improve the healthcare application's visual design,
patient education readability, and agent execution
transparency without breaking existing functionality.

IMPORTANT:
- Do not start M7.
- Preserve all M1–M6 functionality.
- Work on a dedicated feature branch.
- Test and verify every implementation step.
- Do not fabricate execution telemetry.
- Preserve healthcare source accuracy.

==================================================
1. UI THEME & BRANDING
==================================================

Fix the nearly invisible application heading.

Title:
🏥 Open Healthcare Agentic Platform

Colors:
- Healthcare accent: #EF4444
- Open Healthcare: #38BDF8
- Agentic Platform: #F8FAFC
- Subtitle: #CBD5E1

Requirements:
- High contrast in dark and light themes.
- Consistent typography and spacing.
- Accessible text and controls.
- Preserve existing Streamlit functionality.
- Keep the current sidebar compact.
- Avoid oversized cards or unnecessary whitespace.

==================================================
2. PATIENT EDUCATION FORMATTING
==================================================

CURRENT PROBLEM:
MedlinePlus content is displayed as one long,
poorly formatted paragraph.

Examples:
"What is anesthesia?Anesthesia is..."
"Types of anesthesia:Local anesthesia..."

REQUIREMENTS:

1. Inspect MedlinePlus extraction and normalization.

2. Preserve:
   - Section headings
   - Paragraph breaks
   - Lists
   - Clinical terminology
   - Source attribution

3. Render compact patient education cards.

Each card must include:
   - Topic title
   - Source: MedlinePlus
   - Language
   - Short overview
   - Source link
   - Expandable detailed content

4. Default view should display a concise preview.

5. Add:
   "Read More"

6. Expanded view must support:
   - Headings
   - Paragraphs
   - Bullet lists
   - Readable spacing

7. Do not render raw untrusted HTML.

8. Do not fabricate medical summaries.

9. Any generated summary must be grounded,
   explicitly identified, and source-linked.

10. Preserve citations and URLs.

==================================================
3. AGENT EXECUTION VISIBILITY
==================================================

Add a new expandable section or tab:

"🧠 Agent Execution & Observability"

Display the actual workflow from LangGraph.

Possible stages:
- User Query
- Planner Agent
- Query Fan-Out
- NPPES Retrieval
- PubMed Retrieval
- CMS Retrieval
- MedlinePlus Retrieval
- Evidence Processor
- Gemma 4 Synthesis
- Grounded Response

IMPORTANT:
Inspect the actual implementation first.

Do not invent agents or execution stages.

For each executed stage display:
- Name
- Status
- Start timestamp
- End timestamp
- Duration in milliseconds
- Input summary
- Output summary
- Result count
- Errors, if any

Show actual retrieval queries sent to:
- NPPES
- PubMed
- CMS
- MedlinePlus

If query fan-out is not implemented,
show the existing retrieval routing behavior
and document query fan-out as a future feature.

Do not label static UI progress messages
as real execution telemetry.

==================================================
4. EXECUTION TIMELINE
==================================================

Add an execution timeline showing:

- Agent execution order
- Parallel retrieval operations
- Tool execution duration
- Model inference duration
- Total request duration

Requirements:
- Capture timestamps using a monotonic clock
  for duration calculations.
- Handle concurrent tool execution correctly.
- Do not sum overlapping durations to calculate
  total execution time.
- Display failures and timeouts accurately.
- Provide a compact summary at the top.

Example:

Planner          320 ms
NPPES          1,200 ms
PubMed         2,400 ms
CMS            1,800 ms
MedlinePlus    1,100 ms
Evidence         400 ms
Gemma 4       12,600 ms

These are examples only.
Display real measurements in the application.

==================================================
5. ARCHITECTURE & API
==================================================

Implement a reusable execution-event schema.

Recommended fields:
- request_id
- trace_id (optional)
- span_id (optional)
- parent_span_id (optional)
- stage
- tool_name
- status
- start_time
- end_time
- duration_ms
- query_summary
- result_count
- error_type

Requirements:

1. Keep instrumentation vendor-neutral.
2. Prepare for future OpenTelemetry integration.
3. Preserve backward compatibility of API responses.
4. Do not expose credentials, secrets, or PHI.
5. Do not log full sensitive prompts by default.
6. Do not change retrieval/ranking logic merely
   to support visualization.
7. Use bounded event storage and payload sizes.
8. Keep instrumentation overhead low.

==================================================
6. TESTING & VERIFICATION
==================================================

After every implementation step:
- Run relevant unit tests.
- Run integration tests.
- Run Ruff.
- Run mypy.
- Verify earlier functionality remains intact.

Final verification:

1. Run complete pytest suite.
2. Maintain >=90% test coverage.
3. Verify Docker Compose startup.
4. Verify FastAPI /health and /ready.
5. Verify native Ollama / Gemma 4.
6. Verify live healthcare retrieval.
7. Verify Streamlit rendering.
8. Run Playwright browser acceptance tests.
9. Test dark and light theme readability.
10. Test MedlinePlus formatting.
11. Test actual agent events and durations.
12. Test concurrent retrieval timing.
13. Verify citations and source attribution.
14. Test failures and timeout handling.
15. Verify no sensitive data appears in logs.

Capture screenshots of:
- Updated application header
- Patient education cards
- Agent execution timeline
- Query routing/fan-out details
- Final grounded search results

==================================================
7. DOCUMENTATION
==================================================

Create:

docs/milestones/M06-1-ui-observability.md

docs/antigravity/M06-1-ui-observability/
  prompt.md
  implementation.md
  commands.md
  verification.md

Update README with:
- M6.1 features
- Screenshots
- Execution workflow diagram
- Manual testing instructions

Preserve existing documentation.

==================================================
8. GIT & RELEASE
==================================================

1. Create feature branch:
   feature/m06-1-ui-observability

2. Preserve M6 release tag.

3. Complete implementation and verification.

4. Commit and push the feature branch only
   after all local checks pass.

5. Verify GitHub Actions CI.

6. Do not merge into main or create a release
   tag without explicit approval.

7. Do not start M7 automatically.

==================================================
ACCEPTANCE CRITERIA
==================================================

M6.1 is complete only when:

[ ] Title is readable and visually polished.
[ ] Patient education content is well formatted.
[ ] Actual agent execution events are visible.
[ ] Retrieval queries are inspectable.
[ ] Per-step timing is accurate.
[ ] Concurrent operations are represented correctly.
[ ] Existing M1-M6 functionality still works.
[ ] Healthcare evidence and citations are preserved.
[ ] Docker Compose runs successfully.
[ ] Browser acceptance tests pass.
[ ] CI is green.
[ ] Documentation is complete.

Do not mark M6.1 complete until all criteria pass.
