"""Evidence Agent: Retrieves biomedical literature and patient education records."""

from __future__ import annotations

from typing import Any

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    ClinicalEvidenceRecord,
)
from healthcare_agents.retrieval.fixtures import FixtureEvidenceRetriever
from healthcare_agents.workflows.state import HealthcareWorkflowState


def retrieve_evidence(
    state: HealthcareWorkflowState,
    evidence_retriever: BaseEvidenceRetriever | None = None,
) -> dict[str, Any]:
    """Execute evidence retrieval for topics identified in search plan."""
    plan = state.get("search_plan", {})
    metadata = dict(state.get("execution_metadata", {}))
    citations = list(state.get("citations", []))
    errors = list(state.get("errors", []))

    retriever = evidence_retriever or FixtureEvidenceRetriever()
    topics = plan.get("evidence_topics", [])
    topic_str = " ".join(topics) if topics else state.get("original_query", "")

    all_evidence: list[ClinicalEvidenceRecord] = []
    try:
        all_evidence = list(retriever.search_evidence(topic=topic_str, limit=5))
    except Exception as err:
        errors.append(f"Evidence retrieval failure ({type(retriever).__name__}): {err}")

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

    # MedlinePlus consumer education remains simulated fixture in M4B
    if not patient_education:
        fixture_retriever = FixtureEvidenceRetriever()
        medline_fixtures = fixture_retriever.search_evidence(
            topic=topic_str, evidence_type="patient_education", limit=2
        )
        for med_item in medline_fixtures:
            if med_item.evidence_type == "patient_education":
                patient_education.append(med_item)
                cite = (
                    f"[{med_item.source}: {med_item.citation_ref}] "
                    f"{med_item.title} ({med_item.year})"
                )
                if cite not in citations:
                    citations.append(cite)

    metadata["clinical_evidence_count"] = len(clinical_evidence)
    metadata["patient_education_count"] = len(patient_education)
    metadata["evidence_retriever"] = type(retriever).__name__
    metadata["evidence_completed"] = True

    return {
        "clinical_evidence": clinical_evidence,
        "patient_education_evidence": patient_education,
        "citations": citations,
        "execution_metadata": metadata,
        "errors": errors,
    }
