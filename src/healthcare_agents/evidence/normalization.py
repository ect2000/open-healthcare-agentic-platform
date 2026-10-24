"""Evidence normalization transforming raw source records into UnifiedEvidenceItem instances.

Preserves all source-specific attributes and references without semantic flattening.
"""

from __future__ import annotations

from typing import Any

from healthcare_agents.evidence.schemas import (
    EvidenceSourceType,
    ProvenanceRecord,
    RelevanceAssessment,
    UnifiedEvidenceItem,
)
from healthcare_agents.retrieval.base import (
    ClinicalEvidenceRecord,
    CMSQualityRecord,
    ProviderRecord,
)

DEFAULT_INITIAL_RELEVANCE = RelevanceAssessment(
    score=1.0,
    is_relevant=True,
    selection_reason="Retrieved from authoritative source",
    exclusion_reason="",
    matched_terms=(),
)


def normalize_provider_record(record: ProviderRecord) -> UnifiedEvidenceItem:
    """Normalize an NPPES ProviderRecord into a UnifiedEvidenceItem."""
    clean_npi = record.npi.strip()
    evidence_id = f"NPPES:{clean_npi}" if clean_npi else f"NPPES:{record.provider_id}"
    canonical_url = (
        f"https://npiregistry.cms.hhs.gov/provider-view/{clean_npi}" if clean_npi else ""
    )
    citation_id = f"NPPES-{clean_npi}" if clean_npi else f"NPPES-{record.provider_id}"

    provenance = ProvenanceRecord(
        source_name=record.source or "CMS-NPPES-Registry",
        external_id=clean_npi,
        canonical_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        source_record_type="ProviderRecord",
        citation_id=citation_id,
        is_synthetic=record.is_synthetic,
        language="en",
    )

    limitations = (
        "NPI is an administrative identifier and not proof of licensure, competence, or outcomes.",
        "Practice address may differ from secondary clinical sites.",
    )

    metadata: dict[str, Any] = {
        "npi": clean_npi,
        "specialty": record.specialty,
        "facility_name": record.facility_name,
        "city": record.city,
        "state": record.state,
        "practice_address": record.practice_address,
        "telephone": record.telephone,
        "entity_type": record.entity_type,
    }
    if record.metadata:
        metadata.update(record.metadata)

    return UnifiedEvidenceItem(
        evidence_id=evidence_id,
        source_type="NPPES",
        external_id=clean_npi,
        title_or_name=record.name,
        source_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        published_or_updated="",
        relevance=DEFAULT_INITIAL_RELEVANCE,
        provenance=provenance,
        citation_id=citation_id,
        evidence_status="available",
        is_synthetic=record.is_synthetic,
        known_limitations=limitations,
        source_metadata=metadata,
        original_provider=record,
    )


