"""Live integration tests for local Ollama and Gemma 4 inference.

These tests connect directly to a locally running Ollama instance with gemma4:e2b.
They are executed as part of mandatory live milestone verification.
"""

import os

import pytest

from healthcare_agents.models import OllamaAdapter

# Live tests are opt-in so offline test suites and standard CI pass without local Ollama daemon
LIVE_TEST_ENABLED = os.environ.get("HEALTHCARE_AGENTS_LIVE_TESTS", "0") == "1"


@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Live tests disabled by environment variable")
def test_live_ollama_service_and_model_available() -> None:
    """Verify local Ollama service is reachable and gemma4:e2b is installed."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="gemma4:e2b")
    assert adapter.check_service_health() is True, "Local Ollama service is not reachable"
    assert adapter.is_available() is True, "Model gemma4:e2b is not installed on local Ollama"


@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Live tests disabled by environment variable")
def test_live_gemma4_synchronous_inference() -> None:
    """Send real clinical discovery prompt to local gemma4:e2b and verify response & usage."""
    adapter = OllamaAdapter(
        base_url="http://localhost:11434",
        model_name="gemma4:e2b",
        timeout_seconds=120.0,
    )
    prompt = "Explain what NPPES is in one concise sentence."
    response = adapter.generate(
        prompt=prompt,
        system_instruction="You are a clinical assistant. Be concise and precise.",
    )

    assert response.content is not None
    assert len(response.content.strip()) > 0
    content = response.content
    assert any(term in content for term in ("NPPES", "National Plan", "NPI", "Please provide"))
    assert response.usage.prompt_tokens is not None and response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens is not None and response.usage.completion_tokens > 0
    assert response.usage.total_tokens is not None and response.usage.total_tokens > 0


@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Live tests disabled by environment variable")
def test_live_gemma4_streaming_inference() -> None:
    """Stream real inference tokens from local gemma4:e2b and verify stream completion."""
    adapter = OllamaAdapter(
        base_url="http://localhost:11434",
        model_name="gemma4:e2b",
        timeout_seconds=120.0,
    )
    prompt = "Explain PubMed in one concise sentence."
    stream_chunks = list(
        adapter.generate_stream(
            prompt=prompt,
            system_instruction="You are a clinical assistant. Be concise.",
        )
    )

    assert len(stream_chunks) > 1
    assembled_text = "".join(chunk.content for chunk in stream_chunks)
    assert len(assembled_text.strip()) > 0
    keywords = ("PubMed", "biomedical", "database", "citations", "literature")
    assert any(kw.lower() in assembled_text.lower() for kw in keywords)

    # Last chunk must declare done=True and include token usage
    final_chunk = stream_chunks[-1]
    assert final_chunk.done is True
    assert final_chunk.usage is not None
    assert (
        final_chunk.usage.completion_tokens is not None and final_chunk.usage.completion_tokens > 0
    )
