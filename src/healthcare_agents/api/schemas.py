"""Pydantic schemas for the Healthcare Agents FastAPI backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status response."""

    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    version: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response detailing component operational statuses."""

    ready: bool
    status: Literal["ready", "not_ready"]
    version: str
    ollama_service_available: bool
    model_installed: bool
    model_name: str
    retrieval_mode: str
    four_sources_configured: bool
    details: dict[str, Any] = Field(default_factory=dict)


class SystemStatusResponse(BaseModel):
    """System configuration and capabilities response."""

    version: str
    model: str
    ollama_url: str
    retrieval_mode: str
    supported_sources: list[str]
    features: dict[str, bool]
    disclaimer: str


class SearchRequest(BaseModel):
    """User discovery search request."""

    query: str = Field(..., min_length=2, max_length=1000, description="Healthcare user query")
    request_id: str | None = Field(default=None, description="Optional caller correlation ID")
    retrieval_mode: Literal["fixtures", "live"] | None = Field(
        default=None, description="Optional override for retrieval mode"
    )
    result_limit: int | None = Field(
        default=10, ge=1, le=50, description="Maximum provider results"
    )


class EvidenceItemResponse(BaseModel):
    """Serialized unified evidence item."""

    evidence_id: str
    source_type: str
    external_id: str
    title_or_name: str
    source_url: str
    retrieval_timestamp: str
    published_or_updated: str
    relevance_score: float
    is_relevant: bool
    selection_reason: str
    exclusion_reason: str
    citation_id: str
    evidence_status: str
    is_synthetic: bool
    known_limitations: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProvenanceResponse(BaseModel):
    """Provenance record verifying source authenticity."""

    source_name: str
    external_id: str
    canonical_url: str
    retrieval_timestamp: str
    source_record_type: str
    citation_id: str
    is_synthetic: bool
    language: str


class ExecutionEvent(BaseModel):
    """Telemetry event capturing agent and retrieval tool execution details."""

    request_id: str
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    query_id: str | None = None
    dependency_ids: list[str] = Field(default_factory=list)
    stage: str
    tool_name: str | None = None
    status: str = "completed"  # completed, failed, skipped
    start_time: str
    end_time: str
    duration_ms: float
    query_summary: str = ""
    result_count: int = 0
    error_type: str | None = None
    output_summary: str = ""


class SearchResponse(BaseModel):
    """Unified evidence-grounded search response."""

    request_id: str
    query: str
    interpreted_intent: dict[str, Any]
    retrieval_mode: str = "live"
    provider_candidates: list[EvidenceItemResponse]
    clinical_research: list[EvidenceItemResponse]
    cms_quality_data: list[EvidenceItemResponse]
    patient_education: list[EvidenceItemResponse]
    excluded_items: list[EvidenceItemResponse]
    provenance_records: list[ProvenanceResponse]
    relevance_explanations: list[str]
    missing_information: list[str]
    source_errors: list[str]
    grounded_answer: str
    execution_metadata: dict[str, Any]
    limitations_disclaimer: str
    created_at: str
    fanout_plan: dict[str, Any] = Field(default_factory=dict)
    execution_events: list[ExecutionEvent] = Field(default_factory=list)
    trace_id: str | None = Field(default=None, description="OpenTelemetry 32-hex trace ID")
    span_id: str | None = Field(default=None, description="OpenTelemetry 16-hex root span ID")
