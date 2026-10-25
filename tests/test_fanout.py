"""Unit and regression tests for intelligent query fan-out planning."""

from __future__ import annotations

from healthcare_agents.planning.fanout import build_deterministic_fanout, generate_fanout_plan
from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery
from healthcare_agents.workflows.state import SearchPlan


def test_planned_query_parameter_validation() -> None:
    """Verify source-specific search parameter validation rules."""
    # Valid NPPES query
    valid_nppes = PlannedQuery(
        query_id="q-1",
        parent_request_id="req-1",
        source="NPPES",
        query_text="Pediatric dentist Houston",
        search_params={"specialty": "Pediatric Dentistry", "city": "Houston", "state": "TX"},
        intent_category="provider_discovery",
    )
    assert valid_nppes.validate_parameters() is True

    # Valid PubMed query without PHI
    valid_pubmed = PlannedQuery(
        query_id="q-2",
        parent_request_id="req-1",
        source="PubMed",
        query_text="dental anxiety in pediatric patients",
        search_params={"topic": "dental anxiety in pediatric patients"},
        intent_category="clinical_research",
    )
    assert valid_pubmed.validate_parameters() is True

    # PubMed query containing SSN-like PHI pattern must fail validation
    phi_pubmed = PlannedQuery(
        query_id="q-3",
        parent_request_id="req-1",
        source="PubMed",
        query_text="Patient 123-45-6789 treatment records",
        search_params={},
        intent_category="clinical_research",
    )
    assert phi_pubmed.validate_parameters() is False

    # Valid MedlinePlus query
    valid_medline = PlannedQuery(
        query_id="q-4",
        parent_request_id="req-1",
        source="MedlinePlus",
        query_text="child dental health",
        search_params={"keyword": "child dental health"},
        intent_category="patient_education",
    )
    assert valid_medline.validate_parameters() is True

    # Empty MedlinePlus query fails validation
    empty_medline = PlannedQuery(
        query_id="q-5",
        parent_request_id="req-1",
        source="MedlinePlus",
        query_text=" ",
        search_params={},
        intent_category="patient_education",
    )
    assert empty_medline.validate_parameters() is False


def test_fanout_plan_semantic_deduplication() -> None:
    """Verify duplicate queries targeting the same source are pruned."""
    plan = FanOutPlan(
        request_id="req-dedup",
        original_query="child teeth",
        max_fanout=5,
    )
    q1 = PlannedQuery(
        query_id="q-med-1",
        parent_request_id="req-dedup",
        source="MedlinePlus",
        query_text="Child Dental Health",
        intent_category="patient_education",
    )
    q2 = PlannedQuery(
        query_id="q-med-2",
        parent_request_id="req-dedup",
        source="MedlinePlus",
        query_text="child dental health",  # Case difference duplicate
        intent_category="patient_education",
    )
    assert plan.add_query(q1) is True
    assert plan.add_query(q2) is False  # Rejected duplicate
    assert len(plan.queries) == 1


def test_build_deterministic_fanout_pediatric_dentist() -> None:
    """Verify deterministic fan-out for the primary milestone scenario."""
    search_plan: SearchPlan = {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "evidence_topics": ["dental anxiety", "pediatric dentistry"],
        "intent_description": "Find pediatric dentists and research anxiety",
    }
    fanout = build_deterministic_fanout(
        request_id="req-test-1",
        original_query="Find pediatric dentists in Houston and research pediatric dental anxiety",
        search_plan=search_plan,
    )

    sources = [q.source for q in fanout.queries]
    assert "NPPES" in sources
    assert "PubMed" in sources
    assert "MedlinePlus" in sources
    assert "CMS" in sources

    # Verify CMS dependency on NPPES candidate NPIs
    cms_q = next(q for q in fanout.queries if q.source == "CMS")
    assert len(cms_q.dependency_ids) > 0
    nppes_q = next(q for q in fanout.queries if q.source == "NPPES")
    assert nppes_q.query_id in cms_q.dependency_ids


def test_generate_fanout_plan_fallback() -> None:
    """Verify fallback to deterministic planner when model adapter is absent."""
    search_plan: SearchPlan = {
        "specialty": "Cardiology",
        "city": "Austin",
        "state": "TX",
        "evidence_topics": ["heart failure"],
        "intent_description": "Cardiology Austin",
    }
    fanout = generate_fanout_plan(
        request_id="req-test-2",
        original_query="Cardiologist in Austin",
        search_plan=search_plan,
        model_adapter=None,
    )
    assert len(fanout.queries) >= 3
    assert any(q.source == "NPPES" for q in fanout.queries)


def test_generate_fanout_plan_with_model_adapter() -> None:
    """Verify fan-out generation with a mock model adapter returning structured JSON."""
    from unittest.mock import MagicMock

    from healthcare_agents.models.base import BaseModelAdapter
    from healthcare_agents.models.schemas import ModelResponse

    mock_adapter = MagicMock(spec=BaseModelAdapter)
    mock_adapter.generate.return_value = ModelResponse(
        content="""{
            "strategy_notes": "Decomposed via LLM",
            "queries": [
                {
                    "source": "NPPES",
                    "query_text": "Dentist in Dallas, TX",
                    "intent_category": "provider_discovery",
                    "priority": 1,
                    "search_params": {"specialty": "Dentistry", "city": "Dallas", "state": "TX"}
                },
                {
                    "source": "PubMed",
                    "query_text": "dental caries prevention",
                    "intent_category": "clinical_research",
                    "priority": 1,
                    "search_params": {"topic": "dental caries prevention"}
                }
            ]
        }""",
        model="gemma4:mock",
    )

    search_plan: SearchPlan = {
        "specialty": "Dentistry",
        "city": "Dallas",
        "state": "TX",
        "evidence_topics": ["caries"],
        "intent_description": "Dentist in Dallas",
    }
    fanout = generate_fanout_plan(
        request_id="req-mock-llm",
        original_query="Dentist in Dallas",
        search_plan=search_plan,
        model_adapter=mock_adapter,
    )
    assert len(fanout.queries) == 2
    assert fanout.queries[0].source == "NPPES"
    assert fanout.queries[1].source == "PubMed"
