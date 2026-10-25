"""Tests verifying relevance scoring optimization and dental query exclusions."""

from __future__ import annotations

from healthcare_agents.evidence.normalization import normalize_clinical_evidence_record
from healthcare_agents.evidence.relevance import assess_medlineplus_relevance
from healthcare_agents.retrieval.base import ClinicalEvidenceRecord


def test_dental_query_excludes_unrelated_conditions() -> None:
    """Verify that topics like Eating Disorders are excluded for dental inquiries."""
    raw_eating_disorder = ClinicalEvidenceRecord(
        record_id="MEDLINE-EATING",
        title="Eating Disorders",
        source="MedlinePlus-Live",
        summary=(
            "Eating disorders are serious health conditions that affect physical and mental health."
        ),
        evidence_type="patient_education",
        year=2024,
        is_synthetic=False,
        citation_ref="MedlinePlus:eating_disorders",
        topic_id="eating_disorders",
        language="en",
    )
    norm_item = normalize_clinical_evidence_record(raw_eating_disorder)

    assessment = assess_medlineplus_relevance(
        item=norm_item,
        query_intent="Find pediatric dentists in Houston and research on pediatric dental anxiety",
        target_topics=["dental anxiety", "pediatric dentistry"],
    )

    assert assessment.is_relevant is False
    assert assessment.score <= 0.1
    assert (
        "Eating Disorders" in assessment.exclusion_reason
        or "unrelated medical condition" in assessment.exclusion_reason
    )


def test_dental_query_retains_child_dental_health() -> None:
    """Verify that topics directly addressing child teeth and dental health are retained."""
    raw_dental_health = ClinicalEvidenceRecord(
        record_id="MEDLINE-CHILDDENT",
        title="Child Dental Health",
        source="MedlinePlus-Live",
        summary=(
            "Tooth decay is the most common chronic disease of children. "
            "Good oral care helps teeth."
        ),
        evidence_type="patient_education",
        year=2024,
        is_synthetic=False,
        citation_ref="MedlinePlus:childdentalhealth",
        topic_id="childdentalhealth",
        language="en",
    )
    norm_item = normalize_clinical_evidence_record(raw_dental_health)

    assessment = assess_medlineplus_relevance(
        item=norm_item,
        query_intent="Find pediatric dentists in Houston and research on pediatric dental anxiety",
        target_topics=["dental anxiety", "pediatric dentistry"],
    )

    assert assessment.is_relevant is True
    assert assessment.score >= 0.35
