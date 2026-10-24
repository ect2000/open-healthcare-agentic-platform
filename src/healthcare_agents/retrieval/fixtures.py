"""Synthetic test fixtures and deterministic mock retrievers for Milestone M3.

All data contained in this module is explicitly synthetic and labeled as demonstration test data.
No live provider or patient identifiers are accessed.
"""

from __future__ import annotations

from collections.abc import Sequence

from healthcare_agents.retrieval.base import (
    BaseEvidenceRetriever,
    BasePatientEducationRetriever,
    BaseProviderRetriever,
    BaseQualityRetriever,
    ClinicalEvidenceRecord,
    CMSQualityRecord,
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
        npi: str | None = None,
        limit: int = 5,
    ) -> Sequence[ProviderRecord]:
        matches: list[ProviderRecord] = []
        for p in self._records:
            if npi and p.npi != npi:
                continue
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


SYNTHETIC_QUALITY: list[CMSQualityRecord] = [
    CMSQualityRecord(
        record_id="DEMO-CMS-QUAL-001",
        npi="9990001111",
        entity_name="Dr. Jane Smith, DDS",
        dataset_id="a174-a962",
        dataset_name="PY 2024 Clinician Public Reporting: Overall MIPS Performance",
        source="CMS-Provider-Data-Fixture",
        is_synthetic=True,
        entity_type="Individual",
        facility_id="",
        facility_name="",
        measure_id="FINAL_MIPS_SCORE",
        measure_name="MIPS Final Score",
        score="88.5",
        retrieval_timestamp="2026-10-24T00:00:00+00:00",
        source_url="https://data.cms.gov/provider-data/dataset/a174-a962",
        metadata={"quality_category_score": "86.0", "cost_category_score": "82.5"},
    ),
    CMSQualityRecord(
        record_id="DEMO-CMS-FAC-001",
        npi="",
        entity_name="Texas Children's Hospital",
        dataset_id="xubh-q36u",
        dataset_name="Hospital General Information",
        source="CMS-Provider-Data-Fixture",
        is_synthetic=True,
        entity_type="Facility",
        facility_id="450001",
        facility_name="Texas Children's Hospital",
        facility_type="Childrens",
        star_rating="5",
        city="Houston",
        state="TX",
        retrieval_timestamp="2026-10-24T00:00:00+00:00",
        source_url="https://data.cms.gov/provider-data/dataset/xubh-q36u",
        metadata={"emergency_services": "Yes"},
    ),
]


class FixtureQualityRetriever(BaseQualityRetriever):
    """Deterministic CMS quality retriever querying synthetic quality fixtures."""

    def __init__(self, records: Sequence[CMSQualityRecord] | None = None) -> None:
        self._records = list(records if records is not None else SYNTHETIC_QUALITY)

    def get_provider_quality(self, npi: str) -> Sequence[CMSQualityRecord]:
        clean_npi = npi.strip()
        return [r for r in self._records if r.npi and r.npi == clean_npi]

    def search_facility_quality(
        self,
        facility_name: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 5,
    ) -> Sequence[CMSQualityRecord]:
        matches: list[CMSQualityRecord] = []
        for r in self._records:
            if r.entity_type != "Facility":
                continue
            if facility_name and facility_name.lower() not in r.facility_name.lower():
                continue
            if city and city.lower() not in r.city.lower():
                continue
            if state and state.upper() != r.state.upper():
                continue
            matches.append(r)
            if len(matches) >= limit:
                break
        return matches


class FixturePatientEducationRetriever(BasePatientEducationRetriever):
    """Deterministic patient education retriever querying synthetic MedlinePlus fixtures."""

    def __init__(self, records: Sequence[ClinicalEvidenceRecord] | None = None) -> None:
        self._records = [
            r
            for r in (records if records is not None else SYNTHETIC_EVIDENCE)
            if r.evidence_type == "patient_education"
        ]

    def search_topics(
        self,
        keyword: str,
        language: str = "en",
        limit: int = 5,
    ) -> Sequence[ClinicalEvidenceRecord]:
        matches: list[ClinicalEvidenceRecord] = []
        words = set(keyword.lower().split())
        for e in self._records:
            text = f"{e.title} {e.summary}".lower()
            if any(w in text for w in words if len(w) > 3):
                matches.append(e)
            elif not keyword:
                matches.append(e)
            if len(matches) >= limit:
                break
        if not matches:
            matches = self._records[:limit]
        return matches
