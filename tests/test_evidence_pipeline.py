"""Comprehensive tests for the unified evidence processing layer.

Validates:
- Evidence normalization across all 4 sources (NPPES, PubMed, CMS, MedlinePlus)
- Deterministic deduplication (exact NPI, exact PMID/DOI, CMS, MedlinePlus URL/lang)
- Explainable relevance scoring & rejection logic
- Explicit regression requirement: PMID 39046104 (dementia GWAS) must NOT appear
  as evidence for pediatric dental anxiety
- Source-specific ranking without fake universal provider quality scores
- Provenance tracking, URL domain verification, and boundary crossing detection
- StructuredDiscoveryResult serialization
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
    check_boundary_crossings,
    validate_source_url,
    verify_citation_integrity,
)
from healthcare_agents.evidence.ranking import (
    rank_providers,
    rank_pubmed_articles,
)
from healthcare_agents.evidence.relevance import (
    assess_medlineplus_relevance,
    assess_provider_relevance,
    filter_and_score_evidence,
)
from healthcare_agents.evidence.schemas import (
    StructuredDiscoveryResult,
)
from healthcare_agents.retrieval.base import (
    ClinicalEvidenceRecord,
    CMSQualityRecord,
    ProviderRecord,
)


def _make_provider(
    provider_id: str = "P1",
    npi: str = "1234567890",
    name: str = "Dr. Jane Pediatric",
    specialty: str = "Pediatric Dentistry",
    facility_name: str = "Children Dental Clinic",
    city: str = "Houston",
    state: str = "TX",
    source: str = "NPPES-Live",
    is_synthetic: bool = False,
    practice_address: str = "123 Pediatric Way",
) -> ProviderRecord:
    return ProviderRecord(
        provider_id=provider_id,
        npi=npi,
        name=name,
        specialty=specialty,
        facility_name=facility_name,
        city=city,
        state=state,
        source=source,
        is_synthetic=is_synthetic,
        practice_address=practice_address,
    )


def _make_pubmed(
    record_id: str = "E1",
    title: str = "Pediatric Anxiety Study",
    summary: str = "Study summary",
    source: str = "PubMed-Live",
    evidence_type: str = "research_study",
    year: int = 2023,
    pmid: str = "31234567",
    doi: str = "10.1016/j.dental.2023.01.001",
    pubmed_url: str = "https://pubmed.ncbi.nlm.nih.gov/31234567/",
    is_synthetic: bool = False,
    citation_ref: str = "PMID:31234567",
) -> ClinicalEvidenceRecord:
    return ClinicalEvidenceRecord(
        record_id=record_id,
        title=title,
        source=source,
        summary=summary,
        evidence_type=evidence_type,
        year=year,
        pmid=pmid,
        doi=doi,
        pubmed_url=pubmed_url,
        is_synthetic=is_synthetic,
        citation_ref=citation_ref,
    )


def _make_medlineplus(
    record_id: str = "MLP-1",
    title: str = "Child Dental Health",
    summary: str = "Patient education summary",
    source: str = "MedlinePlus-Live",
    evidence_type: str = "patient_education",
    year: int = 2024,
    official_url: str = "https://medlineplus.gov/childdentalhealth.html",
    source_type: str = "MedlinePlus",
    language: str = "en",
    citation_ref: str = "MedlinePlus:child-dental-health",
    is_synthetic: bool = False,
) -> ClinicalEvidenceRecord:
    return ClinicalEvidenceRecord(
        record_id=record_id,
        title=title,
        source=source,
        summary=summary,
        evidence_type=evidence_type,
        year=year,
        official_url=official_url,
        source_type=source_type,
        language=language,
        citation_ref=citation_ref,
        is_synthetic=is_synthetic,
    )


# -----------------------------------------------------------------------------
# Normalization Tests
# -----------------------------------------------------------------------------


def test_normalize_provider_record() -> None:
    """Test normalizing NPPES provider record into UnifiedEvidenceItem."""
    prov = _make_provider()
    item = normalize_provider_record(prov)
    assert item.source_type == "NPPES"
    assert item.external_id == "1234567890"
    assert item.citation_id == "NPPES-1234567890"
    assert "npiregistry.cms.hhs.gov" in item.source_url
    assert item.provenance.source_name == "NPPES-Live"
    assert item.original_provider == prov
    assert len(item.known_limitations) > 0


def test_normalize_pubmed_record() -> None:
    """Test normalizing PubMed clinical evidence record."""
    article = _make_pubmed()
    item = normalize_clinical_evidence_record(article)
    assert item.source_type == "PubMed"
    assert item.external_id == "31234567"
    assert item.citation_id == "PMID:31234567"
    assert item.published_or_updated == "2023"
    assert item.source_metadata["doi"] == "10.1016/j.dental.2023.01.001"
    assert item.original_clinical == article


def test_normalize_medlineplus_record() -> None:
    """Test normalizing MedlinePlus patient education record."""
    edu = _make_medlineplus()
    item = normalize_clinical_evidence_record(edu)
    assert item.source_type == "MedlinePlus"
    assert item.provenance.language == "en"
    assert item.citation_id == "MedlinePlus:child-dental-health"
    assert "medlineplus.gov" in item.source_url


def test_normalize_cms_quality_record() -> None:
    """Test normalizing CMS quality record."""
    cms = CMSQualityRecord(
        record_id="CMS-FAC-12345",
        npi="",
        facility_id="12345",
        entity_name="Houston Children's Hospital",
        dataset_id="xubh-q36u",
        dataset_name="Hospital General Information",
        entity_type="Facility",
        measure_id="HOSP_STAR_RATING",
        score="4",
        city="Houston",
        state="TX",
        metadata={"reporting_period": "2023-2024"},
    )
    item = normalize_cms_quality_record(cms)
    assert item.source_type == "CMS"
    assert item.external_id == "12345"
    assert item.citation_id == "CMS:xubh-q36u:12345"
    assert item.provenance.reporting_period == "2023-2024"
    assert item.original_cms == cms


# -----------------------------------------------------------------------------
# Deduplication Tests
# -----------------------------------------------------------------------------


def test_deduplicate_providers_by_npi() -> None:
    """Deduplication must collapse identical NPIs without losing information."""
    p1 = normalize_provider_record(
        _make_provider(provider_id="P1", npi="1000000001", name="Dr. Alice Smith")
    )
    p2 = normalize_provider_record(
        _make_provider(provider_id="P2", npi="1000000001", name="Alice Smith, DDS")
    )
    p3 = normalize_provider_record(
        _make_provider(provider_id="P3", npi="2000000002", name="Dr. Bob Jones")
    )

    deduped = deduplicate_providers([p1, p2, p3])
    assert len(deduped) == 2
    assert [item.external_id for item in deduped] == ["1000000001", "2000000002"]


def test_deduplicate_pubmed_articles_by_pmid_and_doi() -> None:
    """PubMed deduplication must catch duplicate PMIDs and matching DOIs."""
    a1 = normalize_clinical_evidence_record(
        _make_pubmed(record_id="E1", pmid="123456", doi="10.1000/123")
    )
    a2 = normalize_clinical_evidence_record(
        _make_pubmed(record_id="E2", pmid="123456", doi="10.1000/123")
    )
    a3 = normalize_clinical_evidence_record(
        _make_pubmed(record_id="E3", pmid="789012", doi="10.1000/123")
    )
    a4 = normalize_clinical_evidence_record(
        _make_pubmed(record_id="E4", pmid="999999", doi="10.1000/999")
    )

    deduped = deduplicate_pubmed_articles([a1, a2, a3, a4])
    assert len(deduped) == 2
    assert deduped[0].external_id == "123456"
    assert deduped[1].external_id == "999999"


def test_deduplicate_medlineplus_topics_preserves_spanish_and_english() -> None:
    """MedlinePlus dedup must separate English and Spanish topics while deduping identical URLs."""
    t_en1 = normalize_clinical_evidence_record(
        _make_medlineplus(
            record_id="T1", official_url="https://medlineplus.gov/toothdecay.html", language="en"
        )
    )
    t_en2 = normalize_clinical_evidence_record(
        _make_medlineplus(
            record_id="T2", official_url="https://medlineplus.gov/toothdecay.html", language="en"
        )
    )
    t_es = normalize_clinical_evidence_record(
        _make_medlineplus(
            record_id="T3",
            official_url="https://medlineplus.gov/spanish/toothdecay.html",
            language="es",
        )
    )

    deduped = deduplicate_medlineplus_topics([t_en1, t_en2, t_es])
    assert len(deduped) == 2
    langs = {item.provenance.language for item in deduped}
    assert langs == {"en", "es"}


def test_deduplicate_cms_records() -> None:
    """CMS records deduplicate by dataset_id, entity_id, and measure_id."""
    c1 = normalize_cms_quality_record(
        CMSQualityRecord(
            record_id="R1",
            npi="1234567890",
            entity_name="Clinic A",
            dataset_id="ds1",
            dataset_name="Quality",
            measure_id="MEASURE_1",
            score="90",
        )
    )
    c2 = normalize_cms_quality_record(
        CMSQualityRecord(
            record_id="R2",
            npi="1234567890",
            entity_name="Clinic A",
            dataset_id="ds1",
            dataset_name="Quality",
            measure_id="MEASURE_1",
            score="90",
        )
    )
    c3 = normalize_cms_quality_record(
        CMSQualityRecord(
            record_id="R3",
            npi="1234567890",
            entity_name="Clinic A",
            dataset_id="ds1",
            dataset_name="Quality",
            measure_id="MEASURE_2",
            score="85",
        )
    )
    deduped = deduplicate_cms_records([c1, c2, c3])
    assert len(deduped) == 2


def test_deduplicate_all_evidence_combined() -> None:
    """deduplicate_all_evidence must return unified items across all 4 sources."""
    p = normalize_provider_record(_make_provider(provider_id="P1", npi="1111111111"))
    a = normalize_clinical_evidence_record(_make_pubmed(record_id="A1", pmid="111"))
    c = normalize_cms_quality_record(
        CMSQualityRecord(
            record_id="C1", npi="1111111111", entity_name="Doc", dataset_id="d1", dataset_name="dn"
        )
    )
    m = normalize_clinical_evidence_record(
        _make_medlineplus(record_id="M1", official_url="https://medlineplus.gov/teeth.html")
    )

    all_items = [p, p, a, a, c, c, m, m]
    deduped = deduplicate_all_evidence(all_items)
    assert len(deduped) == 4


# -----------------------------------------------------------------------------
# Relevance and Regression Tests
# -----------------------------------------------------------------------------


def test_regression_pmid_39046104_explicitly_rejected_for_dental_anxiety() -> None:
    """CRITICAL REGRESSION REQUIREMENT:

    PMID 39046104 is 'A genome-wide association meta-analysis of all-cause and vascular dementia'.
    It must NEVER appear as evidence supporting pediatric dental anxiety!
    """
    dementia_article = normalize_clinical_evidence_record(
        _make_pubmed(
            record_id="PUBMED-39046104",
            title="A genome-wide association meta-analysis of all-cause and vascular dementia",
            summary=(
                "Dementia is a debilitating neurological disorder with genetic heritability. "
                "Here we conduct a meta-analysis of GWAS for vascular dementia novel loci."
            ),
            pmid="39046104",
            pubmed_url="https://pubmed.ncbi.nlm.nih.gov/39046104/",
            citation_ref="PMID:39046104",
        )
    )

    relevant, excluded = filter_and_score_evidence(
        [dementia_article],
        query_intent="Find pediatric dentists in Houston and research on pediatric dental anxiety",
        evidence_topics=["pediatric dental anxiety", "behavioral guidance in children"],
    )

    assert len(relevant) == 0
    assert len(excluded) == 1
    excluded_item = excluded[0]
    assert excluded_item.external_id == "39046104"
    assert excluded_item.relevance.is_relevant is False
    assert "PMID 39046104" in excluded_item.relevance.exclusion_reason
    assert "dementia" in excluded_item.relevance.exclusion_reason.lower()


def test_assess_provider_relevance_matching_and_rejection() -> None:
    """Provider assessment must reward requested specialty and city match, and exclude others."""
    p_match = normalize_provider_record(
        _make_provider(
            provider_id="P1",
            npi="1000000001",
            specialty="Pediatric Dentistry",
            city="Houston",
            state="TX",
        )
    )
    p_wrong_loc = normalize_provider_record(
        _make_provider(
            provider_id="P2",
            npi="1000000002",
            specialty="Pediatric Dentistry",
            city="Dallas",
            state="TX",
        )
    )
    p_wrong_spec = normalize_provider_record(
        _make_provider(
            provider_id="P3",
            npi="1000000003",
            specialty="Adult Cardiology",
            city="Houston",
            state="TX",
        )
    )

    rel_match = assess_provider_relevance(
        p_match, target_specialty="Pediatric Dentistry", target_city="Houston", target_state="TX"
    )
    assert rel_match.is_relevant is True
    assert rel_match.score >= 0.85

    rel_wrong_loc = assess_provider_relevance(
        p_wrong_loc,
        target_specialty="Pediatric Dentistry",
        target_city="Houston",
        target_state="TX",
    )
    assert rel_wrong_loc.is_relevant is False
    assert "practice city" in rel_wrong_loc.exclusion_reason.lower()

    rel_wrong_spec = assess_provider_relevance(
        p_wrong_spec,
        target_specialty="Pediatric Dentistry",
        target_city="Houston",
        target_state="TX",
    )
    assert rel_wrong_spec.is_relevant is False
    assert "does not match" in rel_wrong_spec.exclusion_reason.lower()


def test_assess_medlineplus_relevance_matching_and_rejection() -> None:
    """MedlinePlus assessment must reward dental topics and reject unrelated educational content."""
    t_dental = normalize_clinical_evidence_record(
        _make_medlineplus(
            record_id="MLP-dental",
            title="Dental Health in Children",
            summary="Dental visits and anxiety prevention.",
            official_url="https://medlineplus.gov/childdentalhealth.html",
        )
    )
    t_unrelated = normalize_clinical_evidence_record(
        _make_medlineplus(
            record_id="MLP-diabetes",
            title="Type 2 Diabetes in Adults",
            summary="Insulin management and diet for diabetes.",
            official_url="https://medlineplus.gov/diabetes.html",
        )
    )

    rel_dental = assess_medlineplus_relevance(t_dental, query_intent="pediatric dental anxiety")
    assert rel_dental.is_relevant is True
    assert rel_dental.score >= 0.80

    rel_unrelated = assess_medlineplus_relevance(
        t_unrelated, query_intent="pediatric dental anxiety"
    )
    assert rel_unrelated.is_relevant is False
    assert "does not address oral health" in rel_unrelated.exclusion_reason.lower()


# -----------------------------------------------------------------------------
# Ranking Tests
# -----------------------------------------------------------------------------


def test_rank_providers_explainable_sorting() -> None:
    """Providers must be sorted by score and address completeness, NOT invented clinical ratings."""
    p_incomplete = normalize_provider_record(
        _make_provider(provider_id="P1", npi="1111111111", practice_address="")
    )
    p_complete = normalize_provider_record(
        _make_provider(provider_id="P2", npi="2222222222", practice_address="100 Medical Blvd")
    )

    ranked = rank_providers([p_incomplete, p_complete])
    assert ranked[0].external_id == "2222222222"
    assert ranked[1].external_id == "1111111111"


def test_rank_pubmed_articles_prefers_systematic_reviews_and_recency() -> None:
    """PubMed ranking promotes systematic reviews/trials and newer publication years."""
    older_trial = normalize_clinical_evidence_record(
        _make_pubmed(
            record_id="E1",
            title="Randomized controlled trial of nitrous oxide",
            summary="Trial on dental anxiety.",
            pmid="101",
            year=2018,
        )
    )
    newer_review = normalize_clinical_evidence_record(
        _make_pubmed(
            record_id="E2",
            title="A systematic review and meta-analysis of behavioral dental guidance",
            summary="Systematic review of evidence.",
            pmid="102",
            year=2024,
        )
    )
    case_report = normalize_clinical_evidence_record(
        _make_pubmed(
            record_id="E3",
            title="A case report of dental fear",
            summary="One patient.",
            pmid="103",
            year=2024,
        )
    )

    ranked = rank_pubmed_articles([older_trial, case_report, newer_review])
    assert ranked[0].external_id == "102"  # systematic review 2024
    assert ranked[1].external_id == "101"  # RCT 2018
    assert ranked[2].external_id == "103"  # case report 2024


# -----------------------------------------------------------------------------
# Provenance and Citation Integrity Tests
# -----------------------------------------------------------------------------


def test_validate_source_url() -> None:
    """Verify official governmental domain constraints."""
    assert validate_source_url("NPPES", "https://npiregistry.cms.hhs.gov/api/")
    assert validate_source_url("PubMed", "https://pubmed.ncbi.nlm.nih.gov/39046104/")
    assert validate_source_url("CMS", "https://data.cms.gov/provider-data/dataset/xubh-q36u")
    assert validate_source_url("MedlinePlus", "https://medlineplus.gov/spanish/toothdecay.html")

    # Mismatches / Phishing domains
    assert not validate_source_url("NPPES", "https://fake-npi-lookup.com/doctor")
    assert not validate_source_url("PubMed", "https://unverified-journal-blog.org/pmid/123")
    assert not validate_source_url("CMS", "https://commercial-ratings-aggregator.com/facility")


def test_check_boundary_crossings() -> None:
    """Assert boundary violations are caught when evidence semantics are abused."""
    # NPPES claiming clinical competence
    v1 = check_boundary_crossings(
        "NPPES-123", "NPPES", "Dr. Jane is board certified and highest quality."
    )
    assert v1 is not None and "competence/quality" in v1

    # PubMed asserting doctor's practice address
    v2 = check_boundary_crossings("PMID-456", "PubMed", "Dr. Jane practices at 123 Main St.")
    assert v2 is not None and "practice location" in v2

    # CMS facility rating attributed as individual dentist rating
    v3 = check_boundary_crossings(
        "CMS-789", "CMS", "This clinician received a pediatric dentist star rating of 5."
    )
    assert v3 is not None and "individual clinician rating" in v3

    # MedlinePlus asserted as primary randomized trial cohort
    v4 = check_boundary_crossings(
        "MLP-101", "MedlinePlus", "The randomized trial cohort was followed for 2 years."
    )
    assert v4 is not None and "primary clinical trial" in v4

    # Legitimate claim within boundaries
    v_ok = check_boundary_crossings(
        "NPPES-123", "NPPES", "Dr. Jane is registered as an active provider in Houston, TX."
    )
    assert v_ok is None


def test_verify_citation_integrity_full() -> None:
    """Verify that hallucinated citations or boundary violations fail integrity verification."""
    p = normalize_provider_record(
        _make_provider(provider_id="P1", npi="1234567890", name="Dr. Alice")
    )
    a = normalize_clinical_evidence_record(
        _make_pubmed(record_id="A1", pmid="98765432", citation_ref="PMID:98765432")
    )

    text_valid = (
        "Dr. Alice [NPPES-1234567890] was discovered. "
        "Clinical literature [PMID:98765432] demonstrates effectiveness."
    )
    check_ok = verify_citation_integrity(text_valid, [p, a])
    assert check_ok.is_valid is True
    assert set(check_ok.valid_citations) == {"NPPES-1234567890", "PMID:98765432"}

    text_hallucinated = "Clinical literature [PMID:99999999] was invented by the model."
    check_bad = verify_citation_integrity(text_hallucinated, [p, a])
    assert check_bad.is_valid is False
    assert "PMID:99999999" in check_bad.unresolved_citations


def test_structured_discovery_result_model() -> None:
    """StructuredDiscoveryResult encapsulates query, candidate providers, research, and answers."""
    result = StructuredDiscoveryResult(
        query="Test query",
        interpreted_intent={"specialty": "Pediatric Dentistry"},
        provider_candidates=[],
        clinical_research=[],
        cms_quality_data=[],
        patient_education=[],
        excluded_items=[],
        provenance_records=[],
        relevance_explanations=["Explanation 1"],
        missing_information=["Missing CMS data"],
        source_errors=[],
        grounded_answer="Validated answer text",
    )
    assert result.query == "Test query"
    assert result.grounded_answer == "Validated answer text"
    assert len(result.relevance_explanations) == 1
    assert result.created_at is not None
