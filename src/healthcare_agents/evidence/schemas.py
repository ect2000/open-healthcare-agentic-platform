"""Typed schemas for the unified evidence processing layer.

Preserves distinct source-specific record structures while providing a common
typed wrapper for normalization, deduplication, relevance scoring, ranking,
and provenance tracking across:
- NPPES (Provider Registry)
- PubMed (Biomedical Research)
- CMS Provider Data Catalog (Clinician & Facility Quality Metrics)
- MedlinePlus (Consumer Patient Education & Connect Codes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from healthcare_agents.retrieval.base import (
    ClinicalEvidenceRecord,
    CMSQualityRecord,
    ProviderRecord,
)

EvidenceSourceType = Literal["NPPES", "PubMed", "CMS", "MedlinePlus", "MedlinePlus-Connect"]
EvidenceStatus = Literal["available", "no_abstract", "empty_results", "error", "unmatched"]


@dataclass(frozen=True)
class ProvenanceRecord:
    """Detailed provenance metadata verifying the external origin of evidence."""

    source_name: str
    external_id: str
    canonical_url: str
    retrieval_timestamp: str
    source_record_type: str
    citation_id: str
    is_synthetic: bool = False
    language: str = "en"
    reporting_period: str = ""
    associated_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class RelevanceAssessment:
    """Explainable relevance evaluation for an evidence candidate."""

    score: float  # Bounded [0.0, 1.0]
    is_relevant: bool
    selection_reason: str
    exclusion_reason: str = ""
    matched_terms: tuple[str, ...] = ()
    confidence: float = 1.0


@dataclass(frozen=True)
class UnifiedEvidenceItem:
    """Normalized evidence item encapsulating source records and processing metadata."""

    evidence_id: str
    source_type: EvidenceSourceType
    external_id: str
    title_or_name: str
    source_url: str
    retrieval_timestamp: str
    published_or_updated: str
    relevance: RelevanceAssessment
    provenance: ProvenanceRecord
    citation_id: str
    evidence_status: EvidenceStatus
    is_synthetic: bool
    known_limitations: tuple[str, ...]
    source_metadata: dict[str, Any] = field(default_factory=dict)

    # Reference to original typed source record (never flattened or lost)
    original_provider: ProviderRecord | None = None
    original_clinical: ClinicalEvidenceRecord | None = None
    original_cms: CMSQualityRecord | None = None


@dataclass(frozen=True)
class StructuredDiscoveryResult:
    """Stable structured result schema returned from discovery and evaluation."""

    query: str
    interpreted_intent: dict[str, Any]
    provider_candidates: list[UnifiedEvidenceItem]
    clinical_research: list[UnifiedEvidenceItem]
    cms_quality_data: list[UnifiedEvidenceItem]
    patient_education: list[UnifiedEvidenceItem]
    excluded_items: list[UnifiedEvidenceItem]
    provenance_records: list[ProvenanceRecord]
    relevance_explanations: list[str]
    missing_information: list[str]
    source_errors: list[str]
    grounded_answer: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
