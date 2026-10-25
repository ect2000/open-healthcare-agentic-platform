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
    from healthcare_agents.agents.evidence import retrieve_evidence
    from healthcare_agents.agents.evidence_processor import process_evidence_node
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
        try:
            res = plan_query(state=state, model_adapter=model_adapter)
            plan = res.get("search_plan", {})
            spec = plan.get("specialty", "")
            city_st = f"{plan.get('city', '')}, {plan.get('state', '')}"
            topics_str = str(plan.get("evidence_topics", []))
            output_sum = f"Plan: {spec} in {city_st}; topics: {topics_str}"
            return {**res, "execution_events": events}
        except Exception as e:
            status = "failed"
            err_type = type(e).__name__
            output_sum = str(e)
            raise
        finally:
            t1 = time.perf_counter()
            t_end_iso = datetime.now(UTC).isoformat()
            duration_ms = round((t1 - t0) * 1000.0, 2)
            events.append(
                {
                    "request_id": req_id,
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

    def provider_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        plan = state.get("search_plan", {})
        spec = plan.get("specialty") or "healthcare provider"
        city = plan.get("city") or ""
        state_cd = plan.get("state") or ""
        nppes_query = f"specialty='{spec}', city='{city}', state='{state_cd}'"

        # 1. NPPES Provider Registry
        t0_nppes = time.perf_counter()
        t_start_nppes = datetime.now(UTC).isoformat()
        status_nppes = "completed"
        err_nppes = None
        candidates = []
        try:
            candidates = list(
                resolved_provider_retriever.search_providers(
                    specialty=plan.get("specialty"),
                    city=plan.get("city"),
                    state=plan.get("state"),
                    limit=5,
                )
            )
            if not candidates and plan.get("specialty") and (plan.get("city") or plan.get("state")):
                candidates = list(
                    resolved_provider_retriever.search_providers(
                        specialty=plan.get("specialty"),
                        limit=5,
                    )
                )
        except Exception as exc:
            status_nppes = "failed"
            err_nppes = type(exc).__name__
        finally:
            t1_nppes = time.perf_counter()
            events.append(
                {
                    "request_id": req_id,
                    "stage": "NPPES Retrieval",
                    "tool_name": type(resolved_provider_retriever).__name__,
                    "status": status_nppes,
                    "start_time": t_start_nppes,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1_nppes - t0_nppes) * 1000.0, 2),
                    "query_summary": nppes_query,
                    "result_count": len(candidates),
                    "error_type": err_nppes,
                    "output_summary": f"Retrieved {len(candidates)} provider records",
                }
            )

        # 2. CMS Quality Data
        t0_cms = time.perf_counter()
        t_start_cms = datetime.now(UTC).isoformat()
        status_cms = "completed"
        err_cms = None
        cms_quality = []
        unmatched_cms = []
        npis_queried = [p.npi for p in candidates if p.npi and p.npi.isdigit() and len(p.npi) == 10]
        try:
            for npi_val in npis_queried:
                try:
                    records = resolved_quality_retriever.get_provider_quality(npi=npi_val)
                    for q_rec in records:
                        if q_rec.npi == npi_val:
                            cms_quality.append(q_rec)
                        else:
                            unmatched_cms.append(q_rec)
                except Exception as q_exc:
                    err_cms = type(q_exc).__name__
        except Exception as exc:
            status_cms = "failed"
            err_cms = type(exc).__name__
        finally:
            t1_cms = time.perf_counter()
            events.append(
                {
                    "request_id": req_id,
                    "stage": "CMS Retrieval",
                    "tool_name": type(resolved_quality_retriever).__name__,
                    "status": status_cms,
                    "start_time": t_start_cms,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1_cms - t0_cms) * 1000.0, 2),
                    "query_summary": f"NPIs: {npis_queried[:3]} ({len(npis_queried)} total)"
                    if npis_queried
                    else "No candidate NPIs",
                    "result_count": len(cms_quality),
                    "error_type": err_cms,
                    "output_summary": f"Retrieved {len(cms_quality)} CMS quality metric records",
                }
            )

        res = retrieve_providers(
            state=state,
            provider_retriever=resolved_provider_retriever,
            quality_retriever=resolved_quality_retriever,
        )
        return {**res, "execution_events": events}

    def evidence_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        plan = state.get("search_plan", {})
        topics = plan.get("evidence_topics", [])
        topic_str = " ".join(topics) if topics else state.get("original_query", "")

        # 3. PubMed Retrieval
        t0_pubmed = time.perf_counter()
        t_start_pubmed = datetime.now(UTC).isoformat()
        status_pubmed = "completed"
        err_pubmed = None
        pubmed_count = 0
        try:
            pub_res = list(resolved_evidence_retriever.search_evidence(topic=topic_str, limit=5))
            pubmed_count = len(
                [x for x in pub_res if x.evidence_type in ("research_study", "clinical_guideline")]
            )
        except Exception as exc:
            status_pubmed = "failed"
            err_pubmed = type(exc).__name__
        finally:
            t1_pubmed = time.perf_counter()
            events.append(
                {
                    "request_id": req_id,
                    "stage": "PubMed Retrieval",
                    "tool_name": type(resolved_evidence_retriever).__name__,
                    "status": status_pubmed,
                    "start_time": t_start_pubmed,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1_pubmed - t0_pubmed) * 1000.0, 2),
                    "query_summary": f"topic='{topic_str[:80]}'",
                    "result_count": pubmed_count,
                    "error_type": err_pubmed,
                    "output_summary": f"Retrieved {pubmed_count} PubMed research articles",
                }
            )

        # 4. MedlinePlus Retrieval
        t0_medline = time.perf_counter()
        t_start_medline = datetime.now(UTC).isoformat()
        status_medline = "completed"
        err_medline = None
        medline_count = 0
        medline_query = topics[0] if topics else topic_str
        try:
            med_res = list(
                resolved_education_retriever.search_topics(keyword=medline_query, limit=5)
            )
            medline_count = len(med_res)
        except Exception as exc:
            status_medline = "failed"
            err_medline = type(exc).__name__
        finally:
            t1_medline = time.perf_counter()
            events.append(
                {
                    "request_id": req_id,
                    "stage": "MedlinePlus Retrieval",
                    "tool_name": type(resolved_education_retriever).__name__,
                    "status": status_medline,
                    "start_time": t_start_medline,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1_medline - t0_medline) * 1000.0, 2),
                    "query_summary": f"keyword='{medline_query[:80]}'",
                    "result_count": medline_count,
                    "error_type": err_medline,
                    "output_summary": f"Retrieved {medline_count} patient education topics",
                }
            )

        res = retrieve_evidence(
            state=state,
            evidence_retriever=resolved_evidence_retriever,
            patient_education_retriever=resolved_education_retriever,
        )
        return {**res, "execution_events": events}

    def processor_node(state: HealthcareWorkflowState) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        events = list(state.get("execution_events", []))
        t_start_iso = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        status = "completed"
        err_type = None
        output_sum = ""
        item_count = 0
        try:
            res = process_evidence_node(state=state)
            item_count = len(res.get("unified_evidence", []))
            output_sum = (
                f"Normalized {item_count} items, {len(res.get('excluded_evidence', []))} excluded"
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
                    "stage": "Evidence Processor",
                    "tool_name": "UnifiedEvidencePipeline",
                    "status": status,
                    "start_time": t_start_iso,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1 - t0) * 1000.0, 2),
                    "query_summary": (
                        f"Process {len(state.get('provider_candidates', []))} providers, "
                        f"{len(state.get('clinical_evidence', []))} clinical, "
                        f"{len(state.get('patient_education_evidence', []))} education"
                    ),
                    "result_count": item_count,
                    "error_type": err_type,
                    "output_summary": output_sum,
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
        try:
            res = validate_records(state=state)
            val = res.get("validation_results", {})
            output_sum = f"Valid: {val.get('is_valid', True)}, notes: {len(val.get('notes', []))}"
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
                    "stage": "Deterministic Validator",
                    "tool_name": "ClinicalValidator",
                    "status": status,
                    "start_time": t_start_iso,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1 - t0) * 1000.0, 2),
                    "query_summary": (f"Validate {len(state.get('unified_evidence', []))} items"),
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
            events.append(
                {
                    "request_id": req_id,
                    "stage": "Gemma 4 Synthesis",
                    "tool_name": "Gemma 4 Answer Synthesis",
                    "status": status,
                    "start_time": t_start_iso,
                    "end_time": datetime.now(UTC).isoformat(),
                    "duration_ms": round((t1 - t0) * 1000.0, 2),
                    "query_summary": (
                        f"Synthesize answer with {len(state.get('unified_evidence', []))} citations"
                    ),
                    "result_count": 1 if ans_len > 0 else 0,
                    "error_type": err_type,
                    "output_summary": f"Generated grounded answer ({ans_len} chars)",
                }
            )

    workflow.add_node("planner", planner_node)
    workflow.add_node("provider_retrieval", provider_node)
    workflow.add_node("evidence_retrieval", evidence_node)
    workflow.add_node("evidence_processor", processor_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("answer_synthesis", answer_node)

    # Flow: START -> planner -> provider_retrieval -> evidence_retrieval
    # -> evidence_processor -> validator -> answer_synthesis -> END
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "provider_retrieval")
    workflow.add_edge("provider_retrieval", "evidence_retrieval")
    workflow.add_edge("evidence_retrieval", "evidence_processor")
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
