"""Streamlit Web Application for the Open Healthcare Agentic Platform."""

from __future__ import annotations

import os

import streamlit as st

from healthcare_agents.api.schemas import SearchResponse
from healthcare_agents.ui.api_client import HealthcareApiClient
from healthcare_agents.ui.components import (
    render_agent_workflow_and_fanout,
    render_cms_data_section,
    render_disclaimer_banner,
    render_execution_observability,
    render_header,
    render_medlineplus_card,
    render_provenance_and_citations,
    render_provider_card,
    render_pubmed_card,
)

st.set_page_config(
    page_title="Open Healthcare Agentic Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.environ.get("API_BASE_URL") or os.environ.get(
    "HEALTHCARE_AGENTS_API_URL", "http://127.0.0.1:8000"
)
api_client = HealthcareApiClient(base_url=API_BASE_URL, timeout=90.0)


def main() -> None:
    """Main Streamlit application execution."""
    render_header()

    with st.sidebar:
        st.subheader("⚙️ Platform Control")
        api_health = api_client.check_health()
        api_ready = api_client.check_readiness()

        # Compact status panel
        mode_val = api_ready.retrieval_mode if api_ready else "live"
        mode_badge = "🧪 Fixtures" if mode_val == "fixtures" else "🟢 Live Federal"
        ollama_status = (
            "✅ Online" if (api_ready and api_ready.ollama_service_available) else "❌ Offline"
        )
        model_status = "✅ Available" if (api_ready and api_ready.model_installed) else "❌ Missing"
        model_name = api_ready.model_name if api_ready else "gemma4:e2b"
        api_online = bool(api_health and api_health.status == "healthy")

        st.markdown(
            f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 0.65rem 0.8rem; margin-bottom: 0.85rem; color: #f8fafc; font-size: 0.85rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #94a3b8;">Backend API:</span>
                    <span style="font-weight: 600; color: {"#4ade80" if api_online else "#f87171"};">{"Online" if api_online else "Offline"}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #94a3b8;">Retrieval Mode:</span>
                    <span style="font-weight: 600; color: #38bdf8;">{mode_badge}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #94a3b8;">Ollama Host:</span>
                    <span style="font-weight: 600;">{ollama_status}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8;">Model ({model_name}):</span>
                    <span style="font-weight: 600;">{model_status}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='border-top: 1px solid #334155; margin: 0.5rem 0 0.8rem 0;'></div>",
            unsafe_allow_html=True,
        )
        st.subheader("⚡ Quick Demonstrations")
        st.caption("Click a preset to populate the search query without auto-executing:")

        if "selected_preset_idx" not in st.session_state:
            st.session_state["selected_preset_idx"] = None
        if "query_input_text" not in st.session_state:
            st.session_state["query_input_text"] = "Find pediatric dentists in Houston, Texas."

        presets = [
            {
                "idx": 1,
                "label": "1. Pediatric Dentist Discovery",
                "desc": "Houston pediatric dentists NPI registry search.",
                "query": "Find pediatric dentists in Houston, Texas.",
            },
            {
                "idx": 2,
                "label": "2. Best Dentists + Research",
                "desc": "Pediatric dentists in Houston + dental anxiety research.",
                "query": "Find the best pediatric dentists in Houston, Texas, and research pediatric dental anxiety.",
            },
            {
                "idx": 3,
                "label": "3. Tooth Cavity / Find Dentists",
                "desc": "Symptom routing (cavity -> General Dentistry) near Houston.",
                "query": "I live in Houston, Texas. I think I have a tooth cavity. Find the best dentists near me.",
            },
            {
                "idx": 4,
                "label": "4. Pediatric Dental Anxiety",
                "desc": "Clinical PubMed research on pediatric dental anxiety.",
                "query": "What does clinical research say about managing dental anxiety in children?",
            },
            {
                "idx": 5,
                "label": "5. Child Dental Health",
                "desc": "Evidence-based patient education from MedlinePlus.",
                "query": "Find evidence-based patient education about children's dental health and preventive care.",
            },
            {
                "idx": 6,
                "label": "6. Compare Healthcare Evidence",
                "desc": "Compare PubMed clinical literature and MedlinePlus topics.",
                "query": "Compare clinical research and patient education about pediatric dental anxiety.",
            },
        ]

        for p in presets:
            is_active = st.session_state.get("selected_preset_idx") == p["idx"]
            prefix = "👉 " if is_active else ""
            if st.button(
                f"{prefix}{p['label']}",
                key=f"preset_btn_{p['idx']}",
                use_container_width=True,
                type="secondary" if not is_active else "primary",
                help=str(p["desc"]),
            ):
                st.session_state["selected_preset_idx"] = p["idx"]
                st.session_state["query_input_text"] = p["query"]
                st.session_state["search_query_field"] = p["query"]
                st.rerun()

        mode_override = st.selectbox(
            "Mode Override",
            options=["Default (Settings)", "live", "fixtures"],
            index=0,
            help="Choose between live federal healthcare APIs or deterministic fixtures.",
        )
        selected_mode = None if mode_override.startswith("Default") else mode_override

        st.markdown("---")
        st.caption(
            "Vendor-neutral, open-source agentic healthcare architecture. Built with Gemma 4, "
            "LangGraph, FastAPI, and Streamlit."
        )

    render_disclaimer_banner(
        is_synthetic=(selected_mode == "fixtures"),
        retrieval_mode=selected_mode or "live",
    )

    st.subheader("🔎 Discover Healthcare Providers & Clinical Evidence")
    with st.form("search_form", clear_on_submit=False):
        col_query, col_btn = st.columns([5, 1])
        with col_query:
            user_query = st.text_input(
                "Enter your healthcare search query:",
                value=st.session_state.get(
                    "query_input_text",
                    "Find pediatric dentists in Houston, Texas.",
                ),
                placeholder="e.g. Find pediatric dentists in Houston and research on dental anxiety",
                label_visibility="collapsed",
                key="search_query_field",
            )
        with col_btn:
            submit_search = st.form_submit_button(
                "🔍 Search", use_container_width=True, type="primary"
            )

    if submit_search:
        if not user_query.strip():
            st.warning("Please enter a valid search query.")
            return

        with st.status(
            "Executing evidence-grounded agentic workflow...", expanded=True
        ) as status_box:
            st.write("1. 🧠 Planner Agent: Extracting clinical intent, specialty, and location...")
            st.write("2. 📡 Four-Source Retrieval: Querying NPPES, PubMed, CMS, and MedlinePlus...")
            st.write("3. ⚖️ Evidence Processor: Normalizing, deduplicating, and ranking results...")
            st.write(
                "4. 🛡️ Deterministic Validator: Verifying 10-digit NPIs and citation integrity..."
            )
            st.write("5. ✍️ Answer Synthesis: Grounding response with verified federal citations...")

            try:
                resp: SearchResponse = api_client.search(
                    query=user_query,
                    retrieval_mode=selected_mode,
                    result_limit=10,
                )
                status_box.update(
                    label="Discovery Workflow Complete!", state="complete", expanded=False
                )
            except Exception as exc:
                status_box.update(label="Workflow Failed", state="error", expanded=True)
                st.error(f"Failed to execute discovery workflow via FastAPI backend: {exc}")
                return

        st.markdown("## 📋 Grounded Healthcare Discovery Results")

        if resp.grounded_answer:
            st.markdown(
                f"""
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1.2rem; margin-bottom: 1.5rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem; margin-right: 0.5rem;">🤖</span>
                        <strong style="color: #166534; font-size: 1.05rem;">Grounded Synthesis (Gemma 4)</strong>
                    </div>
                    <div style="color: #1e293b; font-size: 0.95rem; line-height: 1.6;">
                        {resp.grounded_answer}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tab_providers, tab_research, tab_education, tab_cms, tab_workflow, tab_observability = (
            st.tabs(
                [
                    f"🩺 Providers ({len(resp.provider_candidates)})",
                    f"🔬 Research ({len(resp.clinical_research)})",
                    f"📖 Patient Education ({len(resp.patient_education)})",
                    f"🏛️ CMS Quality ({len(resp.cms_quality_data)})",
                    "⚡ Agent Workflow & Query Fan-Out",
                    f"🧠 Execution Telemetry ({len(resp.execution_events)})",
                ]
            )
        )

        with tab_providers:
            if resp.provider_candidates:
                st.markdown(
                    f"Found **{len(resp.provider_candidates)}** verified healthcare provider candidates:"
                )
                for prov in resp.provider_candidates:
                    render_provider_card(prov)
            else:
                st.info("No provider records matched the specified query parameters.")

        with tab_research:
            if resp.clinical_research:
                st.markdown(
                    f"Found **{len(resp.clinical_research)}** biomedical research publications:"
                )
                for pub in resp.clinical_research:
                    render_pubmed_card(pub)
            else:
                st.info("No biomedical literature was retrieved for this topic.")

        with tab_education:
            if resp.patient_education:
                st.markdown(
                    f"Found **{len(resp.patient_education)}** patient health education topics:"
                )
                for edu in resp.patient_education:
                    render_medlineplus_card(edu)
            else:
                st.info("No patient education topics were retrieved for this topic.")

        with tab_cms:
            render_cms_data_section(resp.cms_quality_data, resp.missing_information)

        with tab_workflow:
            render_agent_workflow_and_fanout(resp)

        with tab_observability:
            render_execution_observability(resp)

        render_provenance_and_citations(resp)


if __name__ == "__main__":
    main()
