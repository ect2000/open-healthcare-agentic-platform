"""Tests for CLI healthcare-agents search command."""

from unittest.mock import patch

import pytest

from healthcare_agents.cli import handle_search, main


def test_cli_search_success_basic(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify search command prints expected sections."""
    code = main(["search", "--query", "Find pediatric dentists in Houston"])
    assert code == 0
    captured = capsys.readouterr()
    assert "HEALTHCARE MULTI-AGENT WORKFLOW" in captured.out
    assert "Dr. Jane Smith, DDS" in captured.out
    assert "synthetic test fixtures" in captured.out


def test_cli_search_verbose_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify search command in verbose mode outputs all agent stages."""
    code = main(["search", "--query", "Find pediatric dentists in Houston", "--verbose"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Stage 1: Planner Agent" in captured.out
    assert "Stage 2: Provider Retrieval" in captured.out
    assert "Stage 3: Evidence Retrieval" in captured.out
    assert "Stage 4: Deterministic Validation" in captured.out
    assert "Stage 5: Synthesized Discovery Result" in captured.out
    assert "Citations & Source Provenance" in captured.out


def test_cli_search_workflow_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify search command handles workflow execution errors gracefully."""
    with patch(
        "healthcare_agents.cli.run_healthcare_workflow",
        side_effect=RuntimeError("Graph crashed"),
    ):
        code = handle_search(query="Any query")
        assert code == 1
        captured = capsys.readouterr()
        assert "Workflow execution failure: Graph crashed" in captured.err


def test_cli_search_config_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify search command handles bad configuration."""
    from healthcare_agents.config import ConfigurationError

    with patch(
        "healthcare_agents.cli.get_settings",
        side_effect=ConfigurationError("bad config"),
    ):
        code = handle_search(query="Any query")
        assert code == 1
        captured = capsys.readouterr()
        assert "Configuration error: bad config" in captured.err
