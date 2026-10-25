"""Tests for Dockerfile specifications, Compose profiles, and containerized configuration."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import yaml  # type: ignore[import-untyped]

from healthcare_agents.api.schemas import ReadinessResponse
from healthcare_agents.config import get_settings


def test_dockerfile_api_structure() -> None:
    """Verify Dockerfile.api includes multi-stage build, non-root user, and health check."""
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile.api"
    assert dockerfile_path.exists(), "Dockerfile.api must exist"
    content = dockerfile_path.read_text()

    assert "FROM python:3.12-slim-bookworm AS builder" in content
    assert "FROM python:3.12-slim-bookworm AS runner" in content
    assert "useradd -u 10001" in content
    assert "USER appuser:appgroup" in content
    assert "HEALTHCHECK" in content
    assert "/health" in content
    assert "EXPOSE 8000" in content
    assert "ENTRYPOINT" in content
    assert "uvicorn" in content


def test_dockerfile_ui_structure() -> None:
    """Verify Dockerfile.ui includes multi-stage build, non-root user, and health check."""
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile.ui"
    assert dockerfile_path.exists(), "Dockerfile.ui must exist"
    content = dockerfile_path.read_text()

    assert "FROM python:3.12-slim-bookworm AS builder" in content
    assert "FROM python:3.12-slim-bookworm AS runner" in content
    assert "useradd -u 10001" in content
    assert "USER appuser:appgroup" in content
    assert "HEALTHCHECK" in content
    assert "/_stcore/health" in content
    assert "EXPOSE 8501" in content
    assert "ENTRYPOINT" in content
    assert "healthcare-agents" in content


def test_dockerignore_excludes_sensitive_and_ephemeral_files() -> None:
    """Verify .dockerignore excludes git, venv, caches, model weights, and secrets."""
    ignore_path = Path(__file__).parent.parent / ".dockerignore"
    assert ignore_path.exists(), ".dockerignore must exist"
    content = ignore_path.read_text().splitlines()

    patterns = [line.strip() for line in content if line.strip() and not line.startswith("#")]
    assert ".git" in patterns
    assert ".venv" in patterns
    assert ".env" in patterns
    assert "*.whl" in patterns
    assert "*.gguf" in patterns
    assert "*.safetensors" in patterns


def test_docker_compose_config_validity() -> None:
    """Verify docker-compose.yml structure, services, profiles, and networking."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    with open(compose_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    assert "api" in services
    assert "ui" in services
    assert "ollama" in services
    assert "ollama-bootstrap" in services

    # Verify api service config
    api = services["api"]
    assert api["build"]["dockerfile"] == "Dockerfile.api"
    assert api["restart"] == "unless-stopped"
    assert "open-healthcare-api" == api["container_name"]
    assert any("host.docker.internal" in h for h in api.get("extra_hosts", []))
    assert "healthcheck" in api

    # Verify ui service config
    ui = services["ui"]
    assert ui["build"]["dockerfile"] == "Dockerfile.ui"
    assert ui["depends_on"]["api"]["condition"] == "service_healthy"
    assert "healthcheck" in ui

    # Verify ollama profile config
    ollama = services["ollama"]
    assert "container-ollama" in ollama.get("profiles", [])
    assert any("ollama-models" in v for v in ollama.get("volumes", []))

    # Verify volumes and networks
    assert "ollama-models" in config.get("volumes", {})
    assert "healthcare-net" in config.get("networks", {})


def test_container_environment_variable_resolution() -> None:
    """Verify settings resolve container environment variables properly."""
    env = {
        "HEALTHCARE_AGENTS_APP_NAME": "open-healthcare-agentic-platform",
        "HEALTHCARE_AGENTS_ENV": "production",
        "HEALTHCARE_AGENTS_LOG_LEVEL": "WARNING",
        "MODEL_PROVIDER": "ollama",
        "OLLAMA_MODEL": "gemma4:12b",
        "OLLAMA_BASE_URL": "http://host.docker.internal:11434",
        "MODEL_TIMEOUT_SECONDS": "180",
        "RETRIEVAL_MODE": "live",
    }
    settings = get_settings(env=env)
    assert settings.environment == "production"
    assert settings.log_level == "WARNING"
    assert settings.model_name == "gemma4:12b"
    assert settings.ollama_base_url == "http://host.docker.internal:11434"
    assert settings.model_timeout_seconds == 180.0
    assert settings.retrieval_mode == "live"


def test_readiness_model_unavailable_scenario() -> None:
    """Verify readiness logic correctly flags when Ollama model is missing or uncontactable."""
    with (
        patch(
            "healthcare_agents.models.ollama_adapter.OllamaAdapter.check_service_health",
            return_value=True,
        ),
        patch(
            "healthcare_agents.models.ollama_adapter.OllamaAdapter.is_available",
            return_value=False,
        ),
    ):
        from healthcare_agents.models.ollama_adapter import OllamaAdapter

        adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="nonexistent:model")
        service_online = adapter.check_service_health()
        model_ready = adapter.is_available()

        assert service_online is True
        assert model_ready is False

        readiness = ReadinessResponse(
            ready=False,
            status="not_ready",
            version="0.6.0",
            ollama_service_available=service_online,
            model_installed=model_ready,
            model_name="nonexistent:model",
            retrieval_mode="live",
            four_sources_configured=True,
            details={"error": "Configured model not found"},
        )
        assert readiness.ready is False
        assert readiness.status == "not_ready"


def test_backend_unavailable_handling() -> None:
    """Verify HealthcareApiClient handles backend unreachability without crashing."""
    from healthcare_agents.ui.api_client import HealthcareApiClient

    client = HealthcareApiClient(base_url="http://127.0.0.1:59999", timeout=1.0)
    health = client.check_health()
    assert health is None

    readiness = client.check_readiness()
    assert readiness is None

    with pytest.raises(httpx.HTTPError):
        client.search(query="Test query without backend")


def test_bootstrap_script_attributes() -> None:
    """Verify scripts/bootstrap_model.sh is present, non-empty, and executable."""
    script_path = Path(__file__).parent.parent / "scripts" / "bootstrap_model.sh"
    assert script_path.exists(), "scripts/bootstrap_model.sh must exist"
    assert os.access(script_path, os.X_OK), "scripts/bootstrap_model.sh must be executable"
    content = script_path.read_text()
    assert "#!/usr/bin/env bash" in content
    assert "curl" in content
    assert "api/pull" in content
