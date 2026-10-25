"""Unit tests for FastAPI endpoints, Pydantic schemas, and HealthcareSearchService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from healthcare_agents import __version__
from healthcare_agents.api.app import create_app
from healthcare_agents.api.schemas import (
    HealthResponse,
    ReadinessResponse,
    SearchRequest,
    SearchResponse,
    SystemStatusResponse,
)
from healthcare_agents.api.service import HealthcareSearchService
from healthcare_agents.evidence.schemas import (
    ProvenanceRecord,
    RelevanceAssessment,
    StructuredDiscoveryResult,
    UnifiedEvidenceItem,
)


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Verify GET /health returns 200 and valid schema."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == __version__
    assert "timestamp" in data
    # Validate against Pydantic schema
    model = HealthResponse.model_validate(data)
    assert model.status == "healthy"


def test_ready_endpoint(client: TestClient) -> None:
    """Verify GET /ready returns component status."""
    with (
        patch(
            "healthcare_agents.models.ollama_adapter.OllamaAdapter.check_service_health",
            return_value=True,
        ),
        patch(
            "healthcare_agents.models.ollama_adapter.OllamaAdapter.is_available",
            return_value=True,
        ),
    ):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["status"] == "ready"
        assert data["ollama_service_available"] is True
        assert data["model_installed"] is True
        model = ReadinessResponse.model_validate(data)
        assert model.ready is True


def test_ready_endpoint_degraded(client: TestClient) -> None:
    """Verify GET /ready handles unavailable Ollama."""
    with patch(
        "healthcare_agents.models.ollama_adapter.OllamaAdapter.check_service_health",
        return_value=False,
    ):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is False
        assert data["status"] == "not_ready"


def test_system_status_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/status returns system configuration and disclaimers."""
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == __version__
    assert "NPPES" in data["supported_sources"]
    assert "PubMed" in data["supported_sources"]
    assert "CMS Provider Data" in data["supported_sources"]
    assert "MedlinePlus" in data["supported_sources"]
    assert "disclaimer" in data
    assert "NPI" in data["disclaimer"]
    model = SystemStatusResponse.model_validate(data)
    assert len(model.supported_sources) == 4


def test_search_endpoint_validation_empty_query(client: TestClient) -> None:
    """Verify POST /api/v1/search rejects empty queries with 422."""
    resp = client.post("/api/v1/search", json={"query": "   "})
    assert resp.status_code == 422


def test_search_endpoint_validation_missing_query(client: TestClient) -> None:
    """Verify POST /api/v1/search rejects missing query payload with 422."""
    resp = client.post("/api/v1/search", json={})
    assert resp.status_code == 422


def test_search_endpoint_success_fixture_mode(client: TestClient) -> None:
    """Verify POST /api/v1/search in fixtures mode executes and returns SearchResponse."""
    req_body = {
        "query": "Find pediatric dentists in Houston",
        "retrieval_mode": "fixtures",
        "result_limit": 5,
    }
    resp = client.post("/api/v1/search", json=req_body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == req_body["query"]
    assert "provider_candidates" in data
    assert "clinical_research" in data
    assert "patient_education" in data
    assert "provenance_records" in data
    assert "grounded_answer" in data
    assert "limitations_disclaimer" in data

    # Verify Pydantic schema validation
    parsed = SearchResponse.model_validate(data)
    assert parsed.query == req_body["query"]
    assert len(parsed.provider_candidates) <= 5
    assert parsed.request_id is not None


def test_search_endpoint_handles_timeout(client: TestClient) -> None:
    """Verify POST /api/v1/search returns 504 on workflow timeout."""
    with patch(
        "healthcare_agents.api.service.HealthcareSearchService.execute_search",
        side_effect=TimeoutError("Model timed out"),
    ):
        resp = client.post("/api/v1/search", json={"query": "Find pediatric dentists in Houston"})
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"]


def test_search_endpoint_handles_unexpected_error(client: TestClient) -> None:
    """Verify POST /api/v1/search returns 500 on unexpected exceptions."""
    with patch(
        "healthcare_agents.api.service.HealthcareSearchService.execute_search",
        side_effect=RuntimeError("Unexpected workflow crash"),
    ):
        resp = client.post("/api/v1/search", json={"query": "Find pediatric dentists in Houston"})
        assert resp.status_code == 500
        assert "An error occurred" in resp.json()["detail"]


def test_search_service_direct_execution() -> None:
    """Verify HealthcareSearchService direct invocation with mock StructuredDiscoveryResult."""
    service = HealthcareSearchService()
    req = SearchRequest(query="Find pediatric dentists in Houston", retrieval_mode="fixtures")

    item = UnifiedEvidenceItem(
        evidence_id="NPPES:1234567890",
        source_type="NPPES",
        external_id="1234567890",
        title_or_name="Dr. Jane Doe",
        source_url="https://npiregistry.cms.hhs.gov/provider-view/1234567890",
        retrieval_timestamp="2026-10-25T10:00:00Z",
        published_or_updated="2026",
        relevance=RelevanceAssessment(
            score=1.0, is_relevant=True, selection_reason="Specialty and city match"
        ),
        provenance=ProvenanceRecord(
            source_name="NPPES",
            external_id="1234567890",
            canonical_url="https://npiregistry.cms.hhs.gov/provider-view/1234567890",
            retrieval_timestamp="2026-10-25T10:00:00Z",
            source_record_type="ProviderRecord",
            citation_id="NPPES-1234567890",
        ),
        citation_id="NPPES-1234567890",
        evidence_status="available",
        is_synthetic=True,
        known_limitations=("NPI does not guarantee licensure",),
        source_metadata={"specialty": "Pediatric Dentistry"},
    )

    mock_res = StructuredDiscoveryResult(
        query="Find pediatric dentists in Houston",
        interpreted_intent={"specialty": "Pediatric Dentistry", "city": "Houston"},
        provider_candidates=[item],
        clinical_research=[],
        cms_quality_data=[],
        patient_education=[],
        excluded_items=[],
        provenance_records=[item.provenance],
        relevance_explanations=["Specialty and city match"],
        missing_information=["CMS measures unavailable for dental"],
        source_errors=[],
        grounded_answer="Found Dr. Jane Doe [NPPES-1234567890] in Houston.",
    )

    with patch("healthcare_agents.api.service.create_healthcare_graph") as mock_graph:
        mock_app = MagicMock()
        mock_app.invoke.return_value = {
            "search_plan": mock_res.interpreted_intent,
            "structured_discovery_result": mock_res,
            "final_answer": mock_res.grounded_answer,
            "execution_metadata": {"mocked": True},
        }
        mock_graph.return_value.compile.return_value = mock_app

        resp = service.execute_search(req)
        assert resp.query == req.query
        assert len(resp.provider_candidates) == 1
        assert resp.provider_candidates[0].external_id == "1234567890"
        assert resp.grounded_answer == mock_res.grounded_answer
        assert len(resp.provenance_records) == 1
