"""Streamlit Web Application for the Open Healthcare Agentic Platform."""

from __future__ import annotations

import os

import streamlit as st

from healthcare_agents.api.schemas import SearchResponse
from healthcare_agents.ui.api_client import HealthcareApiClient
from healthcare_agents.ui.components import (
    render_cms_data_section,
    render_disclaimer_banner,
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
        st.header("⚙️ Platform Control")
        api_health = api_client.check_health()
        api_ready = api_client.check_readiness()

        if api_health and api_health.status == "healthy":
            st.success(f"Backend API: Online (v{api_health.version})")
        else:
            st.error(f"Backend API: Offline at {API_BASE_URL}")

        if api_ready:
            st.info(
                f"🧠 Model: `{api_ready.model_name}`\n\n"
                f"📡 Retrieval Mode: `{api_ready.retrieval_mode}`\n\n"
                f"Ollama Online: {'✅' if api_ready.ollama_service_available else '❌'}\n\n"
                f"Model Available: {'✅' if api_ready.model_installed else '❌'}"
            )
        else:
            st.warning("Backend readiness probe uncontactable.")

        st.markdown("---")
        st.subheader("📚 Preset Demonstrations")
        demo_1 = st.button("1. Pediatric dentists in Houston", use_container_width=True)
        demo_2 = st.button("2. Pediatric dental anxiety & guidance", use_container_width=True)
        demo_3 = st.button("3. Child dental health education", use_container_width=True)
        demo_4 = st.button("4. Multi-source evidence comparison", use_container_width=True)

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

    preset_query = ""
    if demo_1:
        preset_query = "Find pediatric dentists in Houston"
    elif demo_2:
        preset_query = "Find pediatric dentists in Houston and research on pediatric dental anxiety"
    elif demo_3:
        preset_query = "Find patient education for child dental health"
    elif demo_4:
        preset_query = "Compare publicly available provider data and clinical literature for pediatric dentists in Houston"

    render_disclaimer_banner(is_synthetic=(selected_mode == "fixtures"))

    st.subheader("🔎 Discover Healthcare Providers & Clinical Evidence")
    with st.form("search_form", clear_on_submit=False):
        col_query, col_btn = st.columns([5, 1])
        with col_query:
            user_query = st.text_input(
                "Enter your healthcare search query:",
                value=preset_query
                if preset_query
                else "Find pediatric dentists in Houston and research on pediatric dental anxiety",
                placeholder="e.g. Find pediatric dentists in Houston and research on dental anxiety",
                label_visibility="collapsed",
            )
        with col_btn:
            submit_search = st.form_submit_button(
                "🔍 Search", use_container_width=True, type="primary"
            )

    if submit_search or preset_query:
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

        tab_providers, tab_research, tab_education, tab_cms = st.tabs(
            [
                f"🩺 Providers ({len(resp.provider_candidates)})",
                f"🔬 Research ({len(resp.clinical_research)})",
                f"📖 Patient Education ({len(resp.patient_education)})",
                f"🏛️ CMS Quality ({len(resp.cms_quality_data)})",
            ]
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

        render_provenance_and_citations(resp)


if __name__ == "__main__":
    main()
