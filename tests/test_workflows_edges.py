"""Targeted unit tests for edge branches in agents, retrievers, and workflows."""

from unittest.mock import MagicMock

from healthcare_agents.agents.answer import synthesize_answer
from healthcare_agents.agents.planner import plan_query
from healthcare_agents.agents.provider import retrieve_providers
from healthcare_agents.agents.validator import validate_records
from healthcare_agents.models.schemas import CompletionUsage, ModelResponse
from healthcare_agents.retrieval.base import ClinicalEvidenceRecord, ProviderRecord
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixtureProviderRetriever,
)
from healthcare_agents.workflows import (
    HealthcareWorkflowState,
    SearchPlan,
    ValidationResults,
    create_healthcare_graph,
    run_healthcare_workflow,
)


def test_workflows_init_exports() -> None:
    """Verify package attributes in workflows/__init__.py."""
    assert HealthcareWorkflowState is not None
    assert SearchPlan is not None
    assert ValidationResults is not None
    assert callable(create_healthcare_graph)
    assert callable(run_healthcare_workflow)


def test_answer_agent_with_model_adapter_success_and_error() -> None:
    """Verify answer agent model generation, token tracking, and error fallback."""
    mock_model = MagicMock()
    mock_model.generate.return_value = ModelResponse(
        content="Generated clinical answer with citations.",
        model="gemma4:e2b",
        usage=CompletionUsage(total_tokens=42),
    )

    state: HealthcareWorkflowState = {
        "original_query": "Pediatric dentistry",
        "provider_candidates": [],
        "clinical_evidence": [],
        "patient_education_evidence": [],
    }
    res = synthesize_answer(state, model_adapter=mock_model)
    assert res["final_answer"] == "Generated clinical answer with citations."
    assert res["execution_metadata"]["answer_tokens"] == 42

    # Model generation failure triggers error recording and fallback
    mock_model.generate.side_effect = RuntimeError("Generation failed")
    res_err = synthesize_answer(state, model_adapter=mock_model)
    assert "Healthcare Discovery Summary" in res_err["final_answer"]
    assert len(res_err["errors"]) == 1


def test_planner_agent_keywords_and_topics() -> None:
    """Verify planner regex rules for various medical specialties and cities."""
    queries_and_specialties = [
        ("Find a general dentist in Austin", "Dentistry", "Austin"),
        ("Find a heart doctor in Houston", "Cardiology", "Houston"),
        ("Find children specialist in Houston", "Pediatrics", "Houston"),
    ]
    for q, expected_spec, expected_city in queries_and_specialties:
        res = plan_query({"original_query": q}, model_adapter=None)
        assert res["search_plan"]["specialty"] == expected_spec
        assert res["search_plan"]["city"] == expected_city


def test_provider_retriever_relaxed_search_and_filters() -> None:
    """Verify provider retriever filters by state and falls back when city not matched."""
    retriever = FixtureProviderRetriever()
    # Non-matching city but matching specialty triggers fallback
    state: HealthcareWorkflowState = {
        "search_plan": {
            "specialty": "Pediatric Dentistry",
            "city": "UnknownCity",
            "state": "TX",
        }
    }
    res = retrieve_providers(state, provider_retriever=retriever)
    assert len(res["provider_candidates"]) >= 2

    # Search with state filter
    matches = retriever.search_providers(state="TX", limit=10)
    assert all(p.state == "TX" for p in matches)


def test_evidence_retriever_filtering_and_fallback() -> None:
    """Verify evidence retriever filtering by type and fallback to default records."""
    retriever = FixtureEvidenceRetriever()

    # Search by evidence type
    guidelines = retriever.search_evidence(topic="", evidence_type="clinical_guideline")
    assert all(e.evidence_type == "clinical_guideline" for e in guidelines)

    # Search with nonsense keyword falls back to available records
    fallback = retriever.search_evidence(topic="xyznotatopic1234")
    assert len(fallback) > 0


def test_validator_detects_empty_state_and_missing_name_or_specialty() -> None:
    """Verify validator flags missing provider names, specialties, and empty states."""
    bad_provider = ProviderRecord(
        provider_id="P_BAD",
        npi="",
        name="",
        specialty="",
        facility_name="Clinic",
        city="Houston",
        state="TX",
        source="Src",
    )
    bad_evidence = ClinicalEvidenceRecord(
        record_id="E_BAD",
        title="Bad Evid",
        source="",
        summary="summary",
        evidence_type="research_study",
        year=2024,
        citation_ref="",
    )

    state: HealthcareWorkflowState = {
        "provider_candidates": [bad_provider],
        "clinical_evidence": [bad_evidence],
        "patient_education_evidence": [],
    }
    res = validate_records(state)
    val = res["validation_results"]
    assert val["is_valid"] is False
    assert any("missing NPI" in m for m in val["missing_evidence_fields"])
    assert any("missing name" in m for m in val["missing_evidence_fields"])
    assert any("missing specialty" in m for m in val["missing_evidence_fields"])
    assert any("missing citation reference" in m for m in val["missing_evidence_fields"])

    empty_res = validate_records({"provider_candidates": [], "clinical_evidence": []})
    notes = empty_res["validation_results"]["notes"]
    assert any("No provider or clinical evidence" in note for note in notes)


