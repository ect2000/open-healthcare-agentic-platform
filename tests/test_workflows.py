"""Comprehensive offline tests for LangGraph multi-agent orchestration components."""

from unittest.mock import MagicMock

from healthcare_agents.agents.answer import format_context, synthesize_answer
from healthcare_agents.agents.evidence import retrieve_evidence
from healthcare_agents.agents.planner import extract_json, plan_query
from healthcare_agents.agents.provider import retrieve_providers
from healthcare_agents.agents.validator import validate_records
from healthcare_agents.models.schemas import ModelResponse
from healthcare_agents.retrieval.base import ClinicalEvidenceRecord, ProviderRecord
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixtureProviderRetriever,
)
from healthcare_agents.workflows.healthcare_graph import (
    create_healthcare_graph,
    run_healthcare_workflow,
)
from healthcare_agents.workflows.state import HealthcareWorkflowState


def test_extract_json_valid_and_fallback() -> None:
    """Verify JSON extractor correctly parses embedded JSON or returns empty dict."""
    valid = 'Some text {"specialty": "Dentistry", "city": "Houston"} more text'
    assert extract_json(valid) == {"specialty": "Dentistry", "city": "Houston"}

    invalid = "No json here"
    assert extract_json(invalid) == {}


def test_planner_agent_with_mock_model() -> None:
    """Verify planner agent correctly consumes model output into structured plan."""
    mock_model = MagicMock()
    json_content = (
        '{"specialty": "Cardiology", "city": "Houston", "state": "TX", '
        '"evidence_topics": ["Hypertension"]}'
    )
    mock_model.generate.return_value = ModelResponse(
        content=json_content,
        model="gemma4:e2b",
    )

    state: HealthcareWorkflowState = {
        "original_query": "Find cardiologists in Houston",
    }
    result = plan_query(state, model_adapter=mock_model)
    plan = result["search_plan"]

    assert plan["specialty"] == "Cardiology"
    assert plan["city"] == "Houston"
    assert plan["state"] == "TX"
    assert "Hypertension" in plan["evidence_topics"]
    assert result["execution_metadata"]["planner_completed"] is True


def test_planner_agent_deterministic_fallback() -> None:
    """Verify planner falls back to deterministic regex heuristics when model fails."""
    mock_model = MagicMock()
    mock_model.generate.side_effect = RuntimeError("Model timeout")

    state: HealthcareWorkflowState = {
        "original_query": "Find pediatric dentists in Houston",
    }
    result = plan_query(state, model_adapter=mock_model)
    plan = result["search_plan"]

    assert plan["specialty"] == "Pediatric Dentistry"
    assert plan["city"] == "Houston"
    assert plan["state"] == "TX"
    assert len(result["errors"]) == 1


def test_provider_retriever_and_agent() -> None:
    """Verify provider agent retrieves candidates and updates citations."""
    retriever = FixtureProviderRetriever()
    state: HealthcareWorkflowState = {
        "search_plan": {
            "specialty": "Pediatric Dentistry",
            "city": "Houston",
            "state": "TX",
        },
    }
    result = retrieve_providers(state, provider_retriever=retriever)
    providers = result["provider_candidates"]

    assert len(providers) >= 2
    assert all(p.specialty == "Pediatric Dentistry" for p in providers)
    assert any("Dr. Jane Smith" in p.name for p in providers)
    assert len(result["citations"]) >= 2


def test_evidence_retriever_and_agent() -> None:
    """Verify evidence agent splits clinical studies and patient education."""
    retriever = FixtureEvidenceRetriever()
    state: HealthcareWorkflowState = {
        "search_plan": {
            "evidence_topics": ["Pediatric Dentistry", "Caries"],
        },
    }
    result = retrieve_evidence(state, evidence_retriever=retriever)

    assert len(result["clinical_evidence"]) >= 1
    assert len(result["patient_education_evidence"]) >= 1
    assert any("PMID:" in c for c in result["citations"])


