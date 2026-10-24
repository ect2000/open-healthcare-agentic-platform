"""Tests for configuration parsing, defaults, and overrides."""

import pytest

from healthcare_agents.config import ConfigurationError, Settings, get_settings


def test_settings_default_values() -> None:
    """Verify default values when no environment variables are set."""
    settings = Settings.from_env({})
    assert settings.app_name == "open-healthcare-agentic-platform"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.model_provider == "ollama"
    assert settings.model_name == "gemma:4b"
    assert settings.ollama_base_url == "http://localhost:11434"


def test_settings_environment_overrides() -> None:
    """Verify custom environment variables override defaults."""
    env = {
        "HEALTHCARE_AGENTS_APP_NAME": "custom-agent-system",
        "HEALTHCARE_AGENTS_ENV": "production",
        "HEALTHCARE_AGENTS_LOG_LEVEL": "warning",
        "MODEL_PROVIDER": "vllm",
        "MODEL_NAME": "custom-gemma:7b",
        "OLLAMA_BASE_URL": "https://ollama.internal:11434",
    }
    settings = Settings.from_env(env)
    assert settings.app_name == "custom-agent-system"
    assert settings.environment == "production"
    assert settings.log_level == "WARNING"
    assert settings.model_provider == "vllm"
    assert settings.model_name == "custom-gemma:7b"
    assert settings.ollama_base_url == "https://ollama.internal:11434"


def test_get_settings_helper() -> None:
    """Verify get_settings passes kwargs to Settings.from_env."""
    settings = get_settings({"HEALTHCARE_AGENTS_ENV": "staging"})
    assert settings.environment == "staging"


def test_settings_empty_app_name_error() -> None:
    """Verify empty app name triggers ConfigurationError."""
    with pytest.raises(ConfigurationError, match="must not be empty"):
        Settings.from_env({"HEALTHCARE_AGENTS_APP_NAME": "  "})


def test_settings_invalid_environment_error() -> None:
    """Verify invalid environment raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid HEALTHCARE_AGENTS_ENV"):
        Settings.from_env({"HEALTHCARE_AGENTS_ENV": "invalid_env"})


def test_settings_invalid_log_level_error() -> None:
    """Verify invalid log level raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid HEALTHCARE_AGENTS_LOG_LEVEL"):
        Settings.from_env({"HEALTHCARE_AGENTS_LOG_LEVEL": "TRACE"})


def test_settings_invalid_url_error() -> None:
    """Verify invalid URL format raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid OLLAMA_BASE_URL"):
        Settings.from_env({"OLLAMA_BASE_URL": "ftp://localhost:11434"})
