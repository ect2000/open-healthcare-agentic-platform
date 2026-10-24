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

    retriever = evidence_retriever or FixtureEvidenceRetriever()
    topics = plan.get("evidence_topics", [])
    topic_str = " ".join(topics) if topics else state.get("original_query", "")

    all_evidence = list(retriever.search_evidence(topic=topic_str, limit=5))

    clinical_evidence: list[ClinicalEvidenceRecord] = []
    patient_education: list[ClinicalEvidenceRecord] = []

    for item in all_evidence:
        if item.evidence_type in ("research_study", "clinical_guideline"):
            clinical_evidence.append(item)
        else:
            patient_education.append(item)

        cite = f"[{item.source}: {item.citation_ref}] {item.title} ({item.year})"
        if cite not in citations:
            citations.append(cite)

    metadata["clinical_evidence_count"] = len(clinical_evidence)
    metadata["patient_education_count"] = len(patient_education)
    metadata["evidence_completed"] = True

    return {
        "clinical_evidence": clinical_evidence,
        "patient_education_evidence": patient_education,
        "citations": citations,
        "execution_metadata": metadata,
    }
