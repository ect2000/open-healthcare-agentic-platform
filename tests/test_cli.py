"""Tests for healthcare-agents CLI."""

from unittest.mock import patch

import pytest

from healthcare_agents.cli import handle_health, main
from healthcare_agents.config import ConfigurationError


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify --version prints program version and exits with 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "healthcare-agents 0.4.4" in captured.out or "healthcare-agents 0.4.4" in captured.err


def test_cli_health_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify health subcommand outputs health and configuration info."""
    exit_code = main(["health"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Status: healthy" in captured.out
    assert "Environment: development" in captured.out
    assert "Configured Model Provider: ollama" in captured.out


def test_cli_status_alias(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify status is a working alias for health."""
    exit_code = main(["status"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Status: healthy" in captured.out


def test_cli_health_verbose(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify health --verbose prints detailed settings."""
    exit_code = main(["health", "--verbose"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "App Name: open-healthcare-agentic-platform" in captured.out
    assert "Configured Model: gemma4:e2b" in captured.out
    assert "Ollama URL: http://localhost:11434" in captured.out


def test_cli_help_when_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI prints help when no subcommand provided."""
    exit_code = main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "usage: healthcare-agents" in captured.out or "Available subcommands" in captured.out


def test_cli_health_configuration_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify health command handles configuration failure gracefully."""
    with patch("healthcare_agents.cli.get_settings", side_effect=ConfigurationError("bad config")):
        exit_code = handle_health()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Configuration error: bad config" in captured.err
