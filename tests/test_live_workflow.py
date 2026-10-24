"""Live integration tests for LangGraph multi-agent orchestration with local Gemma 4."""

import os

import pytest

from healthcare_agents.models import OllamaAdapter
from healthcare_agents.workflows import run_healthcare_workflow

LIVE_TEST_ENABLED = os.environ.get("HEALTHCARE_AGENTS_LIVE_TESTS", "0") == "1"


@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Live tests disabled by environment variable")
def test_live_healthcare_langgraph_workflow() -> None:
    """Execute the full LangGraph multi-agent discovery workflow using local Gemma 4."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="gemma4:e2b")
    assert adapter.check_service_health() is True, "Local Ollama is not running"
    assert adapter.is_available() is True, "Model gemma4:e2b is not installed"

    query = "Find pediatric dentists in Houston"
    result = run_healthcare_workflow(query=query, model_adapter=adapter)

    # 1. State integrity
    assert result["request_id"] is not None
    assert result["original_query"] == query

    # 2. Planner agent verification
    plan = result["search_plan"]
    assert plan["city"].lower() == "houston"
    assert "pediatric" in plan["specialty"].lower() or "dentist" in plan["specialty"].lower()
    assert len(plan["evidence_topics"]) > 0

    # 3. Provider & evidence retrieval
    assert len(result["provider_candidates"]) >= 2
    assert len(result["clinical_evidence"]) >= 1

    # 4. Deterministic validation
    validation = result["validation_results"]
    assert validation["is_valid"] is True
    assert validation["duplicate_providers_found"] == 0
    assert validation["provenance_verified"] is True

    # 5. Answer synthesis with Gemma 4
    answer = result["final_answer"]
    assert len(answer) > 100
    assert any(
        cand.name.split()[-1].lower() in answer.lower() for cand in result["provider_candidates"]
    )
    assert "houston" in answer.lower()
    assert len(result["citations"]) >= 2
