"""Workflow state schemas and typed dictionary definitions for LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

from healthcare_agents.evidence.schemas import (
    ProvenanceRecord,
    StructuredDiscoveryResult,
    UnifiedEvidenceItem,
)
from healthcare_agents.retrieval.base import (
    ClinicalEvidenceRecord,
    CMSQualityRecord,
    ProviderRecord,
)


class SearchPlan(TypedDict, total=False):
    """Structured search plan formulated by the Planner Agent."""

    specialty: str
    city: str
    state: str
    evidence_topics: list[str]
    intent_description: str


class ValidationResults(TypedDict, total=False):
    """Deterministic validation outputs from the Validation Agent."""

    is_valid: bool
    duplicate_providers_found: int
    unsupported_claims: list[str]
    missing_evidence_fields: list[str]
    provenance_verified: bool
    notes: list[str]


class HealthcareWorkflowState(TypedDict, total=False):
    """Complete typed state passing through the LangGraph multi-agent workflow."""

    request_id: str
    original_query: str
    search_plan: SearchPlan
    fanout_plan: dict[str, Any]
    provider_candidates: list[ProviderRecord]
    clinical_evidence: list[ClinicalEvidenceRecord]
    patient_education_evidence: list[ClinicalEvidenceRecord]
    cms_quality: list[CMSQualityRecord]
    unmatched_cms_records: list[CMSQualityRecord]
    unified_evidence: list[UnifiedEvidenceItem]
    excluded_evidence: list[UnifiedEvidenceItem]
    provenance_records: list[ProvenanceRecord]
    structured_discovery_result: StructuredDiscoveryResult
    citations: list[str]
    validation_results: ValidationResults
    unsupported_claims: list[str]
    final_answer: str
    errors: list[str]
    execution_metadata: dict[str, Any]
    execution_events: list[dict[str, Any]]
