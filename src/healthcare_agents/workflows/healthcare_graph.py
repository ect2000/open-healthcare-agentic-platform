"""Executable LangGraph multi-agent healthcare discovery workflow."""

from __future__ import annotations

import uuid
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from healthcare_agents.agents.answer import synthesize_answer
from healthcare_agents.agents.evidence import retrieve_evidence
from healthcare_agents.agents.planner import plan_query
from healthcare_agents.agents.provider import retrieve_providers
from healthcare_agents.agents.validator import validate_records
from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BaseProviderRetriever,
)
from healthcare_agents.workflows.state import HealthcareWorkflowState


def create_healthcare_graph(
    model_adapter: BaseModelAdapter | None = None,
    provider_retriever: BaseProviderRetriever | None = None,
    evidence_retriever: BaseEvidenceRetriever | None = None,
) -> StateGraph[HealthcareWorkflowState]:
    """Build and return an uncompiled StateGraph for healthcare multi-agent discovery."""
    workflow: StateGraph[HealthcareWorkflowState] = StateGraph(HealthcareWorkflowState)

    # Node wrappers injecting dependencies
    def planner_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return plan_query(state=state, model_adapter=model_adapter)

    def provider_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return retrieve_providers(state=state, provider_retriever=provider_retriever)

    def evidence_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        return retrieve_evidence(state=state, evidence_retriever=evidence_retriever)

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
