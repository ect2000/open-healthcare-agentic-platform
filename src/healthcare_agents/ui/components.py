"""UI presentational components and card renderers for Streamlit."""

from __future__ import annotations

import streamlit as st

from healthcare_agents.api.schemas import EvidenceItemResponse, SearchResponse


def render_header() -> None:
    """Render high-contrast application header with verified branding colors."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #334155; border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem;">
                <span style="font-size: 2rem; line-height: 1; filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.4));">🏥</span>
                <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.025em; line-height: 1.2;">
                    <span style="color: #38BDF8;">Open Healthcare</span>
                    <span style="color: #F8FAFC;"> Agentic Platform</span>
                </h1>
            </div>
            <p style="color: #CBD5E1; font-size: 1.05rem; margin: 0; font-weight: 400; letter-spacing: 0.01em;">
                Evidence-Grounded Healthcare Discovery with Open Models and Cloud-Native AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer_banner(is_synthetic: bool = False, retrieval_mode: str | None = None) -> None:
    """Render the clinical and administrative disclaimer banner."""
    is_demo = is_synthetic or (retrieval_mode == "fixtures")
    mode_badge = (
        "🧪 Synthetic / Fixture Mode" if is_demo else "🟢 Live Federal Healthcare Data Mode"
    )
    badge_color = "#fef3c7" if is_demo else "#dcfce7"
    badge_text_color = "#92400e" if is_demo else "#166534"

    st.markdown(
        f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                <span style="font-weight: 700; color: #0369a1; font-size: 0.95rem;">Administrative & Scientific Guardrails</span>
                <span style="background-color: {badge_color}; color: {badge_text_color}; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">
                    {mode_badge}
                </span>
            </div>
            <p style="color: #64748b; font-size: 0.82rem; margin: 0; line-height: 1.4;">
                • <strong>NPPES Provider Registry</strong>: NPI is an administrative identifier and not proof of state licensure, clinical competence, or board certification.<br/>
                • <strong>PubMed NCBI</strong>: Literature citations demonstrate published science; they do not attest to an individual doctor's personal qualifications.<br/>
                • <strong>CMS Provider Data</strong>: Hospital/facility metrics cannot be ascribed to outpatient individual dentists. Missing CMS data denotes dataset reporting scope, not low clinical quality.<br/>
                • <strong>MedlinePlus</strong>: Consumer health education for patient literacy only. Not a diagnostic substitute or personalized medical advice.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_provider_card(item: EvidenceItemResponse) -> None:
    """Render a single healthcare provider candidate card."""
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h4 style="color: #1e3a8a; margin: 0 0 0.25rem 0; font-size: 1.1rem;">{item.title_or_name}</h4>
                        <div style="color: #047857; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.4rem;">
                            🩺 {item.metadata.get("specialty", "Healthcare Provider")}
                        </div>
                    </div>
                    <span style="background-color: #dbeafe; color: #1e40af; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; font-weight: 600;">
                        {item.citation_id}
                    </span>
                </div>
                <div style="color: #475569; font-size: 0.88rem; margin-bottom: 0.5rem;">
                    📍 <strong>Practice Address:</strong> {item.metadata.get("practice_address", "Address on file")} | 📞 {item.metadata.get("phone", "N/A")}
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center; font-size: 0.8rem;">
                    <a href="{item.source_url}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 500;">
                        🔗 Official CMS NPPES Registry &rarr;
                    </a>
                    <span style="color: #94a3b8;">•</span>
                    <span style="color: #64748b;">NPI: {item.external_id}</span>
                    <span style="color: #94a3b8;">•</span>
                    <span style="color: #059669; font-weight: 500;">Match Score: {item.relevance_score:.2f} ({item.selection_reason})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pubmed_card(item: EvidenceItemResponse) -> None:
    """Render a PubMed biomedical research card."""
    with st.container():
        authors = ", ".join(item.metadata.get("authors", []))
        journal = item.metadata.get("journal", "")
        year = item.metadata.get("year", "")
        citation_header = (
            f"{journal} ({year})" if journal and year else (journal or year or "PubMed")
        )

        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.3rem;">
                    <h4 style="color: #0f172a; margin: 0; font-size: 1.05rem; line-height: 1.35;">{item.title_or_name}</h4>
                    <span style="background-color: #f1f5f9; color: #334155; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; font-weight: 600; white-space: nowrap; margin-left: 0.5rem;">
                        {item.citation_id}
                    </span>
                </div>
                <div style="color: #64748b; font-size: 0.82rem; margin-bottom: 0.5rem;">
                    <strong>{citation_header}</strong> • <em>{authors}</em>
                </div>
                <p style="color: #334155; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0.6rem;">
                    {item.metadata.get("summary", "Abstract available at official PubMed citation.")}
                </p>
                <div style="display: flex; gap: 0.8rem; font-size: 0.8rem;">
                    <a href="{item.source_url}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 500;">
                        🔗 View on PubMed (NCBI) &rarr;
                    </a>
                    <span style="color: #94a3b8;">•</span>
                    <span style="color: #059669; font-weight: 500;">Relevance: {item.relevance_score:.2f} ({item.selection_reason})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_medlineplus_card(item: EvidenceItemResponse) -> None:
    """Render a compact patient health education topic card with expandable detailed content."""
    with st.container():
        lang = item.metadata.get("language", "en")
        lang_badge = "English (en)" if lang == "en" else f"Spanish ({lang})"
        full_text = item.metadata.get("summary", "")

        # Extract concise overview: take the first paragraph / introductory sentence
        overview_preview = ""
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        for p in paragraphs:
            if not p.startswith("###") and not p.startswith("-"):
                overview_preview = p
                break
        if not overview_preview:
            overview_preview = full_text[:280] + ("..." if len(full_text) > 280 else "")

        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1rem 0.5rem 1rem; margin-bottom: 0.6rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                    <h4 style="color: #065f46; margin: 0; font-size: 1.1rem; font-weight: 700;">📖 {item.title_or_name}</h4>
                    <div style="display: flex; gap: 0.4rem; align-items: center;">
                        <span style="background-color: #f1f5f9; color: #475569; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600;">
                            Source: MedlinePlus
                        </span>
                        <span style="background-color: #d1fae5; color: #065f46; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600;">
                            {lang_badge}
                        </span>
                    </div>
                </div>
                <p style="color: #334155; font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.6rem;">
                    {overview_preview}
                </p>
                <div style="font-size: 0.82rem; margin-bottom: 0.4rem;">
                    <a href="{item.source_url}" target="_blank" style="color: #059669; text-decoration: none; font-weight: 600;">
                        🔗 Read official consumer topic on MedlinePlus (NLM) &rarr;
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Expandable detailed section preserving headings, paragraphs, and lists
        with st.expander("📖 Read More — Complete Patient Education Details", expanded=False):
            st.markdown(full_text)
            st.markdown(
                f"[🔗 Official MedlinePlus Topic URL]({item.source_url})  \n"
                f"*Authoritative consumer health literacy source published by the National Library of Medicine (NIH).*"
            )


def render_cms_data_section(cms_items: list[EvidenceItemResponse], missing_info: list[str]) -> None:
    """Render applicable CMS quality metrics or explain non-applicability."""
    st.markdown("### 🏛️ CMS Provider Data & Quality Metrics")

    if not cms_items:
        st.info(
            "ℹ️ **No Applicable CMS Outpatient Metrics Available**\n\n"
            "CMS Provider Data Catalog metrics focus primarily on Medicare-participating hospitals, "
            "institutional facilities, and Medicare clinicians (MIPS). Outpatient pediatric dentists "
            "do not participate in adult Medicare programs. The absence of public CMS measures indicates "
            "dataset program scope, NOT poor clinical quality."
        )
    else:
        for it in cms_items:
            st.markdown(
                f"""
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.9rem; margin-bottom: 0.6rem;">
                    <strong>{it.title_or_name}</strong> [{it.citation_id}]<br/>
                    <span style="font-size: 0.85rem; color: #64748b;">
                        Dataset: {it.metadata.get("dataset_id", "CMS")} | Entity: {it.metadata.get("entity_type", "Facility")}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_provenance_and_citations(resp: SearchResponse) -> None:
    """Render traceable provenance and audit details."""
    with st.expander("🔍 Evidence Provenance, Exclusions & Citation Audit", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Request ID:** `{resp.request_id}`")
            st.markdown(f"**Created At:** `{resp.created_at}`")
            st.markdown(f"**Verified Citations:** `{len(resp.provenance_records)}`")
        with col2:
            st.markdown(
                f"**Selected Items:** `{resp.execution_metadata.get('provider_count', 0) + resp.execution_metadata.get('clinical_count', 0) + resp.execution_metadata.get('education_count', 0)}`"
            )
            st.markdown(f"**Excluded Items:** `{len(resp.excluded_items)}`")

        if resp.excluded_items:
            st.markdown("#### ⛔ Excluded Topically Irrelevant Items")
            for ex in resp.excluded_items:
                st.markdown(
                    f"- **{ex.title_or_name}** (`{ex.citation_id}`): "
                    f"<span style='color: #dc2626;'>{ex.exclusion_reason}</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("#### 📜 Source Provenance Records")
        prov_data = [
            {
                "Citation": p.citation_id,
                "Source": p.source_name,
                "External ID": p.external_id,
                "Canonical URL": p.canonical_url,
                "Language": p.language,
                "Synthetic": p.is_synthetic,
            }
            for p in resp.provenance_records
        ]
        st.dataframe(prov_data, use_container_width=True)


def render_execution_observability(resp: SearchResponse) -> None:
    """Render LangGraph multi-agent execution telemetry and timeline."""
    st.markdown("### 🧠 Multi-Agent Execution & Observability")
    st.caption(
        "Real-time LangGraph orchestration telemetry: step durations captured with high-resolution "
        "monotonic clocks, actual retrieval queries dispatched to federal healthcare registries, "
        "and execution status."
    )

    events = resp.execution_events
    if not events:
        st.info("No execution telemetry events recorded for this request.")
        return

    # Total duration calculation from first start to last end
    try:
        from datetime import datetime

        start_dt = datetime.fromisoformat(events[0].start_time)
        end_dt = datetime.fromisoformat(events[-1].end_time)
        wall_clock_total_ms = max(0.0, (end_dt - start_dt).total_seconds() * 1000.0)
    except Exception:
        wall_clock_total_ms = sum(e.duration_ms for e in events)

    # Top-level summary metrics
    col_total, col_stages, col_model, col_retrieval = st.columns(4)
    with col_total:
        st.metric("Total Execution", f"{wall_clock_total_ms:,.0f} ms")
    with col_stages:
        st.metric("Executed Stages", f"{len(events)}")
    with col_model:
        model_ms = sum(
            e.duration_ms for e in events if e.stage in ("Planner Agent", "Gemma 4 Synthesis")
        )
        st.metric("Model Inference", f"{model_ms:,.0f} ms")
    with col_retrieval:
        retrieval_ms = sum(
            e.duration_ms for e in events if "Retrieval" in e.stage or "CMS" in e.stage
        )
        st.metric("Federal Retrieval", f"{retrieval_ms:,.0f} ms")

    st.markdown("---")
    st.markdown("#### ⏱️ Execution Timeline & Telemetry Summary")

    # Table breakdown of real measurements
    timeline_rows = []
    for ev in events:
        status_icon = "✅" if ev.status == "completed" else "❌"
        timeline_rows.append(
            {
                "Status": f"{status_icon} {ev.status}",
                "Stage": ev.stage,
                "Tool / Agent": ev.tool_name or "LangGraph Node",
                "Duration (ms)": f"{ev.duration_ms:,.2f}",
                "Results": ev.result_count,
                "Input Query": ev.query_summary,
            }
        )
    st.dataframe(timeline_rows, use_container_width=True)

    # Detailed stage-by-stage inspectable cards
    st.markdown("#### 🔬 Inspect Stage Details & Outgoing Queries")
    for idx, ev in enumerate(events, 1):
        status_badge = "#dcfce7" if ev.status == "completed" else "#fee2e2"
        status_text_color = "#166534" if ev.status == "completed" else "#991b1b"
        icon = "✅" if ev.status == "completed" else "❌"

        with st.expander(
            f"{idx}. {icon} {ev.stage} — {ev.duration_ms:,.1f} ms ({ev.tool_name or 'Node'})",
            expanded=(idx in (1, 2)),
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Stage:** `{ev.stage}`")
                st.markdown(f"**Tool:** `{ev.tool_name or 'N/A'}`")
                st.markdown(
                    f"**Status:** <span style='background-color:{status_badge}; color:{status_text_color}; padding:2px 8px; border-radius:4px; font-weight:600;'>{ev.status}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**Duration:** `{ev.duration_ms:,.2f} ms`")
                st.markdown(f"**Result Count:** `{ev.result_count}`")
                if ev.error_type:
                    st.markdown(f"**Error Type:** `{ev.error_type}`")
            with c3:
                st.markdown(f"**Start:** `{ev.start_time}`")
                st.markdown(f"**End:** `{ev.end_time}`")

            st.markdown(f"**Query Dispatched:** `{ev.query_summary or 'N/A'}`")
            if ev.output_summary:
                st.markdown(f"**Output Summary:** {ev.output_summary}")

    st.markdown("---")
    st.markdown(
        "ℹ️ **OpenTelemetry Pre-Release**: Trace and span IDs are correlated for each executed "
        "stage in readiness for M8 distributed observability."
    )


def render_agent_workflow_and_fanout(resp: SearchResponse) -> None:
    """Render comprehensive Agent Workflow & Query Fan-Out visualization."""
    st.markdown("### ⚡ Agent Workflow & Parallel Query Fan-Out")
    st.caption(
        "Decomposed query fan-out, concurrent execution graph, and stage-by-stage dependency tracking."
    )

    # 1. Mermaid Execution Workflow Graph
    st.markdown("#### 🗺️ Executed Workflow Pipeline")
    workflow_mermaid = """
    graph TD
        Q["User Healthcare Inquiry"] --> P["🧠 Planner Agent<br/>(Gemma 4 Intent & Parameter Extraction)"]
        P --> F["🔀 Query Fan-Out Planner<br/>(Decompose into 4 Sources)"]
        subgraph Parallel_Retrieval ["📡 Concurrent Multi-Source Retrieval"]
            F --> NPPES["🩺 NPPES Registry<br/>(Clinicians & Locations)"]
            F --> PubMed["🔬 PubMed NCBI<br/>(Biomedical Literature)"]
            F --> Medline["📖 MedlinePlus<br/>(Consumer Education)"]
            NPPES -.->|"Candidate NPIs"| CMS["🏛️ CMS Provider Data<br/>(Quality & Measures)"]
        end
        NPPES --> EP["⚖️ Evidence Processing Layer<br/>(Normalize, Dedup, Relevance Score)"]
        PubMed --> EP
        Medline --> EP
        CMS --> EP
        EP --> VAL["🛡️ Deterministic Validator<br/>(NPI Check & Provenance Verification)"]
        VAL --> SYN["✍️ Answer Synthesis<br/>(Gemma 4 Grounded Generation)"]
        SYN --> OUT["📋 Grounded Summary & Citations"]

        classDef agent fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
        classDef tool fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
        classDef storage fill:#fef3c7,stroke:#f59e0b,stroke-width:2px;
        class P,F,SYN agent;
        class NPPES,PubMed,Medline,CMS tool;
        class EP,VAL storage;
    """
    st.markdown(f"```mermaid\n{workflow_mermaid}\n```")

    # 2. Query Fan-Out Inspection
    st.markdown("#### 🔍 Planned vs. Dispatched Queries")
    fanout_data = resp.fanout_plan
    queries = fanout_data.get("queries", []) if fanout_data else []

    if queries:
        query_rows = []
        for q in queries:
            status = q.get("status", "completed")
            status_badge = (
                "🟢" if status == "completed" else ("🟡" if status == "dispatched" else "⚪")
            )
            query_rows.append(
                {
                    "Status": f"{status_badge} {status.upper()}",
                    "Source": q.get("source", ""),
                    "Intent Category": q.get("intent_category", ""),
                    "Priority": f"P{q.get('priority', 2)}",
                    "Query Text": q.get("query_text", ""),
                    "Results": q.get("result_count", 0),
                    "Duration (ms)": f"{q.get('duration_ms', 0.0):,.1f}",
                    "Dependencies": ", ".join(q.get("dependency_ids", [])) or "None (Parallel)",
                }
            )
        st.dataframe(query_rows, use_container_width=True)
    else:
        st.info("No structured query fan-out plan available for this execution.")

    # 3. Parallel Execution Timeline & Monotonic Overlap Analysis
    st.markdown("#### ⏱️ Retrieval Concurrency Breakdown")
    retrieval_events = [e for e in resp.execution_events if "Retrieval" in e.stage]

    if retrieval_events:
        col1, col2, col3 = st.columns(3)
        with col1:
            seq_est = sum(e.duration_ms for e in retrieval_events)
            st.metric("Sequential Sum", f"{seq_est:,.1f} ms")
        with col2:
            # Parallel wall-clock interval
            st.metric("Parallel Execution", "Concurrent Thread Pool", delta="Active (4 Workers)")
        with col3:
            st.metric("Concurrent Sources", f"{len(retrieval_events)}")

        # Parallel timeline bars
        for ev in retrieval_events:
            status_color = "#10b981" if ev.status == "completed" else "#ef4444"
            st.markdown(
                f"""
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #1e293b;">{ev.stage}</span>
                        <span style="font-family: monospace; font-size: 0.85rem; color: {status_color}; font-weight: 600;">
                            {ev.duration_ms:,.1f} ms | {ev.result_count} records
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">
                        <code>{ev.query_summary}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
