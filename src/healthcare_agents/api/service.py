"""Core business service connecting FastAPI routes to the LangGraph orchestration engine."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import cast

from healthcare_agents import __version__
from healthcare_agents.api.schemas import (
    EvidenceItemResponse,
    ExecutionEvent,
    HealthResponse,
    ProvenanceResponse,
    ReadinessResponse,
    SearchRequest,
    SearchResponse,
    SystemStatusResponse,
)
from healthcare_agents.config import get_settings
from healthcare_agents.evidence.schemas import StructuredDiscoveryResult, UnifiedEvidenceItem
from healthcare_agents.models.ollama_adapter import OllamaAdapter
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
from healthcare_agents.workflows.healthcare_graph import create_healthcare_graph
from healthcare_agents.workflows.state import HealthcareWorkflowState

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "Administrative & Clinical Notice: NPI records denote administrative provider identification "
    "under HIPAA and do NOT constitute proof of medical licensure, clinical competence, or board "
    "certification. PubMed research citations demonstrate published biomedical literature and not "
    "individual doctor capability. CMS metrics reflect hospital/facility public program scope and "
    "cannot be attributed to outpatient dental practitioners; absence of CMS metrics denotes "
    "dataset reporting scope, not poor clinical care. "
    "MedlinePlus content is for patient health literacy, "
    "not personal medical advice or diagnostic substitute."
)


def serialize_evidence_item(item: UnifiedEvidenceItem) -> EvidenceItemResponse:
    """Serialize internal UnifiedEvidenceItem to API response schema."""
    return EvidenceItemResponse(
        evidence_id=item.evidence_id,
        source_type=item.source_type,
        external_id=item.external_id,
        title_or_name=item.title_or_name,
        source_url=item.source_url,
        retrieval_timestamp=item.retrieval_timestamp,
        published_or_updated=item.published_or_updated,
        relevance_score=item.relevance.score,
        is_relevant=item.relevance.is_relevant,
        selection_reason=item.relevance.selection_reason,
        exclusion_reason=item.relevance.exclusion_reason,
        citation_id=item.citation_id,
        evidence_status=item.evidence_status,
        is_synthetic=item.is_synthetic,
        known_limitations=list(item.known_limitations),
        metadata=dict(item.source_metadata),
    )


class HealthcareSearchService:
    """Service wrapping LangGraph multi-agent execution and dependency resolution."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_health(self) -> HealthResponse:
        """Get service health status."""
        return HealthResponse(
            status="healthy",
            version=__version__,
            environment=self.settings.environment,
            timestamp=datetime.now(UTC).isoformat(),
        )

    def get_readiness(self) -> ReadinessResponse:
        """Inspect operational readiness of Ollama model and healthcare retrieval backends."""
        adapter = OllamaAdapter(
            base_url=self.settings.ollama_base_url,
            model_name=self.settings.model_name,
            timeout_seconds=self.settings.model_timeout_seconds,
        )

        ollama_ok = False
        model_ok = False
        try:
            ollama_ok = adapter.check_service_health()
            if ollama_ok:
                model_ok = adapter.is_available()
        except Exception as exc:
            logger.warning("Ollama readiness check warning: %s", exc)

        four_sources_ok = True
        ready = bool(ollama_ok and model_ok)

        return ReadinessResponse(
            ready=ready,
            status="ready" if ready else "not_ready",
            version=__version__,
            ollama_service_available=ollama_ok,
            model_installed=model_ok,
            model_name=self.settings.model_name,
            retrieval_mode=self.settings.retrieval_mode,
            four_sources_configured=four_sources_ok,
            details={
                "nppes_api_url": self.settings.nppes_api_url,
                "pubmed_api_url": self.settings.pubmed_api_url,
                "cms_api_url": self.settings.cms_api_url,
                "medlineplus_api_url": self.settings.medlineplus_api_url,
            },
        )

    def get_system_status(self) -> SystemStatusResponse:
        """Get high-level system information."""
        return SystemStatusResponse(
            version=__version__,
            model=self.settings.model_name,
            ollama_url=self.settings.ollama_base_url,
            retrieval_mode=self.settings.retrieval_mode,
            supported_sources=["NPPES", "PubMed", "CMS Provider Data", "MedlinePlus"],
            features={
                "unified_evidence_layer": True,
                "deterministic_deduplication": True,
                "relevance_ranking": True,
                "provenance_tracking": True,
                "topical_regression_guard": True,
            },
            disclaimer=DISCLAIMER_TEXT,
        )

    def execute_search(self, request: SearchRequest) -> SearchResponse:
        """Execute the LangGraph workflow and return a structured response."""
        req_id = request.request_id or f"req-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')[:17]}"
        effective_mode = request.retrieval_mode or self.settings.retrieval_mode

        logger.info(
            "Executing search request %s [mode=%s]: %s", req_id, effective_mode, request.query
        )

        model_adapter = OllamaAdapter(
            base_url=self.settings.ollama_base_url,
            model_name=self.settings.model_name,
            timeout_seconds=self.settings.model_timeout_seconds,
        )

        provider_retriever: BaseProviderRetriever
        evidence_retriever: BaseEvidenceRetriever
        quality_retriever: BaseQualityRetriever
        patient_education_retriever: BasePatientEducationRetriever

        if effective_mode == "live":
            provider_retriever = NPPESProviderRetriever(
                base_url=self.settings.nppes_api_url,
                timeout_seconds=self.settings.nppes_timeout_seconds,
                max_retries=self.settings.nppes_max_retries,
            )
            evidence_retriever = PubMedEvidenceRetriever(
                base_url=self.settings.pubmed_api_url,
                timeout_seconds=self.settings.pubmed_timeout_seconds,
                max_retries=self.settings.pubmed_max_retries,
                api_key=self.settings.ncbi_api_key,
                email=self.settings.ncbi_email,
                tool=self.settings.ncbi_tool,
            )
            quality_retriever = CMSProviderDataRetriever(
                base_url=self.settings.cms_api_url,
                timeout_seconds=self.settings.cms_timeout_seconds,
                max_retries=self.settings.cms_max_retries,
            )
            patient_education_retriever = MedlinePlusPatientEducationRetriever(
                base_url=self.settings.medlineplus_api_url,
                connect_url=self.settings.medlineplus_connect_url,
                timeout_seconds=self.settings.medlineplus_timeout_seconds,
                max_retries=self.settings.medlineplus_max_retries,
            )
        else:
            provider_retriever = FixtureProviderRetriever()
            evidence_retriever = FixtureEvidenceRetriever()
            quality_retriever = FixtureQualityRetriever()
            patient_education_retriever = FixturePatientEducationRetriever()

        graph_builder = create_healthcare_graph(
            model_adapter=model_adapter,
            provider_retriever=provider_retriever,
            evidence_retriever=evidence_retriever,
            quality_retriever=quality_retriever,
            patient_education_retriever=patient_education_retriever,
        )
        app = graph_builder.compile()

        initial_state: HealthcareWorkflowState = {
            "request_id": req_id,
            "original_query": request.query,
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
            "execution_metadata": {
                "retrieval_mode": effective_mode,
                "model_name": self.settings.model_name,
                "result_limit": request.result_limit or 10,
            },
            "execution_events": [],
        }

        raw_state = app.invoke(initial_state)
        final_state: HealthcareWorkflowState = cast(HealthcareWorkflowState, raw_state)

        structured_res = final_state.get("structured_discovery_result")
        if isinstance(structured_res, StructuredDiscoveryResult):
            providers = [serialize_evidence_item(it) for it in structured_res.provider_candidates]
            research = [serialize_evidence_item(it) for it in structured_res.clinical_research]
            cms = [serialize_evidence_item(it) for it in structured_res.cms_quality_data]
            education = [serialize_evidence_item(it) for it in structured_res.patient_education]
            excluded = [serialize_evidence_item(it) for it in structured_res.excluded_items]
            provenance = [
                ProvenanceResponse(
                    source_name=p.source_name,
                    external_id=p.external_id,
                    canonical_url=p.canonical_url,
                    retrieval_timestamp=p.retrieval_timestamp,
                    source_record_type=p.source_record_type,
                    citation_id=p.citation_id,
                    is_synthetic=p.is_synthetic,
                    language=p.language,
                )
                for p in structured_res.provenance_records
            ]
            relevance_reasons = structured_res.relevance_explanations
            missing_info = structured_res.missing_information
            errors = structured_res.source_errors
            answer_text = structured_res.grounded_answer
            created_at = structured_res.created_at
        else:
            unified_items: list[UnifiedEvidenceItem] = final_state.get("unified_evidence", [])
            providers = [
                serialize_evidence_item(it) for it in unified_items if it.source_type == "NPPES"
            ]
            research = [
                serialize_evidence_item(it) for it in unified_items if it.source_type == "PubMed"
            ]
            cms = [serialize_evidence_item(it) for it in unified_items if it.source_type == "CMS"]
            education = [
                serialize_evidence_item(it)
                for it in unified_items
                if it.source_type in ("MedlinePlus", "MedlinePlus-Connect")
            ]
            excluded_raw: list[UnifiedEvidenceItem] = final_state.get("excluded_evidence", [])
            excluded = [serialize_evidence_item(it) for it in excluded_raw]
            provenance = [
                ProvenanceResponse(
                    source_name=p.source_name,
                    external_id=p.external_id,
                    canonical_url=p.canonical_url,
                    retrieval_timestamp=p.retrieval_timestamp,
                    source_record_type=p.source_record_type,
                    citation_id=p.citation_id,
                    is_synthetic=p.is_synthetic,
                    language=p.language,
                )
                for p in final_state.get("provenance_records", [])
            ]
            relevance_reasons = [it.relevance.selection_reason for it in unified_items]
            missing_info = []
            errors = list(final_state.get("errors", []))
            answer_text = final_state.get("final_answer", "")
            created_at = datetime.now(UTC).isoformat()

        if request.result_limit and len(providers) > request.result_limit:
            providers = providers[: request.result_limit]

        exec_metadata = dict(final_state.get("execution_metadata", {}))
        exec_metadata["retrieval_mode"] = effective_mode
        exec_metadata["provider_count"] = len(providers)
        exec_metadata["clinical_count"] = len(research)
        exec_metadata["cms_count"] = len(cms)
        exec_metadata["education_count"] = len(education)
        exec_metadata["excluded_count"] = len(excluded)

        raw_events = final_state.get("execution_events", [])
        events = [
            ExecutionEvent(
                request_id=ev.get("request_id", req_id),
                trace_id=ev.get("trace_id"),
                span_id=ev.get("span_id"),
                parent_span_id=ev.get("parent_span_id"),
                stage=ev.get("stage", "Unknown"),
                tool_name=ev.get("tool_name"),
                status=ev.get("status", "completed"),
                start_time=ev.get("start_time", ""),
                end_time=ev.get("end_time", ""),
                duration_ms=ev.get("duration_ms", 0.0),
                query_summary=ev.get("query_summary", ""),
                result_count=ev.get("result_count", 0),
                error_type=ev.get("error_type"),
                output_summary=ev.get("output_summary", ""),
            )
            for ev in raw_events
        ]

        return SearchResponse(
            request_id=req_id,
            query=request.query,
            interpreted_intent=dict(final_state.get("search_plan", {})),
            provider_candidates=providers,
            clinical_research=research,
            cms_quality_data=cms,
            patient_education=education,
            excluded_items=excluded,
            provenance_records=provenance,
            relevance_explanations=relevance_reasons,
            missing_information=missing_info,
            source_errors=errors,
            grounded_answer=answer_text,
            execution_metadata=exec_metadata,
            limitations_disclaimer=DISCLAIMER_TEXT,
            created_at=created_at,
            execution_events=events,
        )
