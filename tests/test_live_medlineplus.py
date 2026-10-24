"""Opt-in live integration tests against U.S. NLM MedlinePlus Web Service.

Enabled only when HEALTHCARE_AGENTS_LIVE_TESTS=1 is set in the environment.
Offline CI on GitHub Actions runs without these live network calls.
"""

import os

import pytest

from healthcare_agents.models import OllamaAdapter
from healthcare_agents.retrieval.medlineplus_client import (
    MedlinePlusPatientEducationRetriever,
)
from healthcare_agents.workflows.healthcare_graph import run_healthcare_workflow

LIVE_ENABLED = os.getenv("HEALTHCARE_AGENTS_LIVE_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Live tests disabled by environment variable",
)


def test_live_medlineplus_keyword_search() -> None:
    """Execute real keyword search against MedlinePlus Web Service."""
    retriever = MedlinePlusPatientEducationRetriever(timeout_seconds=15.0)
    records = retriever.search_topics(
        keyword="child dental health",
        language="en",
        limit=3,
    )

    assert len(records) > 0, "Expected at least 1 MedlinePlus health topic"
    first = records[0]
    assert first.title != ""
    assert first.official_url.startswith("https://medlineplus.gov/")
    assert first.evidence_type == "patient_education"
    assert first.source == "MedlinePlus-Live"
    assert first.is_synthetic is False
    assert first.language == "en"
    assert first.retrieval_timestamp != ""


def test_live_medlineplus_spanish_search() -> None:
    """Execute real Spanish keyword search against MedlinePlus Web Service."""
    retriever = MedlinePlusPatientEducationRetriever(timeout_seconds=15.0)
    records = retriever.search_topics(
        keyword="salud dental infantil",
        language="es",
        limit=3,
    )

    assert len(records) > 0, "Expected at least 1 Spanish MedlinePlus health topic"
    first = records[0]
    assert first.title != ""
    assert "https://medlineplus.gov/spanish/" in first.official_url
    assert first.language == "es"


def test_live_all_four_sources_in_workflow() -> None:
    """Execute LangGraph workflow with NPPES + PubMed + CMS + MedlinePlus all in live mode."""
    os.environ["RETRIEVAL_MODE"] = "live"
    try:
        adapter = OllamaAdapter(model_name="gemma4:e2b", timeout_seconds=120)
        state = run_healthcare_workflow(
            query="Find pediatric dentists in Houston and research on pediatric dental anxiety",
            model_adapter=adapter,
        )

        providers = state.get("provider_candidates", [])
        clinical_evidence = state.get("clinical_evidence", [])
        patient_education = state.get("patient_education_evidence", [])
        validation = state.get("validation_results", {})
        final_answer = state.get("final_answer", "")

        # 1. NPPES
        assert len(providers) > 0
        assert any(not p.is_synthetic for p in providers)

        # 2. PubMed
        assert len(clinical_evidence) > 0
        assert any(not e.is_synthetic for e in clinical_evidence)

        # 3. MedlinePlus
        assert len(patient_education) > 0
        assert any(not e.is_synthetic for e in patient_education)
        assert any("medlineplus.gov" in (e.official_url or "") for e in patient_education)

        # 4. Validation
        assert validation.get("is_valid") is True

        # 5. Final Answer
        assert final_answer != ""
    finally:
        os.environ.pop("RETRIEVAL_MODE", None)
