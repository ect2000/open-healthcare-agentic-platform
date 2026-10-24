"""Tests for CLI model status and model chat subcommands."""

from unittest.mock import MagicMock, patch

import pytest

from healthcare_agents.cli import handle_model_chat, handle_model_status, main
from healthcare_agents.models import (
    CompletionUsage,
    ModelInferenceError,
    ModelNotFoundError,
    ModelResponse,
    ModelStreamChunk,
    ModelTimeoutError,
    ModelUnavailableError,
    OllamaAdapter,
)


def test_cli_model_status_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model status prints availability when service and model exist."""
    mock_adapter = MagicMock(spec=OllamaAdapter)
    mock_adapter.check_service_health.return_value = True
    mock_adapter.list_models.return_value = ["gemma4:e2b"]

    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        code = handle_model_status()
        assert code == 0
        captured = capsys.readouterr()
        assert "Service Status: reachable" in captured.out
        assert "Model Availability: installed (gemma4:e2b)" in captured.out


def test_cli_model_status_service_unavailable(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model status reports service down."""
    mock_adapter = MagicMock(spec=OllamaAdapter)
    mock_adapter.check_service_health.return_value = False

    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        code = handle_model_status()
        assert code == 1
        captured = capsys.readouterr()
        assert "Ollama service is unavailable" in captured.err


def test_cli_model_status_model_not_installed(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model status reports model missing and suggests pull command."""
    mock_adapter = MagicMock(spec=OllamaAdapter)
    mock_adapter.check_service_health.return_value = True
    mock_adapter.list_models.return_value = ["other-model"]

    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        code = handle_model_status()
        assert code == 1
        captured = capsys.readouterr()
        assert "Model Availability: NOT installed" in captured.err
        assert "ollama pull gemma4:e2b" in captured.err


def test_cli_model_chat_sync(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model chat outputs response content."""
    mock_adapter = MagicMock()
    mock_adapter.generate.return_value = ModelResponse(
        content="NPPES explanation",
        model="gemma4:e2b",
        usage=CompletionUsage(total_tokens=15),
    )

    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        code = main(["model", "chat", "--prompt", "Explain NPPES"])
        assert code == 0
        captured = capsys.readouterr()
        assert "NPPES explanation" in captured.out


def test_cli_model_chat_stream(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model chat --stream prints streamed tokens."""
    mock_adapter = MagicMock()
    mock_adapter.generate_stream.return_value = iter(
        [
            ModelStreamChunk(content="NPPES ", model="gemma4:e2b", done=False),
            ModelStreamChunk(content="registry.", model="gemma4:e2b", done=True),
        ]
    )

    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        code = main(["model", "chat", "--prompt", "Explain NPPES", "--stream"])
        assert code == 0
        captured = capsys.readouterr()
        assert "NPPES registry." in captured.out


def test_cli_model_chat_errors(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify model chat error handling for unavailable, missing, timeout, and general errors."""
    mock_adapter = MagicMock()

    # Unavailable
    mock_adapter.generate.side_effect = ModelUnavailableError("connection error")
    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        assert handle_model_chat(prompt="hi") == 1
        assert "Connection Error" in capsys.readouterr().err

    # Not found
    mock_adapter.generate.side_effect = ModelNotFoundError("model missing")
    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        assert handle_model_chat(prompt="hi") == 1
        assert "Model Not Found" in capsys.readouterr().err

    # Timeout
    mock_adapter.generate.side_effect = ModelTimeoutError("timed out")
    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        assert handle_model_chat(prompt="hi") == 1
        assert "Timeout Error" in capsys.readouterr().err

    # Generic ModelError
    mock_adapter.generate.side_effect = ModelInferenceError("backend broke")
    with patch("healthcare_agents.cli.get_model_adapter", return_value=mock_adapter):
        assert handle_model_chat(prompt="hi") == 1
        assert "Model Inference Error" in capsys.readouterr().err
