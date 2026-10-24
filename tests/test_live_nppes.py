"""Opt-in live integration tests against the public CMS NPPES Registry API v2.1.

Enabled only when HEALTHCARE_AGENTS_LIVE_TESTS=1 is set in the environment.
Offline CI on GitHub Actions runs without these live network calls.
"""

import os

import pytest

from healthcare_agents.retrieval.nppes_client import NPPESProviderRetriever
from healthcare_agents.workflows.healthcare_graph import run_healthcare_workflow

LIVE_ENABLED = os.getenv("HEALTHCARE_AGENTS_LIVE_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Live tests disabled by environment variable",
)


def test_live_nppes_query_pediatric_dentistry_houston() -> None:
    """Execute real public NPPES query for pediatric dentists in Houston, Texas."""
    retriever = NPPESProviderRetriever(timeout_seconds=15.0)
    records = retriever.search_providers(
        specialty="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=5,
    )

    assert len(records) > 0, "Expected at least 1 real pediatric dentist in Houston, TX"
    first = records[0]

    # Validate essential fields
    assert first.npi.isdigit() and len(first.npi) == 10
    assert first.name
    assert "Dentist" in first.specialty or "Pediatric" in first.specialty
    assert first.city.upper() == "HOUSTON"
    assert first.state.upper() == "TX"
    assert first.is_synthetic is False
    assert first.source == "CMS-NPPES-Live"
    assert first.practice_address != ""
    assert first.retrieval_timestamp != ""


def test_live_nppes_direct_npi_lookup() -> None:
    """Execute direct NPI lookup for a known public NPI."""
    retriever = NPPESProviderRetriever(timeout_seconds=15.0)
    # Search for an initial provider
    records = retriever.search_providers(
        specialty="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=1,
    )
    assert len(records) == 1
    target_npi = records[0].npi

    # Directly lookup that NPI
    direct_lookup = retriever.search_providers(npi=target_npi)
    assert len(direct_lookup) == 1
    assert direct_lookup[0].npi == target_npi
    assert direct_lookup[0].name == records[0].name


def test_live_workflow_with_nppes_and_gemma4() -> None:
    """Execute full LangGraph healthcare workflow with real NPPES and local Gemma 4."""
    from healthcare_agents.config import get_settings
    from healthcare_agents.models import get_model_adapter

    settings = get_settings()
    model_adapter = get_model_adapter(
        provider=settings.model_provider,
        base_url=settings.ollama_base_url,
        model_name=settings.model_name,
        timeout_seconds=settings.model_timeout_seconds,
    )
    nppes_retriever = NPPESProviderRetriever(timeout_seconds=15.0)

    result = run_healthcare_workflow(
        query="Find pediatric dentists in Houston",
        model_adapter=model_adapter,
        provider_retriever=nppes_retriever,
    )

    assert result["request_id"]
    assert result["validation_results"]["is_valid"] is True
    assert len(result["provider_candidates"]) >= 1

    # Verify candidate records are live
    first_prov = result["provider_candidates"][0]
    assert first_prov.is_synthetic is False
    assert first_prov.source == "CMS-NPPES-Live"
    assert first_prov.npi.isdigit()

    # Verify answer synthesis
    assert len(result["final_answer"]) > 50
    assert result["execution_metadata"]["provider_completed"] is True
    assert result["execution_metadata"]["answer_completed"] is True
