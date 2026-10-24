"""Base interfaces and data schemas for healthcare data retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderRecord:
    """Healthcare provider candidate record normalized from registry or fixture data."""

    provider_id: str
    npi: str
    name: str
    specialty: str
    facility_name: str
    city: str
    state: str
    source: str
    is_synthetic: bool = True
    entity_type: str = "Individual"  # "Individual" (NPI-1) or "Organization" (NPI-2)
    taxonomy_code: str = ""
    practice_address: str = ""
    mailing_address: str = ""
    telephone: str = ""
    retrieval_timestamp: str = ""
    source_url: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ClinicalEvidenceRecord:
    """Biomedical research or clinical study evidence record."""

    record_id: str
    title: str
    source: str  # e.g. "PubMed-Live", "MedlinePlus-Live", "MedlinePlus-Demo-Fixture"
    summary: str
    evidence_type: str  # "research_study", "clinical_guideline", "patient_education"
    year: int
    is_synthetic: bool = True
    citation_ref: str = ""
    pmid: str = ""
    authors: tuple[str, ...] = ()
    journal: str = ""
    doi: str = ""
    pubmed_url: str = ""
    retrieval_timestamp: str = ""
    source_type: str = "PubMed"  # "PubMed", "MedlinePlus", "MedlinePlus-Connect"
    evidence_status: str = "available"  # "available", "no_abstract", "empty_results", "error"
    official_url: str = ""
    topic_id: str = ""
    language: str = "en"


@dataclass(frozen=True)
class CMSQualityRecord:
    """CMS Provider Data Catalog quality or facility affiliation record."""

    record_id: str
    npi: str
    entity_name: str
    dataset_id: str
    dataset_name: str
    source: str = "CMS-Provider-Data"
    is_synthetic: bool = True
    entity_type: str = "Individual"  # "Individual", "Facility", or "Group"
    facility_id: str = ""
    facility_name: str = ""
    facility_type: str = ""
    measure_id: str = ""
    measure_name: str = ""
    score: str = ""  # Numeric or categorical rating as string
    performance_rate: str = ""
    star_rating: str = ""
    city: str = ""
    state: str = ""
    retrieval_timestamp: str = ""
    source_url: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class BaseProviderRetriever(ABC):
    """Abstract interface for healthcare provider discovery."""

    @abstractmethod
    def search_providers(
        self,
        specialty: str | None = None,
        city: str | None = None,
        state: str | None = None,
        npi: str | None = None,
        limit: int = 5,
    ) -> Sequence[ProviderRecord]:
        """Retrieve candidate provider records matching criteria."""


class BaseEvidenceRetriever(ABC):
    """Abstract interface for biomedical and patient education evidence retrieval."""

    @abstractmethod
    def search_evidence(
        self,
        topic: str,
        evidence_type: str | None = None,
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        """Retrieve relevant scientific or patient education evidence."""


class BaseQualityRetriever(ABC):
    """Abstract interface for CMS clinician and facility quality metric retrieval."""

    @abstractmethod
    def get_provider_quality(
        self,
        npi: str,
    ) -> Sequence[CMSQualityRecord]:
        """Retrieve quality or affiliation measures for an individual or group NPI."""

    @abstractmethod
    def search_facility_quality(
        self,
        facility_name: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 5,
    ) -> Sequence[CMSQualityRecord]:
        """Retrieve quality ratings for healthcare facilities."""


class BasePatientEducationRetriever(ABC):
    """Abstract interface for MedlinePlus consumer health topic discovery."""

    @abstractmethod
    def search_topics(
        self,
        keyword: str,
        language: str = "en",
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        """Retrieve authoritative patient education topics matching keyword."""
