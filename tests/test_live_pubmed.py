"""Opt-in live integration tests against NCBI Entrez PubMed E-utilities.

Enabled only when HEALTHCARE_AGENTS_LIVE_TESTS=1 is set in the environment.
Offline CI on GitHub Actions runs without these live network calls.
"""

import os

import pytest

from healthcare_agents.models import OllamaAdapter
from healthcare_agents.retrieval.pubmed_client import PubMedEvidenceRetriever
from healthcare_agents.workflows.healthcare_graph import run_healthcare_workflow

LIVE_ENABLED = os.getenv("HEALTHCARE_AGENTS_LIVE_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Live tests disabled by environment variable",
)


def test_live_pubmed_search_articles() -> None:
    """Execute real ESearch and EFetch against PubMed for pediatric dentistry dental anxiety."""
    retriever = PubMedEvidenceRetriever(timeout_seconds=15.0)
    records = retriever.search_evidence(
        topic="pediatric dentistry dental anxiety",
        limit=3,
    )

    assert len(records) > 0, "Expected at least 1 real PubMed article on pediatric dental anxiety"
    first = records[0]

    # Validate essential fields
    assert first.pmid.isdigit()
    assert first.title
    assert first.year >= 1990
    assert first.is_synthetic is False
    assert first.source == "PubMed-Live"
    assert first.pubmed_url == f"https://pubmed.ncbi.nlm.nih.gov/{first.pmid}/"
    assert first.retrieval_timestamp != ""
    assert first.source_type == "PubMed"


def test_live_nppes_and_pubmed_in_workflow() -> None:
    """Execute LangGraph workflow with both real NPPES and real PubMed retrievers."""
    os.environ["RETRIEVAL_MODE"] = "live"
    try:
        adapter = OllamaAdapter(model_name="gemma4:e2b", timeout_seconds=120)
        state = run_healthcare_workflow(
            query="Find pediatric dentists in Houston and research on pediatric dental anxiety",
            model_adapter=adapter,
        )

        providers = state.get("provider_candidates", [])
        clinical_evidence = state.get("clinical_evidence", [])
        validation = state.get("validation_results", {})
        final_answer = state.get("final_answer", "")

        # Verify live NPPES retrieved real providers
        assert len(providers) > 0
        assert any(not p.is_synthetic for p in providers)
        assert all(p.city.upper() == "HOUSTON" for p in providers)

        # Verify live PubMed retrieved real articles
        assert len(clinical_evidence) > 0
        assert any(not e.is_synthetic for e in clinical_evidence)
        assert all(e.source == "PubMed-Live" for e in clinical_evidence)

        # Verify validation passed
        assert validation.get("is_valid") is True

        # Verify final answer mentions retrieved content
        assert final_answer != ""
    finally:
        os.environ.pop("RETRIEVAL_MODE", None)
