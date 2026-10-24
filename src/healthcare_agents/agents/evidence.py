"""Evidence Agent: Retrieves biomedical literature and patient education records."""

from __future__ import annotations

from typing import Any

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BasePatientEducationRetriever,
    ClinicalEvidenceRecord,
)
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
)
from healthcare_agents.workflows.state import HealthcareWorkflowState


def retrieve_evidence(
    state: HealthcareWorkflowState,
    evidence_retriever: BaseEvidenceRetriever | None = None,
    patient_education_retriever: BasePatientEducationRetriever | None = None,
) -> dict[str, Any]:
    """Execute evidence retrieval for topics identified in search plan."""
    plan = state.get("search_plan", {})
    metadata = dict(state.get("execution_metadata", {}))
    citations = list(state.get("citations", []))
    errors = list(state.get("errors", []))

    ev_retriever = evidence_retriever or FixtureEvidenceRetriever()
    edu_retriever = patient_education_retriever or FixturePatientEducationRetriever()

    topics = plan.get("evidence_topics", [])
    topic_str = " ".join(topics) if topics else state.get("original_query", "")

    all_evidence: list[ClinicalEvidenceRecord] = []
    try:
        all_evidence = list(ev_retriever.search_evidence(topic=topic_str, limit=5))
    except Exception as err:
        errors.append(f"Evidence retrieval failure ({type(ev_retriever).__name__}): {err}")

    clinical_evidence: list[ClinicalEvidenceRecord] = []
    patient_education: list[ClinicalEvidenceRecord] = []

    for item in all_evidence:
        if item.evidence_type in ("research_study", "clinical_guideline"):
            clinical_evidence.append(item)
        else:
            patient_education.append(item)

        url_part = f" <{item.pubmed_url}>" if item.pubmed_url else ""
        cite = f"[{item.source}: {item.citation_ref}] {item.title} ({item.year}){url_part}"
        if cite not in citations:
            citations.append(cite)

    # Retrieve patient education from patient_education_retriever if not already populated
    if not patient_education:
        try:
            edu_candidates: list[ClinicalEvidenceRecord] = []
            queries_to_try = topics if topics else [topic_str]
            seen_record_urls: set[str] = set()

            for q_topic in queries_to_try:
                found = list(edu_retriever.search_topics(keyword=q_topic, limit=3))
                for f_item in found:
                    key = f_item.official_url or f_item.title
                    if key not in seen_record_urls:
                        seen_record_urls.add(key)
                        edu_candidates.append(f_item)
                if len(edu_candidates) >= 5:
                    break

            if not edu_candidates and topic_str:
                edu_candidates = list(edu_retriever.search_topics(keyword=topic_str, limit=5))

            for edu_item in edu_candidates[:5]:
                patient_education.append(edu_item)
                url_display = edu_item.official_url or edu_item.pubmed_url
                url_part = f" <{url_display}>" if url_display else ""
                cite = (
                    f"[{edu_item.source}: {edu_item.citation_ref}] "
                    f"{edu_item.title} ({edu_item.year}){url_part}"
                )
                if cite not in citations:
                    citations.append(cite)
        except Exception as err:
            retriever_name = type(edu_retriever).__name__
            errors.append(f"Patient education retrieval failure ({retriever_name}): {err}")

    metadata["clinical_evidence_count"] = len(clinical_evidence)
    metadata["patient_education_count"] = len(patient_education)
    metadata["evidence_retriever"] = type(ev_retriever).__name__
    metadata["patient_education_retriever"] = type(edu_retriever).__name__
    metadata["evidence_completed"] = True

    return {
        "clinical_evidence": clinical_evidence,
        "patient_education_evidence": patient_education,
        "citations": citations,
        "execution_metadata": metadata,
        "errors": errors,
    }
