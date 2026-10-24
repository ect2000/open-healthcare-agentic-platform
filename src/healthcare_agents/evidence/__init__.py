"""Unified evidence processing package for multi-source healthcare discovery.

Provides normalization, deduplication, explainable relevance scoring,
ranking, and provenance verification across:
- NPPES (National Provider Identifier Registry)
- PubMed (Biomedical Research)
- CMS Provider Data Catalog (Public Hospital & Clinician Quality Metrics)
- MedlinePlus (Authoritative Consumer Health Education)
"""

from __future__ import annotations

from healthcare_agents.evidence.deduplication import (
    deduplicate_all_evidence,
    deduplicate_cms_records,
    deduplicate_medlineplus_topics,
    deduplicate_providers,
    deduplicate_pubmed_articles,
)
from healthcare_agents.evidence.normalization import (
    normalize_clinical_evidence_record,
    normalize_cms_quality_record,
    normalize_provider_record,
)
from healthcare_agents.evidence.provenance import (
    CitationCheckResult,
    build_provenance_registry,
    check_boundary_crossings,
    extract_citation_references,
    validate_source_url,
    verify_citation_integrity,
)
from healthcare_agents.evidence.ranking import (
    rank_cms_records,
    rank_evidence_collection,
    rank_medlineplus_topics,
    rank_providers,
    rank_pubmed_articles,
)
from healthcare_agents.evidence.relevance import (
    assess_cms_relevance,
    assess_medlineplus_relevance,
    assess_provider_relevance,
    assess_pubmed_relevance,
    filter_and_score_evidence,
)
from healthcare_agents.evidence.schemas import (
    EvidenceSourceType,
    EvidenceStatus,
    ProvenanceRecord,
    RelevanceAssessment,
    StructuredDiscoveryResult,
    UnifiedEvidenceItem,
)

__all__ = [
    "CitationCheckResult",
    "EvidenceSourceType",
    "EvidenceStatus",
    "ProvenanceRecord",
    "RelevanceAssessment",
    "StructuredDiscoveryResult",
    "UnifiedEvidenceItem",
    "assess_cms_relevance",
    "assess_medlineplus_relevance",
    "assess_provider_relevance",
    "assess_pubmed_relevance",
    "build_provenance_registry",
    "check_boundary_crossings",
    "deduplicate_all_evidence",
    "deduplicate_cms_records",
    "deduplicate_medlineplus_topics",
    "deduplicate_providers",
    "deduplicate_pubmed_articles",
    "extract_citation_references",
    "filter_and_score_evidence",
    "normalize_clinical_evidence_record",
    "normalize_cms_quality_record",
    "normalize_provider_record",
    "rank_cms_records",
    "rank_evidence_collection",
    "rank_medlineplus_topics",
    "rank_providers",
    "rank_pubmed_articles",
    "validate_source_url",
    "verify_citation_integrity",
]
