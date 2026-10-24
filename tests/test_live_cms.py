"""Opt-in live integration tests against official CMS Provider Data Catalog APIs.

Enabled only when HEALTHCARE_AGENTS_LIVE_TESTS=1 is set in the environment.
Offline CI on GitHub Actions runs without these live network calls.
"""

import os

import pytest

from healthcare_agents.models import OllamaAdapter
from healthcare_agents.retrieval.cms_client import (
    CMS_DATASET_CLINICIAN_MIPS,
    CMS_DATASET_HOSPITAL_GENERAL,
    CMSProviderDataRetriever,
)
from healthcare_agents.workflows.healthcare_graph import run_healthcare_workflow

LIVE_ENABLED = os.getenv("HEALTHCARE_AGENTS_LIVE_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Live tests disabled by environment variable",
)


def test_live_cms_hospital_general_information() -> None:
    """Query live CMS Provider Data Catalog for Houston general hospital info."""
    retriever = CMSProviderDataRetriever(timeout_seconds=20.0)
    hospitals = retriever.search_facility_quality(
        city="Houston",
        state="TX",
        limit=3,
    )

    assert len(hospitals) > 0, "Expected at least 1 hospital in Houston from CMS dataset xubh-q36u"
    first = hospitals[0]
    assert first.entity_type == "Facility"
    assert first.city.upper() == "HOUSTON"
    assert first.state.upper() == "TX"
    assert first.dataset_id == CMS_DATASET_HOSPITAL_GENERAL
    assert not first.is_synthetic
    assert first.source_url.startswith("https://data.cms.gov/provider-data/")


def test_live_cms_clinician_mips_performance() -> None:
    """Query live CMS Provider Data Catalog for confirmed clinician NPI with MIPS score."""
    retriever = CMSProviderDataRetriever(timeout_seconds=20.0)
    # NPI 1003809641 (Robert Davidson) is confirmed present in PY 2024 MIPS dataset a174-a962
    records = retriever.get_provider_quality(npi="1003809641")
    assert len(records) > 0, "Expected MIPS records for confirmed clinician NPI"
    mips_rec = next(r for r in records if r.measure_id == "FINAL_MIPS_SCORE")
    assert mips_rec.score != ""
    assert "DAVIDSON" in mips_rec.entity_name.upper()
    assert mips_rec.dataset_id == CMS_DATASET_CLINICIAN_MIPS
    assert not mips_rec.is_synthetic


def test_live_full_workflow_with_nppes_pubmed_and_cms() -> None:
    """Execute end-to-end LangGraph workflow in live mode with NPPES, PubMed, and CMS."""
    os.environ["RETRIEVAL_MODE"] = "live"
    try:
        adapter = OllamaAdapter(model_name="gemma4:e2b", timeout_seconds=120)
        state = run_healthcare_workflow(
            query="Find pediatric dentists in Houston and research on pediatric dental anxiety",
            model_adapter=adapter,
        )

        providers = state.get("provider_candidates", [])
        evidence = state.get("clinical_evidence", [])
        validation = state.get("validation_results", {})
        final_answer = state.get("final_answer", "")

        # NPPES live providers
        assert len(providers) > 0
        assert all(not p.is_synthetic for p in providers)

        # PubMed live evidence
        assert len(evidence) > 0
        assert all(not e.is_synthetic for e in evidence)

        # Confirm PMID 39046104 (dementia) was NOT included
        assert all(e.pmid != "39046104" for e in evidence)

        # Validation status
        assert validation.get("is_valid") is True
        assert validation.get("provenance_verified") is True

        # Final answer mentions
        assert len(final_answer) > 0
        assert "Pediatric" in final_answer
    finally:
        os.environ["RETRIEVAL_MODE"] = "fixture"