def normalize_clinical_evidence_record(record: ClinicalEvidenceRecord) -> UnifiedEvidenceItem:
    """Normalize a PubMed or MedlinePlus ClinicalEvidenceRecord into a UnifiedEvidenceItem."""
    is_medline = (
        record.source_type in ("MedlinePlus", "MedlinePlus-Connect")
        or "MedlinePlus" in record.source
        or record.evidence_type == "patient_education"
    )

    source_type: EvidenceSourceType
    if is_medline:
        source_type = (
            "MedlinePlus-Connect" if record.source_type == "MedlinePlus-Connect" else "MedlinePlus"
        )
        canonical_url = record.official_url or record.pubmed_url
        clean_ext_id = record.topic_id or record.record_id
        citation_id = record.citation_ref if record.citation_ref else f"MedlinePlus:{clean_ext_id}"
        evidence_id = f"MEDLINEPLUS:{clean_ext_id}"
        limitations = (
            "Consumer health education topic intended for patient literacy only.",
            "Not a peer-reviewed clinical research study or clinician credential.",
        )
    else:
        source_type = "PubMed"
        clean_ext_id = record.pmid if record.pmid else record.record_id
        canonical_url = (
            record.pubmed_url
            if record.pubmed_url
            else (
                f"https://pubmed.ncbi.nlm.nih.gov/{clean_ext_id}/" if clean_ext_id.isdigit() else ""
            )
        )
        citation_id = record.citation_ref if record.citation_ref else f"PMID:{clean_ext_id}"
        evidence_id = f"PUBMED:{clean_ext_id}"
        limitations = (
            "Biomedical research study establishing literature findings only.",
            "Does not attest to specific clinician competence or substitute for medical diagnosis.",
        )

    provenance = ProvenanceRecord(
        source_name=record.source,
        external_id=clean_ext_id,
        canonical_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        source_record_type="ClinicalEvidenceRecord",
        citation_id=citation_id,
        is_synthetic=record.is_synthetic,
        language=record.language or "en",
    )

    metadata: dict[str, Any] = {
        "summary": record.summary,
        "evidence_type": record.evidence_type,
        "year": record.year,
        "authors": list(record.authors),
        "journal": record.journal,
        "doi": record.doi,
        "pmid": record.pmid,
        "topic_id": record.topic_id,
        "language": record.language,
    }

    return UnifiedEvidenceItem(
        evidence_id=evidence_id,
        source_type=source_type,
        external_id=clean_ext_id,
        title_or_name=record.title,
        source_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        published_or_updated=str(record.year) if record.year else "",
        relevance=DEFAULT_INITIAL_RELEVANCE,
        provenance=provenance,
        citation_id=citation_id,
        evidence_status="available" if record.evidence_status == "available" else "no_abstract",
        is_synthetic=record.is_synthetic,
        known_limitations=limitations,
        source_metadata=metadata,
        original_clinical=record,
    )


def normalize_cms_quality_record(record: CMSQualityRecord) -> UnifiedEvidenceItem:
    """Normalize a CMSQualityRecord into a UnifiedEvidenceItem."""
    clean_id = record.npi.strip() if record.npi else record.facility_id.strip()
    evidence_id = f"CMS:{record.dataset_id}:{clean_id or record.record_id}:{record.measure_id}"
    canonical_url = (
        record.source_url
        if record.source_url
        else f"https://data.cms.gov/provider-data/dataset/{record.dataset_id}"
    )
    citation_id = f"CMS:{record.dataset_id}:{clean_id or record.record_id}"

    rep_period = record.metadata.get("reporting_period", "") if record.metadata else ""

    provenance = ProvenanceRecord(
        source_name=record.source or "CMS-Provider-Data",
        external_id=clean_id,
        canonical_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        source_record_type="CMSQualityRecord",
        citation_id=citation_id,
        is_synthetic=record.is_synthetic,
        language="en",
        reporting_period=rep_period,
    )

    limitations = (
        "Applies strictly to participating clinicians/facilities under Medicare public reporting.",
        "Absence of scores indicates reporting program scope (e.g. dentistry), NOT low quality.",
    )

    metadata: dict[str, Any] = {
        "dataset_id": record.dataset_id,
        "dataset_name": record.dataset_name,
        "entity_type": record.entity_type,
        "measure_id": record.measure_id,
        "measure_name": record.measure_name,
        "score": record.score,
        "facility_type": record.facility_type,
        "star_rating": record.star_rating,
        "reporting_period": rep_period,
    }
    if record.metadata:
        metadata.update(record.metadata)

    return UnifiedEvidenceItem(
        evidence_id=evidence_id,
        source_type="CMS",
        external_id=clean_id,
        title_or_name=record.entity_name,
        source_url=canonical_url,
        retrieval_timestamp=record.retrieval_timestamp,
        published_or_updated=rep_period,
        relevance=DEFAULT_INITIAL_RELEVANCE,
        provenance=provenance,
        citation_id=citation_id,
        evidence_status="available",
        is_synthetic=record.is_synthetic,
        known_limitations=limitations,
        source_metadata=metadata,
        original_cms=record,
    )
