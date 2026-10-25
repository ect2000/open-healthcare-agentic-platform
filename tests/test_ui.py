"""Unit tests for Streamlit UI components, api client, and UI views."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

from healthcare_agents.api.schemas import (
    EvidenceItemResponse,
    HealthResponse,
    ProvenanceResponse,
    ReadinessResponse,
    SearchResponse,
)
from healthcare_agents.ui.api_client import HealthcareApiClient
from healthcare_agents.ui.components import (
    render_cms_data_section,
    render_disclaimer_banner,
    render_medlineplus_card,
    render_provenance_and_citations,
    render_provider_card,
    render_pubmed_card,
)


@pytest.fixture
def sample_search_response() -> SearchResponse:
    """Fixture returning a realistic SearchResponse instance."""
    prov = EvidenceItemResponse(
        evidence_id="NPPES:1000000001",
        source_type="NPPES",
        external_id="1000000001",
        title_or_name="Dr. Jane Houston DDS",
        source_url="https://npiregistry.cms.hhs.gov/provider-view/1000000001",
        retrieval_timestamp="2026-10-25T10:00:00Z",
        published_or_updated="2026",
        relevance_score=1.0,
        is_relevant=True,
        selection_reason="Pediatric Dentistry in Houston",
        exclusion_reason="",
        citation_id="NPPES-1000000001",
        evidence_status="available",
        is_synthetic=False,
        known_limitations=["NPI is administrative only"],
        metadata={
            "specialty": "Pediatric Dentistry",
            "practice_address": "123 Medical Center Blvd, Houston, TX 77030",
            "phone": "713-555-0199",
        },
    )

    pubmed = EvidenceItemResponse(
        evidence_id="PUBMED:12345678",
        source_type="PubMed",
        external_id="12345678",
        title_or_name="Behavioral Guidance in Pediatric Dental Anxiety: A Randomized Trial",
        source_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        retrieval_timestamp="2026-10-25T10:00:00Z",
        published_or_updated="2024",
        relevance_score=0.95,
        is_relevant=True,
        selection_reason="Topical match on pediatric dental anxiety",
        exclusion_reason="",
        citation_id="PMID:12345678",
        evidence_status="available",
        is_synthetic=False,
        known_limitations=["Biomedical literature only"],
        metadata={
            "summary": "Evaluation of non-pharmacological behavioral management in anxious pediatric patients.",
            "authors": ["Smith J", "Johnson E"],
            "journal": "Pediatr Dent",
            "year": 2024,
        },
    )

    mlp = EvidenceItemResponse(
        evidence_id="MEDLINEPLUS:T101",
        source_type="MedlinePlus",
        external_id="T101",
        title_or_name="Child Dental Health",
        source_url="https://medlineplus.gov/childdentalhealth.html",
        retrieval_timestamp="2026-10-25T10:00:00Z",
        published_or_updated="2025",
        relevance_score=0.9,
        is_relevant=True,
        selection_reason="Consumer health topic on child oral health",
        exclusion_reason="",
        citation_id="MedlinePlus:childdentalhealth",
        evidence_status="available",
        is_synthetic=False,
        known_limitations=["Consumer education only"],
        metadata={
            "summary": "Tips and guidance for parents on establishing healthy oral hygiene in children.",
            "language": "en",
        },
    )

    prov_rec = ProvenanceResponse(
        source_name="NPPES Registry",
        external_id="1000000001",
        canonical_url="https://npiregistry.cms.hhs.gov/provider-view/1000000001",
        retrieval_timestamp="2026-10-25T10:00:00Z",
        source_record_type="ProviderRecord",
        citation_id="NPPES-1000000001",
        is_synthetic=False,
        language="en",
    )

    return SearchResponse(
        request_id="req-test-12345",
        query="Find pediatric dentists in Houston and research on pediatric dental anxiety",
        interpreted_intent={"specialty": "Pediatric Dentistry", "city": "Houston"},
        provider_candidates=[prov],
        clinical_research=[pubmed],
        cms_quality_data=[],
        patient_education=[mlp],
        excluded_items=[],
        provenance_records=[prov_rec],
        relevance_explanations=["Specialty and city matched"],
        missing_information=["CMS outpatient metrics not applicable to pediatric dentists"],
        source_errors=[],
        grounded_answer="Found Dr. Jane Houston DDS [NPPES-1000000001]. Research [PMID:12345678] and MedlinePlus support behavioral guidance.",
        execution_metadata={"provider_count": 1, "clinical_count": 1, "education_count": 1},
        limitations_disclaimer="Administrative disclaimer text",
        created_at="2026-10-25T10:00:00Z",
    )


def test_api_client_health() -> None:
    """Verify HealthcareApiClient check_health method."""
    client = HealthcareApiClient(base_url="http://testserver")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "healthy",
        "version": "0.5.0",
        "environment": "development",
        "timestamp": "2026-10-25T10:00:00Z",
    }
    with patch("httpx.Client.get", return_value=mock_resp):
        res = client.check_health()
        assert res is not None
        assert res.status == "healthy"
        assert res.version == "0.5.0"


def test_api_client_readiness() -> None:
    """Verify HealthcareApiClient check_readiness method."""
    client = HealthcareApiClient(base_url="http://testserver")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ready": True,
        "status": "ready",
        "version": "0.5.0",
        "ollama_service_available": True,
        "model_installed": True,
        "model_name": "gemma4:e2b",
        "retrieval_mode": "fixtures",
        "four_sources_configured": True,
        "details": {},
    }
    with patch("httpx.Client.get", return_value=mock_resp):
        res = client.check_readiness()
        assert res is not None
        assert res.ready is True
        assert res.model_installed is True


def test_api_client_system_status() -> None:
    """Verify HealthcareApiClient get_system_status method."""
    client = HealthcareApiClient(base_url="http://testserver")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "version": "0.5.0",
        "model": "gemma4:e2b",
        "ollama_url": "http://localhost:11434",
        "retrieval_mode": "fixtures",
        "supported_sources": ["NPPES", "PubMed", "CMS Provider Data", "MedlinePlus"],
        "features": {"unified_evidence_layer": True},
        "disclaimer": "Administrative disclaimer",
    }
    with patch("httpx.Client.get", return_value=mock_resp):
        res = client.get_system_status()
        assert res is not None
        assert len(res.supported_sources) == 4


def test_api_client_search(sample_search_response: SearchResponse) -> None:
    """Verify HealthcareApiClient search method."""
    client = HealthcareApiClient(base_url="http://testserver")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_search_response.model_dump()
    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.search(query="Find pediatric dentists in Houston")
        assert res.query == sample_search_response.query
        assert len(res.provider_candidates) == 1
        assert res.provider_candidates[0].external_id == "1000000001"


def test_ui_components_render(sample_search_response: SearchResponse) -> None:
    """Verify Streamlit UI component renderers execute without exceptions."""
    with patch("streamlit.markdown") as mock_md, patch("streamlit.container") as mock_cont:
        mock_cont.return_value.__enter__ = MagicMock()
        mock_cont.return_value.__exit__ = MagicMock()

        # Render provider card
        render_provider_card(sample_search_response.provider_candidates[0])
        assert mock_md.called

        # Render pubmed card
        render_pubmed_card(sample_search_response.clinical_research[0])

        # Render medlineplus card
        render_medlineplus_card(sample_search_response.patient_education[0])

        # Render disclaimer
        render_disclaimer_banner(is_synthetic=False)
        render_disclaimer_banner(is_synthetic=True)

        # Render CMS non-applicability and applicability
        render_cms_data_section([], ["CMS metrics not applicable"])
        render_cms_data_section(
            [
                EvidenceItemResponse(
                    evidence_id="CMS:HOSP-1234",
                    source_type="CMS",
                    external_id="HOSP-1234",
                    title_or_name="Houston General Hospital",
                    source_url="https://data.cms.gov",
                    retrieval_timestamp="2026-10-25T10:00:00Z",
                    published_or_updated="2025",
                    relevance_score=0.8,
                    is_relevant=True,
                    selection_reason="Facility match",
                    exclusion_reason="",
                    citation_id="CMS:HOSP-1234",
                    evidence_status="available",
                    is_synthetic=False,
                    known_limitations=[],
                    metadata={"dataset_id": "xubh-q36u", "entity_type": "Facility"},
                )
            ],
            [],
        )

        # Render provenance and citations
        render_provenance_and_citations(sample_search_response)


def test_streamlit_app_test_initialization(sample_search_response: SearchResponse) -> None:
    """Verify Streamlit AppTest initializes app layout and sidebar."""
    with patch("healthcare_agents.ui.api_client.HealthcareApiClient.check_health") as mock_h:
        with patch("healthcare_agents.ui.api_client.HealthcareApiClient.check_readiness") as mock_r:
            mock_h.return_value = HealthResponse(
                status="healthy",
                version="0.5.0",
                environment="development",
                timestamp="2026-10-25T10:00:00Z",
            )
            mock_r.return_value = ReadinessResponse(
                ready=True,
                status="ready",
                version="0.5.0",
                ollama_service_available=True,
                model_installed=True,
                model_name="gemma4:e2b",
                retrieval_mode="fixtures",
                four_sources_configured=True,
                details={},
            )

            import inspect

            import healthcare_agents.ui.app as ui_app_module

            script_path = inspect.getfile(ui_app_module)
            at = AppTest.from_file(script_path, default_timeout=15.0)
            at.run()
            assert not at.exception
            # Verify buttons exist in sidebar
            assert len(at.button) >= 4


def test_streamlit_app_test_search_flow(sample_search_response: SearchResponse) -> None:
    """Verify Streamlit AppTest form submission and results rendering."""
    with (
        patch("healthcare_agents.ui.api_client.HealthcareApiClient.check_health") as mock_h,
        patch("healthcare_agents.ui.api_client.HealthcareApiClient.check_readiness") as mock_r,
        patch("healthcare_agents.ui.api_client.HealthcareApiClient.search") as mock_s,
    ):
        mock_h.return_value = HealthResponse(
            status="healthy",
            version="0.5.0",
            environment="development",
            timestamp="2026-10-25T10:00:00Z",
        )
        mock_r.return_value = ReadinessResponse(
            ready=True,
            status="ready",
            version="0.5.0",
            ollama_service_available=True,
            model_installed=True,
            model_name="gemma4:e2b",
            retrieval_mode="fixtures",
            four_sources_configured=True,
            details={},
        )
        mock_s.return_value = sample_search_response

        import inspect

        import healthcare_agents.ui.app as ui_app_module

        script_path = inspect.getfile(ui_app_module)
        at = AppTest.from_file(script_path, default_timeout=15.0)
        at.run()
        # Find search button inside form and click
        if len(at.button) > 0:
            at.button[0].click().run()
        assert not at.exception
