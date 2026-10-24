"""Executable LangGraph multi-agent healthcare discovery workflow."""

from __future__ import annotations

import uuid
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from healthcare_agents.config import get_settings
from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BaseProviderRetriever,
)
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixtureProviderRetriever,
)
from healthcare_agents.retrieval.nppes_client import NPPESProviderRetriever
from healthcare_agents.retrieval.pubmed_client import PubMedEvidenceRetriever
from healthcare_agents.workflows.state import HealthcareWorkflowState


def get_default_provider_retriever() -> BaseProviderRetriever:
    """Resolve provider retriever based on application settings."""
    try:
        settings = get_settings()
        if settings.retrieval_mode == "live":
            return NPPESProviderRetriever(
                base_url=settings.nppes_api_url,
                timeout_seconds=settings.nppes_timeout_seconds,
                max_retries=settings.nppes_max_retries,
            )
    except Exception:
        pass
    return FixtureProviderRetriever()


def get_default_evidence_retriever() -> BaseEvidenceRetriever:
    """Resolve evidence retriever based on application settings."""
    try:
        settings = get_settings()
        if settings.retrieval_mode == "live":
            return PubMedEvidenceRetriever(
                base_url=settings.pubmed_api_url,
                timeout_seconds=settings.pubmed_timeout_seconds,
                max_retries=settings.pubmed_max_retries,
                api_key=settings.ncbi_api_key,
                email=settings.ncbi_email,
                tool=settings.ncbi_tool,
            )
    except Exception:
        pass
    return FixtureEvidenceRetriever()


def create_healthcare_graph(
    model_adapter: BaseModelAdapter | None = None,
    provider_retriever: BaseProviderRetriever | None = None,
    evidence_retriever: BaseEvidenceRetriever | None = None,
) -> StateGraph[HealthcareWorkflowState]:
    """Build and return an uncompiled StateGraph for healthcare multi-agent discovery."""
    from healthcare_agents.agents.answer import synthesize_answer
    from healthcare_agents.agents.evidence import retrieve_evidence
    from healthcare_agents.agents.planner import plan_query
    from healthcare_agents.agents.provider import retrieve_providers
    from healthcare_agents.agents.validator import validate_records

    workflow: StateGraph[HealthcareWorkflowState] = StateGraph(HealthcareWorkflowState)
    resolved_provider_retriever = (
        provider_retriever if provider_retriever is not None else get_default_provider_retriever()
    )
    resolved_evidence_retriever = (
        evidence_retriever if evidence_retriever is not None else get_default_evidence_retriever()
    )

    # Node wrappers injecting dependencies
    def planner_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return plan_query(state=state, model_adapter=model_adapter)

    def provider_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return retrieve_providers(state=state, provider_retriever=resolved_provider_retriever)

    def evidence_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return retrieve_evidence(state=state, evidence_retriever=resolved_evidence_retriever)

    def validation_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return validate_records(state=state)

    def answer_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return synthesize_answer(state=state, model_adapter=model_adapter)

    workflow.add_node("planner", planner_node)
    workflow.add_node("provider_retrieval", provider_node)
    workflow.add_node("evidence_retrieval", evidence_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("answer_synthesis", answer_node)

    # Flow: START -> planner -> provider_retrieval -> evidence_retrieval
    # -> validator -> answer_synthesis -> END
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "provider_retrieval")
    workflow.add_edge("provider_retrieval", "evidence_retrieval")
    workflow.add_edge("evidence_retrieval", "validator")
    workflow.add_edge("validator", "answer_synthesis")
    workflow.add_edge("answer_synthesis", END)

    return workflow


def run_healthcare_workflow(
    query: str,
    model_adapter: BaseModelAdapter | None = None,
    provider_retriever: BaseProviderRetriever | None = None,
    evidence_retriever: BaseEvidenceRetriever | None = None,
) -> HealthcareWorkflowState:
    """Helper executing compiled workflow with initial state."""
    graph_builder = create_healthcare_graph(
        model_adapter=model_adapter,
        provider_retriever=provider_retriever,
        evidence_retriever=evidence_retriever,
    )
    app: CompiledStateGraph[HealthcareWorkflowState] = graph_builder.compile()

    initial_state: HealthcareWorkflowState = {
        "request_id": str(uuid.uuid4()),
        "original_query": query,
        "search_plan": {},
        "provider_candidates": [],
        "clinical_evidence": [],
        "patient_education_evidence": [],
        "citations": [],
        "validation_results": {},
        "unsupported_claims": [],
        "final_answer": "",
        "errors": [],
        "execution_metadata": {},
    }

    raw_result = app.invoke(initial_state)
    return cast(HealthcareWorkflowState, raw_result)
