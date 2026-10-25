"""Regression tests for M7 Quick Demonstration Presets and Intent Routing."""

from __future__ import annotations

from healthcare_agents.agents.planner import plan_query
from healthcare_agents.evidence.ranking import rank_providers
from healthcare_agents.planning.fanout import generate_fanout_plan
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.workflows.healthcare_graph import run_healthcare_workflow
from healthcare_agents.workflows.state import HealthcareWorkflowState, SearchPlan


def test_preset_1_pediatric_dentist_discovery() -> None:
    """PRESET 1: 'Find pediatric dentists in Houston, Texas.'"""
    query = "Find pediatric dentists in Houston, Texas."
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    assert plan["specialty"] == "Pediatric Dentistry"
    assert plan["city"] == "Houston"
    assert plan["state"] == "TX"

    fanout = generate_fanout_plan("req-p1", query, plan)
    assert any(q.source == "NPPES" and "Houston" in q.query_text for q in fanout.queries)


def test_preset_2_best_pediatric_dentists_and_research() -> None:
    """PRESET 2: Best pediatric dentists in Houston + research."""
    query = (
        "Find the best pediatric dentists in Houston, Texas, and research pediatric dental anxiety."
    )
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    assert plan["specialty"] == "Pediatric Dentistry"
    assert plan["city"] == "Houston"
    assert plan["state"] == "TX"
    assert any("anxiety" in t for t in plan["evidence_topics"])

    fanout = generate_fanout_plan("req-p2", query, plan)
    sources = {q.source for q in fanout.queries}
    assert "NPPES" in sources
    assert "PubMed" in sources
    assert "MedlinePlus" in sources


def test_preset_3_tooth_cavity_symptom_routing_and_near_me() -> None:
    """PRESET 3: Tooth cavity symptom routing and near me handling.

    Verifies:
    - Symptom awareness: Possible tooth cavity routes to General Dentistry.
    - Location extraction: Uses Houston, Texas as geographic scope without asking for ZIP.
    - 'Near me' interpretation: Matches Houston-area providers without fabricating distances.
    - Patient education: Retrieves tooth decay and cavity care topics.
    """
    query = (
        "I live in Houston, Texas. I think I have a tooth cavity. Find the best dentists near me."
    )
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    assert plan["city"] == "Houston"
    assert plan["state"] == "TX"
    assert plan["specialty"] == "General Practice Dentistry"
    assert any("tooth decay" in t for t in plan["evidence_topics"])

    fanout = generate_fanout_plan("req-p3", query, plan)
    medline_queries = [q for q in fanout.queries if q.source == "MedlinePlus"]
    assert any("tooth decay" in q.query_text for q in medline_queries)

    # Execute workflow and ensure General Dentistry provider in Houston is retrieved
    prov_retriever = FixtureProviderRetriever()
    ev_retriever = FixtureEvidenceRetriever()
    edu_retriever = FixturePatientEducationRetriever()
    qual_retriever = FixtureQualityRetriever()

    res = run_healthcare_workflow(
        query=query,
        provider_retriever=prov_retriever,
        evidence_retriever=ev_retriever,
        quality_retriever=qual_retriever,
        patient_education_retriever=edu_retriever,
    )
    assert res["execution_metadata"].get("answer_completed") is True
    provs = res.get("provider_candidates", [])
    assert len(provs) > 0
    assert any("Houston" in p.city for p in provs)


def test_preset_4_pediatric_dental_anxiety_research() -> None:
    """PRESET 4: 'What does clinical research say about managing dental anxiety in children?'"""
    query = "What does clinical research say about managing dental anxiety in children?"
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    assert any("anxiety" in t for t in plan["evidence_topics"])
    fanout = generate_fanout_plan("req-p4", query, plan)
    pubmed_queries = [q for q in fanout.queries if q.source == "PubMed"]
    assert len(pubmed_queries) >= 1
    assert any("anxiety" in q.query_text for q in pubmed_queries)


def test_preset_5_child_dental_health_education() -> None:
    """PRESET 5: Child dental health patient education."""
    query = (
        "Find evidence-based patient education about children's dental health and preventive care."
    )
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    fanout = generate_fanout_plan("req-p5", query, plan)
    medline_queries = [q for q in fanout.queries if q.source == "MedlinePlus"]
    assert len(medline_queries) >= 1
    assert any("child dental health" in q.query_text for q in medline_queries)


def test_preset_6_compare_healthcare_evidence() -> None:
    """PRESET 6: Compare clinical research and patient education."""
    query = "Compare clinical research and patient education about pediatric dental anxiety."
    state: HealthcareWorkflowState = {"original_query": query}
    planned = plan_query(state)
    plan: SearchPlan = planned["search_plan"]

    fanout = generate_fanout_plan("req-p6", query, plan)
    sources = {q.source for q in fanout.queries}
    assert "PubMed" in sources
    assert "MedlinePlus" in sources


def test_best_match_ranking_principles() -> None:
    """Verify 'best' query terms rank by objective completeness without inventing reviews."""
    from healthcare_agents.evidence.normalization import normalize_provider_record
    from healthcare_agents.retrieval.base import ProviderRecord

    rec_incomplete = ProviderRecord(
        provider_id="P1",
        npi="1111111111",
        name="Dr. Partial Dentist",
        specialty="Dentistry",
        facility_name="Houston Center",
        city="Houston",
        state="TX",
        source="NPPES",
        practice_address="",
    )
    rec_complete = ProviderRecord(
        provider_id="P2",
        npi="2222222222",
        name="Dr. Complete Dentist",
        specialty="Dentistry",
        facility_name="Houston Clinic",
        city="Houston",
        state="TX",
        source="NPPES",
        practice_address="100 Main St",
    )

    item_incomplete = normalize_provider_record(rec_incomplete)
    item_complete = normalize_provider_record(rec_complete)

    ranked = rank_providers([item_incomplete, item_complete])
    # The provider with complete practice location and NPI stability ranks first
    assert ranked[0].external_id == "2222222222"
    assert ranked[1].external_id == "1111111111"
