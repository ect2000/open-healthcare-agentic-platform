"""Synthetic test fixtures and deterministic mock retrievers for Milestone M3.

All data contained in this module is explicitly synthetic and labeled as demonstration test data.
No live provider or patient identifiers are accessed.
"""

from __future__ import annotations

from collections.abc import Sequence

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BaseProviderRetriever,
    ClinicalEvidenceRecord,
    ProviderRecord,
)

SYNTHETIC_PROVIDERS: list[ProviderRecord] = [
    ProviderRecord(
        provider_id="DEMO-PROV-001",
        npi="9990001111",
        name="Dr. Jane Smith, DDS",
        specialty="Pediatric Dentistry",
        facility_name="Houston Children's Dental Clinic",
        city="Houston",
        state="TX",
        source="NPPES-Demo-Fixture",
        is_synthetic=True,
        metadata={"board_certified": "true", "languages": "English, Spanish"},
    ),
    ProviderRecord(
        provider_id="DEMO-PROV-002",
        npi="9990002222",
        name="Dr. Marcus Vance, DDS",
        specialty="Pediatric Dentistry",
        facility_name="Bayou City Pediatric Smiles",
        city="Houston",
        state="TX",
        source="NPPES-Demo-Fixture",
        is_synthetic=True,
        metadata={"board_certified": "true", "languages": "English"},
    ),
    ProviderRecord(
        provider_id="DEMO-PROV-003",
        npi="9990003333",
        name="Dr. Elena Rostova, MD",
        specialty="Cardiology",
        facility_name="Memorial Cardiology Center",
        city="Houston",
        state="TX",
        source="NPPES-Demo-Fixture",
        is_synthetic=True,
        metadata={"board_certified": "true"},
    ),
    ProviderRecord(
        provider_id="DEMO-PROV-004",
        npi="9990004444",
        name="Dr. Robert Chen, MD",
        specialty="Pediatrics",
        facility_name="Lone Star Children's Health",
        city="Austin",
        state="TX",
        source="CMS-Demo-Fixture",
        is_synthetic=True,
        metadata={"star_rating": "4.5"},
    ),
]

SYNTHETIC_EVIDENCE: list[ClinicalEvidenceRecord] = [
    ClinicalEvidenceRecord(
        record_id="EVID-PUBMED-001",
        title="Early Childhood Caries Prevention and Dietary Fluoride Recommendations",
        source="PubMed-Demo-Fixture",
        summary=(
            "Routine dental visits starting by age 1 or within 6 months of primary tooth "
            "eruption significantly reduce caries incidence and emergency dental treatments "
            "in pediatric populations."
        ),
        evidence_type="research_study",
        year=2024,
        is_synthetic=True,
        citation_ref="PMID:DEMO-3829101",
    ),
    ClinicalEvidenceRecord(
        record_id="EVID-MEDLINE-002",
        title="Child Dental Health: Prevention, Checkups, and Fluoride Varnish",
        source="MedlinePlus-Demo-Fixture",
        summary=(
            "Pediatric dentists specialize in diagnosing, treating, and preventing dental issues "
            "in infants, children, and teens, including special-needs pediatric care."
        ),
        evidence_type="patient_education",
        year=2025,
        is_synthetic=True,
        citation_ref="MedlinePlus:DEMO-pediatric-dentistry",
    ),
    ClinicalEvidenceRecord(
        record_id="EVID-PUBMED-003",
        title="Cardiovascular Risk Assessment in Preventive Primary Care",
        source="PubMed-Demo-Fixture",
        summary=(
            "Annual screening of lipid profiles and blood pressure reduces "
            "10-year major adverse cardiac events."
        ),
        evidence_type="clinical_guideline",
        year=2023,
        is_synthetic=True,
        citation_ref="PMID:DEMO-3612847",
    ),
]


class FixtureProviderRetriever(BaseProviderRetriever):
    """Deterministic provider retriever querying synthetic fixtures."""

    def __init__(self, records: Sequence[ProviderRecord] | None = None) -> None:
        self._records = list(records if records is not None else SYNTHETIC_PROVIDERS)

    def search_providers(
        self,
        specialty: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 5,
    ) -> Sequence[ProviderRecord]:
        matches: list[ProviderRecord] = []
        for p in self._records:
            if specialty and specialty.lower() not in p.specialty.lower():
                continue
            if city and city.lower() not in p.city.lower():
                continue
            if state and state.upper() != p.state.upper():
                continue
            matches.append(p)
            if len(matches) >= limit:
                break
        return matches


class FixtureEvidenceRetriever(BaseEvidenceRetriever):
    """Deterministic evidence retriever querying synthetic research fixtures."""

    def __init__(self, records: Sequence[ClinicalEvidenceRecord] | None = None) -> None:
        self._records = list(records if records is not None else SYNTHETIC_EVIDENCE)

    def search_evidence(
        self,
        topic: str,
        evidence_type: str | None = None,
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        matches: list[ClinicalEvidenceRecord] = []
        topic_words = set(topic.lower().split())
        for e in self._records:
            if evidence_type and e.evidence_type != evidence_type:
                continue
            text = f"{e.title} {e.summary}".lower()
            if any(w in text for w in topic_words if len(w) > 3):
                matches.append(e)
            elif not topic:
                matches.append(e)
            if len(matches) >= limit:
                break
        # Fallback to returning general evidence if no keyword match
        if not matches:
            matches = self._records[:limit]
        return matches
