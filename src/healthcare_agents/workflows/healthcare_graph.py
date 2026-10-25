"""Executable LangGraph multi-agent healthcare discovery workflow."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from healthcare_agents.config import get_settings
from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BasePatientEducationRetriever,
    BaseProviderRetriever,
    BaseQualityRetriever,
)
from healthcare_agents.retrieval.cms_client import CMSProviderDataRetriever
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.retrieval.medlineplus_client import MedlinePlusPatientEducationRetriever
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


def get_default_quality_retriever() -> BaseQualityRetriever:
    """Resolve CMS quality retriever based on application settings."""
    try:
        settings = get_settings()
        if settings.retrieval_mode == "live":
            return CMSProviderDataRetriever(
                base_url=settings.cms_api_url,
                timeout_seconds=settings.cms_timeout_seconds,
                max_retries=settings.cms_max_retries,
            )
    except Exception:
        pass
    return FixtureQualityRetriever()


def get_default_patient_education_retriever() -> BasePatientEducationRetriever:
    """Resolve MedlinePlus patient education retriever based on application settings."""
    try:
        settings = get_settings()
        if settings.retrieval_mode == "live":
            return MedlinePlusPatientEducationRetriever(
                base_url=settings.medlineplus_api_url,
                connect_url=settings.medlineplus_connect_url,
                timeout_seconds=settings.medlineplus_timeout_seconds,
                cache_ttl_seconds=settings.medlineplus_cache_ttl_seconds,
                max_retries=settings.medlineplus_max_retries,
            )
    except Exception:
        pass
    return FixturePatientEducationRetriever()


def create_healthcare_graph(
    model_adapter: BaseModelAdapter | None = None,
    provider_retriever: BaseProviderRetriever | None = None,
    evidence_retriever: BaseEvidenceRetriever | None = None,
    quality_retriever: BaseQualityRetriever | None = None,
    patient_education_retriever: BasePatientEducationRetriever | None = None,
) -> StateGraph[HealthcareWorkflowState]:
    """Build and return an uncompiled StateGraph for healthcare multi-agent discovery."""
    from healthcare_agents.agents.answer import synthesize_answer
    from healthcare_agents.agents.evidence_processor import process_evidence_node
    from healthcare_agents.agents.planner import plan_query
    from healthcare_agents.agents.validator import validate_records
    from healthcare_agents.planning.fanout import generate_fanout_plan
    from healthcare_agents.retrieval.parallel_retriever import execute_parallel_retrieval

    workflow: StateGraph[HealthcareWorkflowState] = StateGraph(HealthcareWorkflowState)
    resolved_provider_retriever = (
        provider_retriever if provider_retriever is not None else get_default_provider_retriever()
    )
    resolved_evidence_retriever = (
        evidence_retriever if evidence_retriever is not None else get_default_evidence_retriever()
    )
    resolved_quality_retriever = (
        quality_retriever if quality_retriever is not None else get_default_quality_retriever()
    )
    resolved_education_retriever = (
        patient_education_retriever
        if patient_education_retriever is not None
        else get_default_patient_education_retriever()
    )

    # Node wrappers injecting dependencies with monotonic execution telemetry
    def planner_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        t_start_iso = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        status = "completed"
        err_type = None
        output_sum = ""

        from healthcare_agents.observability import (
            get_current_span_id,
            get_current_trace_id,
            get_metrics,
            trace_span,
        )

        with trace_span(
            "agent.planner",
            attributes={"request_id": req_id, "stage": "Planner Agent"},
        ):
            active_trace_id = get_current_trace_id()
            active_span_id = get_current_span_id()
            try:
                res = plan_query(state=state, model_adapter=model_adapter)
                plan = res.get("search_plan", {})
                spec = plan.get("specialty", "")
                city_st = f"{plan.get('city', '')}, {plan.get('state', '')}"

                # Generate structured multi-source fan-out plan
                with trace_span(
                    "agent.query_fanout",
                    attributes={"request_id": req_id, "stage": "Query Fan-Out"},
                ):
                    fanout = generate_fanout_plan(
                        request_id=req_id,
                        original_query=state.get("original_query", ""),
                        search_plan=plan,
                        model_adapter=model_adapter,
                    )
                output_sum = (
                    f"Plan: {spec} in {city_st}; {len(fanout.queries)} queries planned across "
                    f"NPPES, PubMed, MedlinePlus, CMS"
                )
                return {
                    **res,
                    "fanout_plan": fanout.model_dump(),
                    "execution_events": events,
                }
            except Exception as e:
                status = "failed"
                err_type = type(e).__name__
                output_sum = str(e)
                raise
            finally:
                t1 = time.perf_counter()
                t_end_iso = datetime.now(UTC).isoformat()
                duration_ms = round((t1 - t0) * 1000.0, 2)
                try:
                    get_metrics().stage_duration_seconds.record(
                        (t1 - t0), {"stage": "planner", "status": status}
                    )
                except Exception:
                    pass
                events.append(
                    {
                        "request_id": req_id,
                        "trace_id": active_trace_id,
                        "span_id": active_span_id,
                        "stage": "Planner Agent",
                        "tool_name": "Gemma 4 Planner",
                        "status": status,
                        "start_time": t_start_iso,
                        "end_time": t_end_iso,
                        "duration_ms": duration_ms,
                        "query_summary": state.get("original_query", "")[:100],
                        "result_count": 1 if status == "completed" else 0,
                        "error_type": err_type,
                        "output_summary": output_sum,
                    }
                )

    def retrieval_orchestrator_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        errors = list(state.get("errors", []))
        fanout_dict = state.get("fanout_plan", {})

        from healthcare_agents.planning.fanout_schema import FanOutPlan

        if fanout_dict:
            fanout = FanOutPlan.model_validate(fanout_dict)
        else:
            fanout = generate_fanout_plan(
                request_id=req_id,
                original_query=state.get("original_query", ""),
                search_plan=state.get("search_plan", {}),
                model_adapter=model_adapter,
            )

        from healthcare_agents.observability import trace_span

        # Execute parallel retrieval
        with trace_span(
            "agent.parallel_retrieval",
            attributes={"request_id": req_id, "query_count": len(fanout.queries)},
        ):
            parallel_results = execute_parallel_retrieval(
                fanout_plan=fanout,
                provider_retriever=resolved_provider_retriever,
                evidence_retriever=resolved_evidence_retriever,
                patient_education_retriever=resolved_education_retriever,
                quality_retriever=resolved_quality_retriever,
                max_workers=4,
            )

        # Merge execution events from parallel branches
        for ev in parallel_results.get("execution_events", []):
            events.append(ev)

        # Build citations
        citations = list(state.get("citations", []))
        for item in parallel_results.get("clinical_evidence", []):
            url_part = f" <{item.pubmed_url}>" if item.pubmed_url else ""
            cite = f"[{item.source}: {item.citation_ref}] {item.title} ({item.year}){url_part}"
            if cite not in citations:
                citations.append(cite)

        for edu_item in parallel_results.get("patient_education_evidence", []):
            url_display = edu_item.official_url or edu_item.pubmed_url
            url_part = f" <{url_display}>" if url_display else ""
            cite = (
                f"[{edu_item.source}: {edu_item.citation_ref}] "
                f"{edu_item.title} ({edu_item.year}){url_part}"
            )
            if cite not in citations:
                citations.append(cite)

        errors.extend(parallel_results.get("errors", []))

        return {
            "provider_candidates": parallel_results.get("provider_candidates", []),
            "clinical_evidence": parallel_results.get("clinical_evidence", []),
            "patient_education_evidence": parallel_results.get("patient_education_evidence", []),
            "cms_quality": parallel_results.get("cms_quality", []),
            "unmatched_cms_records": parallel_results.get("unmatched_cms_records", []),
            "fanout_plan": parallel_results.get("fanout_plan", {}),
            "citations": citations,
            "execution_events": events,
            "errors": errors,
        }

    def processor_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        t_start_iso = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        status = "completed"
        err_type = None
        output_sum = ""
        item_count = 0

        from healthcare_agents.observability import (
            get_current_span_id,
            get_current_trace_id,
            get_metrics,
            trace_span,
        )

        with trace_span(
            "agent.evidence_processor",
            attributes={"request_id": req_id, "stage": "Evidence Processor"},
        ):
            active_trace_id = get_current_trace_id()
            active_span_id = get_current_span_id()
            try:
                res = process_evidence_node(state=state)
                excl_len = len(res.get("excluded_evidence", []))
                output_sum = f"Normalized {item_count} items, {excl_len} excluded"
                return {**res, "execution_events": events}
            except Exception as e:
                status = "failed"
                err_type = type(e).__name__
                output_sum = str(e)
                raise
            finally:
                t1 = time.perf_counter()
                raw_prov = len(state.get("provider_candidates", []))
                raw_clin = len(state.get("clinical_evidence", []))
                raw_edu = len(state.get("patient_education_evidence", []))
                raw_cms = len(state.get("cms_quality", []))
                raw_total = raw_prov + raw_clin + raw_edu + raw_cms
                try:
                    get_metrics().stage_duration_seconds.record(
                        (t1 - t0), {"stage": "evidence_processor", "status": status}
                    )
                except Exception:
                    pass
                events.append(
                    {
                        "request_id": req_id,
                        "trace_id": active_trace_id,
                        "span_id": active_span_id,
                        "stage": "Evidence Processor",
                        "tool_name": "UnifiedEvidencePipeline",
                        "status": status,
                        "start_time": t_start_iso,
                        "end_time": datetime.now(UTC).isoformat(),
                        "duration_ms": round((t1 - t0) * 1000.0, 2),
                        "query_summary": (
                            f"Input retrieved: {raw_total} total ({raw_prov} providers, "
                            f"{raw_clin} research, {raw_edu} education, {raw_cms} CMS)"
                        ),
                        "result_count": item_count,
                        "error_type": err_type,
                        "output_summary": (
                            f"Retained: {item_count} normalized & ranked items "
                            f"({len(res.get('excluded_evidence', []))} excluded)"
                            if status == "completed"
                            else output_sum
                        ),
                    }
                )

    def validation_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        t_start_iso = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        status = "completed"
        err_type = None
        output_sum = ""

        from healthcare_agents.observability import (
            get_current_span_id,
            get_current_trace_id,
            trace_span,
        )

        with trace_span(
            "agent.deterministic_validator",
            attributes={"request_id": req_id, "stage": "Deterministic Validator"},
        ):
            active_trace_id = get_current_trace_id()
            active_span_id = get_current_span_id()
            try:
                res = validate_records(state=state)
                val = res.get("validation_results", {})
                output_sum = (
                    f"Valid: {val.get('is_valid', True)}, notes: {len(val.get('notes', []))}"
                )
                return {**res, "execution_events": events}
            except Exception as e:
                status = "failed"
                err_type = type(e).__name__
                output_sum = str(e)
                raise
            finally:
                t1 = time.perf_counter()
                events.append(
                    {
                        "request_id": req_id,
                        "trace_id": active_trace_id,
                        "span_id": active_span_id,
                        "stage": "Deterministic Validator",
                        "tool_name": "ClinicalValidator",
                        "status": status,
                        "start_time": t_start_iso,
                        "end_time": datetime.now(UTC).isoformat(),
                        "duration_ms": round((t1 - t0) * 1000.0, 2),
                        "query_summary": (
                            f"Validate {len(state.get('unified_evidence', []))} items"
                        ),
                        "result_count": len(state.get("unified_evidence", [])),
                        "error_type": err_type,
                        "output_summary": output_sum,
                    }
                )

    def answer_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        t_start_iso = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        status = "completed"
        err_type = None
        ans_len = 0

        from healthcare_agents.observability import (
            get_current_span_id,
            get_current_trace_id,
            get_metrics,
            trace_span,
        )

        with trace_span(
            "agent.grounded_synthesis",
            attributes={"request_id": req_id, "stage": "Grounded Synthesis"},
        ):
            active_trace_id = get_current_trace_id()
            active_span_id = get_current_span_id()
            try:
                res = synthesize_answer(state=state, model_adapter=model_adapter)
                ans = res.get("final_answer", "")
                ans_len = len(ans)
                return {**res, "execution_events": events}
            except Exception as e:
                status = "failed"
                err_type = type(e).__name__
                raise
            finally:
                t1 = time.perf_counter()
                try:
                    get_metrics().stage_duration_seconds.record(
                        (t1 - t0), {"stage": "grounded_synthesis", "status": status}
                    )
                except Exception:
                    pass
                events.append(
                    {
                        "request_id": req_id,
                        "trace_id": active_trace_id,
                        "span_id": active_span_id,
                        "stage": "Grounded Synthesis",
                        "tool_name": "Gemma 4 Answer Synthesis",
                        "status": status,
                        "start_time": t_start_iso,
                        "end_time": datetime.now(UTC).isoformat(),
                        "duration_ms": round((t1 - t0) * 1000.0, 2),
                        "query_summary": (
                            f"Synthesize answer with {len(state.get('unified_evidence', []))} "
                            "citations"
                        ),
                        "result_count": 1 if ans_len > 0 else 0,
                        "error_type": err_type,
                        "output_summary": (
                            f"Generated grounded answer ({ans_len} chars)"
                            if status == "completed"
                            else f"Synthesis failed: {err_type}"
                        ),
                    }
                )

    workflow.add_node("planner", planner_node)
    workflow.add_node("retrieval_orchestrator", retrieval_orchestrator_node)
    workflow.add_node("evidence_processor", processor_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("answer_synthesis", answer_node)

    # Flow: START -> planner -> retrieval_orchestrator (parallel NPPES/PubMed/MedlinePlus + CMS)
    # -> evidence_processor -> validator -> answer_synthesis -> END
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "retrieval_orchestrator")
    workflow.add_edge("retrieval_orchestrator", "evidence_processor")
    workflow.add_edge("evidence_processor", "validator")
    workflow.add_edge("validator", "answer_synthesis")
    workflow.add_edge("answer_synthesis", END)

    return workflow


def run_healthcare_workflow(
    query: str,
    model_adapter: BaseModelAdapter | None = None,
    provider_retriever: BaseProviderRetriever | None = None,
    evidence_retriever: BaseEvidenceRetriever | None = None,
    quality_retriever: BaseQualityRetriever | None = None,
    patient_education_retriever: BasePatientEducationRetriever | None = None,
) -> HealthcareWorkflowState:
    """Helper executing compiled workflow with initial state."""
    graph_builder = create_healthcare_graph(
        model_adapter=model_adapter,
        provider_retriever=provider_retriever,
        evidence_retriever=evidence_retriever,
        quality_retriever=quality_retriever,
        patient_education_retriever=patient_education_retriever,
    )
    app: CompiledStateGraph[HealthcareWorkflowState] = graph_builder.compile()

    initial_state: HealthcareWorkflowState = {
        "request_id": str(uuid.uuid4()),
        "original_query": query,
        "search_plan": {},
        "provider_candidates": [],
        "clinical_evidence": [],
        "patient_education_evidence": [],
        "cms_quality": [],
        "unmatched_cms_records": [],
        "unified_evidence": [],
        "excluded_evidence": [],
        "provenance_records": [],
        "citations": [],
        "validation_results": {},
        "unsupported_claims": [],
        "final_answer": "",
        "errors": [],
        "execution_metadata": {},
        "execution_events": [],
    }

    raw_result = app.invoke(initial_state)
    return cast(HealthcareWorkflowState, raw_result)
