"""Provider Agent: Retrieves candidate clinicians and facilities using retrieval abstractions."""

from __future__ import annotations

from typing import Any

from healthcare_agents.retrieval.base import BaseProviderRetriever
from healthcare_agents.retrieval.fixtures import FixtureProviderRetriever
from healthcare_agents.workflows.state import HealthcareWorkflowState


def retrieve_providers(
    state: HealthcareWorkflowState,
    provider_retriever: BaseProviderRetriever | None = None,
) -> dict[str, Any]:
    """Execute provider search based on the formulated search plan."""
    plan = state.get("search_plan", {})
    metadata = dict(state.get("execution_metadata", {}))

    retriever = provider_retriever or FixtureProviderRetriever()
    specialty = plan.get("specialty")
    city = plan.get("city")
    state_code = plan.get("state")

    candidates = list(
        retriever.search_providers(
            specialty=specialty,
            city=city,
            state=state_code,
            limit=5,
        )
    )

    # If strict search returned nothing, relax location to find specialty candidates
    if not candidates and specialty:
        candidates = list(
            retriever.search_providers(
                specialty=specialty,
                limit=5,
            )
        )

    # Collect source citations
    citations = list(state.get("citations", []))
    for p in candidates:
        cite = f"[{p.source}: NPI {p.npi}] {p.name} - {p.facility_name}"
        if cite not in citations:
            citations.append(cite)

    metadata["provider_count"] = len(candidates)
    metadata["provider_completed"] = True

    return {
        "provider_candidates": candidates,
        "citations": citations,
        "execution_metadata": metadata,
    }