def test_validator_pmid_format_url_and_duplicate_evidence() -> None:
    """Verify validator flags invalid PMIDs, URLs, duplicates, and independence note."""
    valid_provider = ProviderRecord(
        provider_id="P_OK",
        npi="1234567890",
        name="Dr. Valid",
        specialty="Pediatric Dentistry",
        facility_name="Clinic",
        city="Houston",
        state="TX",
        source="CMS-NPPES-Live",
    )
    # Article with invalid PMID and invalid URL
    bad_article = ClinicalEvidenceRecord(
        record_id="E_PUB1",
        title="Study One",
        source="PubMed-Live",
        summary="Some summary",
        evidence_type="research_study",
        year=2024,
        citation_ref="PMID:invalid_pmid",
        pmid="invalid_pmid",
        pubmed_url="http://fake-site.org/123",
        is_synthetic=False,
    )
    # Duplicate article with same PMID
    dup_article = ClinicalEvidenceRecord(
        record_id="E_PUB2",
        title="Study Two",
        source="PubMed-Live",
        summary="Another summary",
        evidence_type="research_study",
        year=2024,
        citation_ref="PMID:invalid_pmid",
        pmid="invalid_pmid",
        pubmed_url="https://pubmed.ncbi.nlm.nih.gov/12345/",
        is_synthetic=False,
    )

    state: HealthcareWorkflowState = {
        "provider_candidates": [valid_provider],
        "clinical_evidence": [bad_article, dup_article],
        "patient_education_evidence": [],
    }

    res = validate_records(state)
    val = res["validation_results"]
    assert any("invalid PMID format" in claim for claim in val["unsupported_claims"])
    assert any("invalid PubMed URL" in claim for claim in val["unsupported_claims"])
    assert any("Duplicate PubMed article detected" in note for note in val["notes"])
    assert any("do not attest to specific individual provider" in note for note in val["notes"])


def test_validator_cms_quality_and_npi_matching() -> None:
    """Verify CMS quality validation, exact NPI checking, and clinical independence guardrails."""
    from healthcare_agents.retrieval.base import CMSQualityRecord

    prov = ProviderRecord(
        provider_id="P1",
        npi="1003809641",
        name="Dr. Robert Davidson",
        specialty="Internal Medicine",
        facility_name="Hospital",
        city="Houston",
        state="TX",
        source="CMS-NPPES-Live",
        is_synthetic=False,
    )
    # Valid CMS quality record matching NPI
    valid_cms = CMSQualityRecord(
        record_id="CMS-MIPS-1",
        npi="1003809641",
        entity_name="Dr. Robert Davidson",
        dataset_id="a174-a962",
        dataset_name="PY 2024 Clinician MIPS",
        source="CMS-Provider-Data",
        measure_id="FINAL_MIPS_SCORE",
        score="87.27",
        is_synthetic=False,
    )
    # Unmatched CMS record with different NPI
    unmatched_cms = CMSQualityRecord(
        record_id="CMS-MIPS-OTHER",
        npi="9999999999",
        entity_name="Dr. Other Clinician",
        dataset_id="a174-a962",
        dataset_name="PY 2024 Clinician MIPS",
        source="CMS-Provider-Data",
        measure_id="FINAL_MIPS_SCORE",
        score="95.0",
        is_synthetic=False,
    )

    state: HealthcareWorkflowState = {
        "provider_candidates": [prov],
        "clinical_evidence": [],
        "patient_education_evidence": [],
        "cms_quality": [valid_cms, unmatched_cms],
        "unmatched_cms_records": [unmatched_cms],
    }

    res = validate_records(state)
    val = res["validation_results"]

    # Verify warning on unmatched NPI in cms_quality
    assert any(
        "refers to NPI 9999999999 not among candidate providers" in c
        for c in val["unsupported_claims"]
    )
    # Verify guardrail note on absence of CMS quality not equating to low quality
    assert any("Absence of CMS quality measures" in note for note in val["notes"])
    # Verify note on preserving unmatched CMS records
    assert any("Preserved 1 unmatched CMS record" in note for note in val["notes"])