def test_validator_detects_duplicates_and_unsupported_claims() -> None:
    """Verify validator flags duplicate providers and missing provenance."""
    dup_provider_1 = ProviderRecord(
        provider_id="P1",
        npi="12345",
        name="Dr. One",
        specialty="Pediatrics",
        facility_name="Clinic A",
        city="Houston",
        state="TX",
        source="Test-Src",
    )
    dup_provider_2 = ProviderRecord(
        provider_id="P2",
        npi="12345",  # Duplicate NPI
        name="Dr. One Duplicate",
        specialty="Pediatrics",
        facility_name="Clinic B",
        city="Houston",
        state="TX",
        source="",  # Missing source provenance
    )

    state: HealthcareWorkflowState = {
        "provider_candidates": [dup_provider_1, dup_provider_2],
        "clinical_evidence": [],
        "patient_education_evidence": [],
    }
    result = validate_records(state)
    validation = result["validation_results"]

    assert validation["duplicate_providers_found"] == 1
    assert validation["provenance_verified"] is False
    assert len(result["unsupported_claims"]) >= 1
    assert validation["is_valid"] is False


def test_format_context_builder() -> None:
    """Verify format_context formats providers and warnings cleanly."""
    provider = ProviderRecord(
        provider_id="P1",
        npi="111",
        name="Dr. Test",
        specialty="Dentistry",
        facility_name="Clinic",
        city="City",
        state="ST",
        source="Src",
    )
    evidence = ClinicalEvidenceRecord(
        record_id="E1",
        title="Title",
        source="PubMed",
        summary="Summary text",
        evidence_type="research_study",
        year=2024,
        citation_ref="PMID:123",
    )

    state: HealthcareWorkflowState = {
        "original_query": "Test query",
        "provider_candidates": [provider],
        "clinical_evidence": [evidence],
        "patient_education_evidence": [],
        "validation_results": {"unsupported_claims": ["Test claim alert"]},
    }
    ctx = format_context(state)
    assert "Dr. Test" in ctx
    assert "PMID:123" in ctx
    assert "WARNING: Test claim alert" in ctx


def test_answer_agent_deterministic_synthesis() -> None:
    """Verify answer synthesis produces formatted markdown when model is omitted."""
    provider = ProviderRecord(
        provider_id="P1",
        npi="9990001111",
        name="Dr. Jane Smith, DDS",
        specialty="Pediatric Dentistry",
        facility_name="Houston Children's Dental Clinic",
        city="Houston",
        state="TX",
        source="NPPES-Demo-Fixture",
    )
    evidence = ClinicalEvidenceRecord(
        record_id="E1",
        title="Early Caries Prevention",
        source="PubMed-Demo-Fixture",
        summary="Early visits prevent caries.",
        evidence_type="research_study",
        year=2024,
        citation_ref="PMID:DEMO-3829101",
    )

    state: HealthcareWorkflowState = {
        "original_query": "Pediatric dentists in Houston",
        "provider_candidates": [provider],
        "clinical_evidence": [evidence],
        "patient_education_evidence": [],
        "validation_results": {},
    }
    result = synthesize_answer(state, model_adapter=None)

    assert "Dr. Jane Smith, DDS" in result["final_answer"]
    assert "Early Caries Prevention" in result["final_answer"]
    assert "fixture" in result["final_answer"].lower()


def test_healthcare_graph_compilation_and_execution() -> None:
    """Verify full LangGraph StateGraph executes offline from START to END."""
    graph_builder = create_healthcare_graph(provider_retriever=FixtureProviderRetriever())
    app = graph_builder.compile()
    assert app is not None

    result = run_healthcare_workflow(
        query="Find pediatric dentists in Houston",
        provider_retriever=FixtureProviderRetriever(),
    )

    assert result["request_id"] is not None
    assert result["search_plan"]["city"] == "Houston"
    assert len(result["provider_candidates"]) >= 2
    assert len(result["clinical_evidence"]) >= 1
    assert result["validation_results"]["is_valid"] is True
    assert len(result["final_answer"]) > 50
    assert result["execution_metadata"]["answer_completed"] is True
