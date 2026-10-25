"""UI presentational components and card renderers for Streamlit."""

from __future__ import annotations

import streamlit as st

from healthcare_agents.api.schemas import EvidenceItemResponse, SearchResponse


def render_header() -> None:
    """Render the application header with titles and architectural metadata."""
    st.markdown(
        """
        <div style="padding: 1rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.5rem;">
            <h1 style="color: #0f172a; margin-bottom: 0.25rem; font-size: 2.2rem; font-weight: 700;">
                🏥 Open Healthcare Agentic Platform
            </h1>
            <p style="color: #475569; font-size: 1.1rem; margin: 0; font-weight: 500;">
                Evidence-Grounded Healthcare Discovery with Open Models and Cloud-Native AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer_banner(is_synthetic: bool = False) -> None:
    """Render the clinical and administrative disclaimer banner."""
    mode_badge = (
        "🧪 Synthetic / Fixture Mode" if is_synthetic else "🟢 Live Federal Healthcare Data Mode"
    )
    badge_color = "#fef3c7" if is_synthetic else "#dcfce7"
    badge_text_color = "#92400e" if is_synthetic else "#166534"

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
    """Render a MedlinePlus patient health education topic card."""
    with st.container():
        lang = item.metadata.get("language", "en")
        lang_badge = "English (en)" if lang == "en" else f"Spanish ({lang})"

        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.3rem;">
                    <h4 style="color: #065f46; margin: 0; font-size: 1.05rem;">📖 {item.title_or_name}</h4>
                    <span style="background-color: #d1fae5; color: #065f46; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">
                        {lang_badge}
                    </span>
                </div>
                <p style="color: #334155; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0.5rem;">
                    {item.metadata.get("summary", "Patient education topic from U.S. National Library of Medicine.")}
                </p>
                <div style="font-size: 0.8rem;">
                    <a href="{item.source_url}" target="_blank" style="color: #059669; text-decoration: none; font-weight: 600;">
                        🔗 Read Consumer Topic on MedlinePlus &rarr;
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
