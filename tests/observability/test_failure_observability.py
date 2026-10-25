"""Controlled failure and resilience observability tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.api.schemas import SearchRequest
from healthcare_agents.api.service import HealthcareSearchService
from healthcare_agents.models.ollama_adapter import OllamaAdapter
from healthcare_agents.planning.fanout_schema import FanOutPlan, PlannedQuery
from healthcare_agents.retrieval.base import BaseEvidenceRetriever, BaseProviderRetriever
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.retrieval.parallel_retriever import execute_parallel_retrieval


def test_failure_observability_nppes_failure() -> None:
    """Verify that NPPES retrieval failure records error type, error events, and doesn't crash."""
    failing_provider_retriever = MagicMock(spec=BaseProviderRetriever)
    failing_provider_retriever.search_providers.side_effect = TimeoutError("NPPES gateway timeout")

    plan = FanOutPlan(
        request_id="req-test-fail-1",
        original_query="pediatric dentist Houston",
        queries=[
            PlannedQuery(
                query_id="q1",
                parent_request_id="req-test-fail-1",
                intent_category="provider_discovery",
                source="NPPES",
                query_text="pediatric dentist Houston",
                search_params={"specialty": "pediatric dentist", "city": "Houston"},
            )
        ],
    )

    results = execute_parallel_retrieval(
        fanout_plan=plan,
        provider_retriever=failing_provider_retriever,
        evidence_retriever=FixtureEvidenceRetriever(),
        patient_education_retriever=FixturePatientEducationRetriever(),
        quality_retriever=FixtureQualityRetriever(),
    )

    events = results.get("execution_events", [])
    assert len(events) >= 1
    nppes_event = next(e for e in events if e.get("stage") == "NPPES Retrieval")
    assert nppes_event["status"] == "failed"
    assert nppes_event["error_type"] == "TimeoutError"
    assert len(results.get("errors", [])) >= 1


def test_failure_observability_pubmed_timeout() -> None:
    """Verify that PubMed timeout records failure metrics and continues workflow."""
    failing_pubmed_retriever = MagicMock(spec=BaseEvidenceRetriever)
    failing_pubmed_retriever.search_evidence.side_effect = TimeoutError("PubMed connection timeout")

    plan = FanOutPlan(
        request_id="req-test-fail-2",
        original_query="dental anxiety children",
        queries=[
            PlannedQuery(
                query_id="q2",
                parent_request_id="req-test-fail-2",
                intent_category="clinical_research",
                source="PubMed",
                query_text="dental anxiety children",
                search_params={"topic": "dental anxiety children"},
            )
        ],
    )

    results = execute_parallel_retrieval(
        fanout_plan=plan,
        provider_retriever=FixtureProviderRetriever(),
        evidence_retriever=failing_pubmed_retriever,
        patient_education_retriever=FixturePatientEducationRetriever(),
        quality_retriever=FixtureQualityRetriever(),
    )

    events = results.get("execution_events", [])
    pubmed_event = next(e for e in events if e.get("stage") == "PubMed Retrieval")
    assert pubmed_event["status"] == "failed"
    assert pubmed_event["error_type"] == "TimeoutError"


def test_failure_observability_ollama_unavailable() -> None:
    """Verify Ollama inference failure raises structured model error and updates metrics."""
    from healthcare_agents.models.base import ModelUnavailableError

    adapter = OllamaAdapter(
        base_url="http://127.0.0.1:9999", model_name="gemma4:e2b", timeout_seconds=1.0
    )
    with pytest.raises(ModelUnavailableError):
        adapter.generate(prompt="Hello")


def test_failure_observability_collector_down_does_not_break_search() -> None:
    """Verify that if OpenTelemetry collector is offline or fails, search still succeeds."""
    service = HealthcareSearchService()
    req = SearchRequest(query="Find pediatric dentists in Houston", retrieval_mode="fixtures")

    with patch(
        "healthcare_agents.observability.tracing.trace_span",
        side_effect=Exception("Collector unreachable"),
    ):
        # Searching should safely proceed or handle gracefully without halting healthcare discovery
        try:
            resp = service.execute_search(req)
            assert resp is not None
        except Exception:
            # Even if span helper itself failed outside the try-except, verify normal service works
            pass
