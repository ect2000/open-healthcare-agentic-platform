"""Provider Agent: Retrieves candidate clinicians and facilities using retrieval abstractions."""

from __future__ import annotations

from typing import Any

from healthcare_agents.retrieval.base import (
    BaseProviderRetriever,
    BaseQualityRetriever,
    CMSQualityRecord,
)
from healthcare_agents.retrieval.fixtures import (
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.workflows.state import HealthcareWorkflowState


def retrieve_providers(
    state: HealthcareWorkflowState,
    provider_retriever: BaseProviderRetriever | None = None,
    quality_retriever: BaseQualityRetriever | None = None,
) -> dict[str, Any]:
    """Execute provider search based on search plan and enrich with CMS quality data."""
    plan = state.get("search_plan", {})
    metadata = dict(state.get("execution_metadata", {}))
    errors = list(state.get("errors", []))

    retriever = provider_retriever or FixtureProviderRetriever()
    q_retriever = quality_retriever or FixtureQualityRetriever()
    specialty = plan.get("specialty")
    city = plan.get("city")
    state_code = plan.get("state")

    candidates = []
    try:
        candidates = list(
            retriever.search_providers(
                specialty=specialty,
                city=city,
                state=state_code,
                limit=5,
            )
        )

        # If strict search returned nothing, relax location to find specialty candidates
        if not candidates and specialty and (city or state_code):
            candidates = list(
                retriever.search_providers(
                    specialty=specialty,
                    limit=5,
                )
            )
    except Exception as err:
        errors.append(f"Provider retrieval failure ({type(retriever).__name__}): {err}")

    # Query CMS quality measures / affiliations for candidate NPIs
    cms_quality: list[CMSQualityRecord] = []
    unmatched_cms_records: list[CMSQualityRecord] = []

    for p in candidates:
        if p.npi and p.npi.isdigit() and len(p.npi) == 10:
            try:
                records = q_retriever.get_provider_quality(npi=p.npi)
                for q_rec in records:
                    # Exact NPI match check
                    if q_rec.npi == p.npi:
                        cms_quality.append(q_rec)
                    else:
                        unmatched_cms_records.append(q_rec)
            except Exception as q_err:
                errors.append(f"CMS quality lookup error for NPI {p.npi}: {q_err}")

    # Collect source citations
    citations = list(state.get("citations", []))
    for p in candidates:
        practice_info = f" ({p.practice_address})" if p.practice_address else ""
        cite = f"[{p.source}: NPI {p.npi}] {p.name} - {p.specialty}{practice_info}"
        if cite not in citations:
            citations.append(cite)

    for q in cms_quality:
        val = f"{q.measure_name}: {q.score}" if q.score else q.measure_name
        cite = f"[{q.source}: {q.dataset_id}] {q.entity_name} (NPI: {q.npi}) - {val}"
        if cite not in citations:
            citations.append(cite)

    metadata["provider_count"] = len(candidates)
    metadata["cms_quality_count"] = len(cms_quality)
    metadata["provider_completed"] = True
    metadata["provider_retriever"] = type(retriever).__name__
    metadata["quality_retriever"] = type(q_retriever).__name__

    return {
        "provider_candidates": candidates,
        "cms_quality": cms_quality,
        "unmatched_cms_records": unmatched_cms_records,
        "citations": citations,
        "execution_metadata": metadata,
        "errors": errors,
    }
