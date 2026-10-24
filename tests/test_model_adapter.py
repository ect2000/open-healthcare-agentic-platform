"""Offline unit tests for the model adapter and schemas."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.models import (
    CompletionUsage,
    Message,
    ModelInferenceError,
    ModelNotFoundError,
    ModelResponse,
    ModelStreamChunk,
    ModelTimeoutError,
    ModelUnavailableError,
    OllamaAdapter,
    get_model_adapter,
)


def test_schemas_instantiation() -> None:
    """Verify dataclasses construct cleanly."""
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"

    usage = CompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30

    res = ModelResponse(content="answer", model="gemma4:e2b", usage=usage)
    assert res.content == "answer"
    assert res.model == "gemma4:e2b"

    chunk = ModelStreamChunk(content="chunk", model="gemma4:e2b", done=False)
    assert chunk.content == "chunk"
    assert not chunk.done


def test_get_model_adapter_factory() -> None:
    """Verify factory initializes OllamaAdapter and rejects unknown providers."""
    adapter = get_model_adapter(
        provider="ollama",
        base_url="http://localhost:11434",
        model_name="gemma4:e2b",
    )
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model_name == "gemma4:e2b"

    with pytest.raises(ValueError, match="Unsupported model provider 'unknown'"):
        get_model_adapter(provider="unknown")


def test_ollama_adapter_check_service_health() -> None:
    """Verify service health check succeeds on HTTP 200 and fails on error."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert adapter.check_service_health() is True

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        assert adapter.check_service_health() is False


def test_ollama_adapter_list_models() -> None:
    """Verify model listing parses tags payload correctly."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")

    tags_payload = json.dumps(
        {"models": [{"name": "gemma4:e2b"}, {"name": "other-model:latest"}]}
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = tags_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        models = adapter.list_models()
        assert "gemma4:e2b" in models
        assert "other-model:latest" in models
        assert "other-model" in models
        assert adapter.is_available() is True


def test_ollama_adapter_list_models_unavailable() -> None:
    """Verify list_models raises ModelUnavailableError on network failure."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        with pytest.raises(ModelUnavailableError, match="Cannot connect to Ollama"):
            adapter.list_models()
        assert adapter.is_available() is False


def test_ollama_adapter_generate_success() -> None:
    """Verify synchronous chat completion produces expected ModelResponse and usage."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="gemma4:e2b")

    chat_payload = json.dumps(
        {
            "model": "gemma4:e2b",
            "message": {"role": "assistant", "content": "NPPES is a provider registry."},
            "prompt_eval_count": 12,
            "eval_count": 25,
            "total_duration": 1500000000,
            "eval_duration": 1200000000,
        }
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = chat_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = adapter.generate(
            prompt="Explain what NPPES is.",
            system_instruction="Be concise.",
            temperature=0.2,
        )
        assert res.content == "NPPES is a provider registry."
        assert res.model == "gemma4:e2b"
        assert res.usage.prompt_tokens == 12
        assert res.usage.completion_tokens == 25
        assert res.usage.total_tokens == 37
        assert res.usage.total_duration_ms == 1500.0
        assert res.usage.eval_duration_ms == 1200.0


def test_ollama_adapter_generate_model_not_found() -> None:
    """Verify HTTP 404 raises ModelNotFoundError."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="missing:model")

    err = urllib.error.HTTPError(
        url="http://localhost:11434/api/chat",
        code=404,
        msg="Not Found",
        hdrs=MagicMock(),
        fp=io.BytesIO(b'{"error":"model not found"}'),
    )

    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(ModelNotFoundError, match="Run `ollama pull missing:model`"):
            adapter.generate(prompt="hello")


def test_ollama_adapter_generate_timeout() -> None:
    """Verify timeout triggers ModelTimeoutError."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", timeout_seconds=1.0)

    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        with pytest.raises(ModelTimeoutError, match=r"timed out after 1\.0 seconds"):
            adapter.generate(prompt="hello")


def test_ollama_adapter_generate_malformed_json() -> None:
    """Verify bad JSON triggers ModelInferenceError."""
    adapter = OllamaAdapter(base_url="http://localhost:11434")

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"invalid json"
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(ModelInferenceError, match="Malformed JSON"):
            adapter.generate(prompt="hello")


def test_ollama_adapter_generate_stream() -> None:
    """Verify streaming chunks are yielded incrementally with final token counts."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="gemma4:e2b")

    lines = [
        json.dumps(
            {
                "model": "gemma4:e2b",
                "message": {"role": "assistant", "content": "Hello "},
                "done": False,
            }
        ).encode("utf-8")
        + b"\n",
        json.dumps(
            {
                "model": "gemma4:e2b",
                "message": {"role": "assistant", "content": "world!"},
                "done": True,
                "prompt_eval_count": 5,
                "eval_count": 8,
                "total_duration": 900000000,
                "eval_duration": 700000000,
            }
        ).encode("utf-8")
        + b"\n",
    ]

    mock_resp = MagicMock()
    mock_resp.__iter__.return_value = iter(lines)
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        chunks = list(adapter.generate_stream(prompt="Hi"))
        assert len(chunks) == 2
        assert chunks[0].content == "Hello "
        assert chunks[0].done is False
        assert chunks[1].content == "world!"
        assert chunks[1].done is True
        assert chunks[1].usage is not None
        assert chunks[1].usage.total_tokens == 13
