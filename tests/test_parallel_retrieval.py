"""Tests for parallel multi-source healthcare retrieval and CMS dependency handling."""

from __future__ import annotations

from typing import Any

from healthcare_agents.planning.fanout import build_deterministic_fanout
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.retrieval.parallel_retriever import execute_parallel_retrieval
from healthcare_agents.workflows.state import SearchPlan


def test_parallel_retrieval_execution() -> None:
    """Verify concurrent multi-source retrieval executes all sources and satisfies dependencies."""
    search_plan: SearchPlan = {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "evidence_topics": ["dental anxiety"],
        "intent_description": "Find pediatric dentists and research anxiety",
    }
    fanout = build_deterministic_fanout(
        request_id="req-par-1",
        original_query="Find pediatric dentists in Houston and research pediatric dental anxiety",
        search_plan=search_plan,
    )

    prov_retriever = FixtureProviderRetriever()
    ev_retriever = FixtureEvidenceRetriever()
    edu_retriever = FixturePatientEducationRetriever()
    q_retriever = FixtureQualityRetriever()

    results = execute_parallel_retrieval(
        fanout_plan=fanout,
        provider_retriever=prov_retriever,
        evidence_retriever=ev_retriever,
        patient_education_retriever=edu_retriever,
        quality_retriever=q_retriever,
        max_workers=4,
    )

    assert len(results["provider_candidates"]) > 0
    assert len(results["clinical_evidence"]) > 0
    assert len(results["patient_education_evidence"]) > 0
    assert len(results["execution_events"]) >= 4

    # Verify each retrieval event captured monotonic duration and query summary
    for ev in results["execution_events"]:
        assert ev["duration_ms"] >= 0.0
        assert ev["status"] == "completed"
        assert ev["query_summary"]


def test_parallel_retrieval_partial_failure_tolerance() -> None:
    """Verify system tolerates individual source failures without dropping other sources."""
    search_plan: SearchPlan = {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "evidence_topics": ["dental anxiety"],
        "intent_description": "Failure tolerance test",
    }
    fanout = build_deterministic_fanout(
        request_id="req-par-fail",
        original_query="Find pediatric dentists in Houston",
        search_plan=search_plan,
    )

    class FailingPubMedRetriever(FixtureEvidenceRetriever):
        def search_evidence(
            self, topic: str, evidence_type: str | None = None, limit: int = 5
        ) -> list[Any]:
            raise ConnectionError("Simulated PubMed NCBI gateway timeout")

    prov_retriever = FixtureProviderRetriever()
    ev_retriever = FailingPubMedRetriever()
    edu_retriever = FixturePatientEducationRetriever()
    q_retriever = FixtureQualityRetriever()

    results = execute_parallel_retrieval(
        fanout_plan=fanout,
        provider_retriever=prov_retriever,
        evidence_retriever=ev_retriever,
        patient_education_retriever=edu_retriever,
        quality_retriever=q_retriever,
        max_workers=4,
    )

    # Provider and Patient Education must succeed despite PubMed failure
    assert len(results["provider_candidates"]) > 0
    assert len(results["patient_education_evidence"]) > 0
    assert len(results["clinical_evidence"]) == 0
    assert any("PubMed retrieval error" in err for err in results["errors"])

    # Failed query event recorded accurately
    failed_event = next(e for e in results["execution_events"] if e["stage"] == "PubMed Retrieval")
    assert failed_event["status"] == "failed"
    assert failed_event["error_type"] == "ConnectionError"


def test_parallel_retrieval_empty_npis() -> None:
    """Verify CMS query handles empty discovered provider NPIs gracefully."""
    from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery

    fanout = FanOutPlan(request_id="req-empty-npis", original_query="CMS test")
    fanout.add_query(
        PlannedQuery(
            query_id="q-cms-empty",
            parent_request_id="req-empty-npis",
            source="CMS",
            query_text="CMS lookups",
            search_params={"dependent_on": "candidate_npis"},
            intent_category="quality_metrics",
            priority=3,
        )
    )

    class EmptyProviderRetriever(FixtureProviderRetriever):
        def search_providers(
            self,
            specialty: str | None = None,
            city: str | None = None,
            state: str | None = None,
            npi: str | None = None,
            limit: int = 10,
        ) -> list[Any]:
            return []

    results = execute_parallel_retrieval(
        fanout_plan=fanout,
        provider_retriever=EmptyProviderRetriever(),
        evidence_retriever=FixtureEvidenceRetriever(),
        patient_education_retriever=FixturePatientEducationRetriever(),
        quality_retriever=FixtureQualityRetriever(),
    )

    cms_event = next(e for e in results["execution_events"] if e["stage"] == "CMS Retrieval")
    assert cms_event["status"] == "completed"
    assert cms_event["result_count"] == 0
    assert "0 candidate NPIs" in cms_event["output_summary"]


def test_parallel_retrieval_with_topics_list() -> None:
    """Verify MedlinePlus retrieval executes multi-topic lists and compound strings."""
    from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery

    fanout = FanOutPlan(request_id="req-topics-list", original_query="topics test")
    fanout.add_query(
        PlannedQuery(
            query_id="q-med-topics",
            parent_request_id="req-topics-list",
            source="MedlinePlus",
            query_text="child dental health and anxiety",
            search_params={"topics": ["child dental health", "anxiety"], "language": "en"},
            intent_category="patient_education",
            priority=2,
        )
    )

    results = execute_parallel_retrieval(
        fanout_plan=fanout,
        provider_retriever=FixtureProviderRetriever(),
        evidence_retriever=FixtureEvidenceRetriever(),
        patient_education_retriever=FixturePatientEducationRetriever(),
        quality_retriever=FixtureQualityRetriever(),
    )
    assert len(results["patient_education_evidence"]) > 0
