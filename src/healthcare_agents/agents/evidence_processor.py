"""Evidence processing node for the LangGraph healthcare discovery workflow.

Integrates normalization, deterministic deduplication, explainable relevance
scoring, source-specific ranking, and provenance registry generation.
"""

from __future__ import annotations

from typing import Any

from healthcare_agents.evidence.deduplication import (
    deduplicate_cms_records,
    deduplicate_medlineplus_topics,
    deduplicate_providers,
    deduplicate_pubmed_articles,
)
from healthcare_agents.evidence.normalization import (
    normalize_clinical_evidence_record,
    normalize_cms_quality_record,
    normalize_provider_record,
)
from healthcare_agents.evidence.provenance import (
    build_provenance_registry,
)
from healthcare_agents.evidence.ranking import rank_evidence_collection
from healthcare_agents.evidence.relevance import filter_and_score_evidence
from healthcare_agents.evidence.schemas import (
    StructuredDiscoveryResult,
    UnifiedEvidenceItem,
)
from healthcare_agents.workflows.state import HealthcareWorkflowState


def process_evidence_node(state: HealthcareWorkflowState) -> dict[str, Any]:
    """Execute normalization, deduplication, relevance filtering, and ranking."""
    query = state.get("original_query", "")
    search_plan = state.get("search_plan", {})
    metadata = dict(state.get("execution_metadata", {}))

    providers_raw = state.get("provider_candidates", [])
    pubmed_raw = state.get("clinical_evidence", [])
    patient_edu_raw = state.get("patient_education_evidence", [])
    cms_raw = state.get("cms_quality", [])

    # 1. Normalize all retrieved records into UnifiedEvidenceItems
    norm_providers = [normalize_provider_record(p) for p in providers_raw]
    norm_pubmed = [normalize_clinical_evidence_record(e) for e in pubmed_raw]
    norm_medlineplus = [normalize_clinical_evidence_record(e) for e in patient_edu_raw]
    norm_cms = [normalize_cms_quality_record(q) for q in cms_raw]

    # 2. Deterministic deduplication
    dedup_providers = deduplicate_providers(norm_providers)
    dedup_pubmed = deduplicate_pubmed_articles(norm_pubmed)
    dedup_medlineplus = deduplicate_medlineplus_topics(norm_medlineplus)
    dedup_cms = deduplicate_cms_records(norm_cms)

    # 3. Explainable relevance filtering & scoring
    target_specialty = search_plan.get("specialty")
    target_city = search_plan.get("city")
    target_state = search_plan.get("state")
    evidence_topics = search_plan.get("evidence_topics", [])
    candidate_npis = [p.external_id for p in dedup_providers if p.external_id]

    relevant_prov, excl_prov = filter_and_score_evidence(
        dedup_providers,
        query_intent=query,
        target_specialty=target_specialty,
        target_city=target_city,
        target_state=target_state,
    )
    relevant_pm, excl_pm = filter_and_score_evidence(
        dedup_pubmed,
        query_intent=query,
        evidence_topics=evidence_topics,
    )
    relevant_mlp, excl_mlp = filter_and_score_evidence(
        dedup_medlineplus,
        query_intent=query,
        evidence_topics=evidence_topics,
    )
    relevant_cms, excl_cms = filter_and_score_evidence(
        dedup_cms,
        query_intent=query,
        candidate_npis=candidate_npis,
    )

    all_excluded = excl_prov + excl_pm + excl_mlp + excl_cms

    # 4. Source-specific explainable ranking
    ranked_prov, ranked_pm, ranked_cms, ranked_mlp = rank_evidence_collection(
        providers=relevant_prov,
        clinical_research=relevant_pm,
        cms_records=relevant_cms,
        patient_education=relevant_mlp,
    )

    all_unified: list[UnifiedEvidenceItem] = ranked_prov + ranked_pm + ranked_cms + ranked_mlp

    # 5. Build provenance records
    prov_registry = build_provenance_registry(all_unified)
    provenance_records = list(prov_registry.values())

    # Build stable citation identifiers list
    citation_ids = [item.citation_id for item in all_unified if item.citation_id]

    # 6. Construct structured discovery result shell (without final answer yet)
    relevance_explanations: list[str] = []
    for item in all_unified:
        if item.relevance.selection_reason:
            relevance_explanations.append(f"{item.citation_id}: {item.relevance.selection_reason}")

    missing_info: list[str] = []
    if not ranked_prov:
        missing_info.append(
            "No matching provider candidates discovered for the requested specialty/location."
        )
    if not ranked_pm:
        missing_info.append("No relevant clinical research articles matched the query intent.")
    if not ranked_cms:
        missing_info.append(
            "No CMS quality or performance measures available for discovered providers."
        )
    if not ranked_mlp:
        missing_info.append("No relevant patient education topics found for this query.")

    structured_result = StructuredDiscoveryResult(
        query=query,
        interpreted_intent=dict(search_plan),
        provider_candidates=ranked_prov,
        clinical_research=ranked_pm,
        cms_quality_data=ranked_cms,
        patient_education=ranked_mlp,
        excluded_items=all_excluded,
        provenance_records=provenance_records,
        relevance_explanations=relevance_explanations,
        missing_information=missing_info,
        source_errors=list(state.get("errors", [])),
        grounded_answer="",
    )

    # Convert back to original typed records for downstream backwards-compatibility
    filtered_providers = [
        item.original_provider for item in ranked_prov if item.original_provider is not None
    ]
    filtered_pubmed = [
        item.original_clinical for item in ranked_pm if item.original_clinical is not None
    ]
    filtered_edu = [
        item.original_clinical for item in ranked_mlp if item.original_clinical is not None
    ]
    filtered_cms = [item.original_cms for item in ranked_cms if item.original_cms is not None]

    metadata["evidence_processing_completed"] = True
    metadata["unified_evidence_count"] = len(all_unified)
    metadata["excluded_evidence_count"] = len(all_excluded)
    metadata["dedup_provider_count"] = len(ranked_prov)
    metadata["dedup_pubmed_count"] = len(ranked_pm)
    metadata["dedup_cms_count"] = len(ranked_cms)
    metadata["dedup_medlineplus_count"] = len(ranked_mlp)

    return {
        "provider_candidates": filtered_providers,
        "clinical_evidence": filtered_pubmed,
        "patient_education_evidence": filtered_edu,
        "cms_quality": filtered_cms,
        "unified_evidence": all_unified,
        "excluded_evidence": all_excluded,
        "provenance_records": provenance_records,
        "citations": citation_ids,
        "structured_discovery_result": structured_result,
        "execution_metadata": metadata,
    }
