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
    source: str  # e.g. "PubMed-Demo-Fixture", "MedlinePlus-Demo-Fixture"
    summary: str
    evidence_type: str  # "research_study", "clinical_guideline", "patient_education"
    year: int
    is_synthetic: bool = True
    citation_ref: str = ""


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
