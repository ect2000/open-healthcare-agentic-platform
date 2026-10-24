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
    assert settings.model_name == "gemma4:e2b"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.model_timeout_seconds == 120.0


def test_settings_environment_overrides() -> None:
    """Verify custom environment variables override defaults."""
    env = {
        "HEALTHCARE_AGENTS_APP_NAME": "custom-agent-system",
        "HEALTHCARE_AGENTS_ENV": "production",
        "HEALTHCARE_AGENTS_LOG_LEVEL": "warning",
        "MODEL_PROVIDER": "vllm",
        "MODEL_NAME": "custom-gemma:7b",
        "OLLAMA_BASE_URL": "https://ollama.internal:11434",
        "MODEL_TIMEOUT_SECONDS": "60.5",
    }
    settings = Settings.from_env(env)
    assert settings.app_name == "custom-agent-system"
    assert settings.environment == "production"
    assert settings.log_level == "WARNING"
    assert settings.model_provider == "vllm"
    assert settings.model_name == "custom-gemma:7b"
    assert settings.ollama_base_url == "https://ollama.internal:11434"
    assert settings.model_timeout_seconds == 60.5


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


def test_settings_invalid_provider_error() -> None:
    """Verify invalid model provider raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid MODEL_PROVIDER"):
        Settings.from_env({"MODEL_PROVIDER": "cloud-ai"})


def test_settings_empty_model_name_error() -> None:
    """Verify empty model name raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="MODEL_NAME must not be empty"):
        Settings.from_env({"MODEL_NAME": "   "})


def test_settings_invalid_url_error() -> None:
    """Verify invalid URL format raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid OLLAMA_BASE_URL"):
        Settings.from_env({"OLLAMA_BASE_URL": "ftp://localhost:11434"})


def test_settings_invalid_timeout_error() -> None:
    """Verify negative or non-numeric timeout raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid MODEL_TIMEOUT_SECONDS"):
        Settings.from_env({"MODEL_TIMEOUT_SECONDS": "-10"})

    with pytest.raises(ConfigurationError, match="Invalid MODEL_TIMEOUT_SECONDS"):
        Settings.from_env({"MODEL_TIMEOUT_SECONDS": "not_a_number"})


def test_settings_medlineplus_configuration() -> None:
    """Verify MedlinePlus default values and custom overrides."""
    default_settings = Settings.from_env({})
    assert default_settings.medlineplus_api_url == "https://wsearch.nlm.nih.gov/ws/query"
    assert default_settings.medlineplus_connect_url == "https://connect.medlineplus.gov/service"
    assert default_settings.medlineplus_timeout_seconds == 10.0
    assert default_settings.medlineplus_cache_ttl_seconds == 43200.0
    assert default_settings.medlineplus_max_retries == 3

    custom_env = {
        "MEDLINEPLUS_API_URL": "https://custom.nlm.nih.gov/ws",
        "MEDLINEPLUS_CONNECT_URL": "https://custom.connect.nlm.nih.gov/service",
        "MEDLINEPLUS_TIMEOUT_SECONDS": "20.5",
        "MEDLINEPLUS_CACHE_TTL_SECONDS": "86400",
        "MEDLINEPLUS_MAX_RETRIES": "5",
    }
    custom_settings = Settings.from_env(custom_env)
    assert custom_settings.medlineplus_api_url == "https://custom.nlm.nih.gov/ws"
    assert custom_settings.medlineplus_connect_url == "https://custom.connect.nlm.nih.gov/service"
    assert custom_settings.medlineplus_timeout_seconds == 20.5
    assert custom_settings.medlineplus_cache_ttl_seconds == 86400.0
    assert custom_settings.medlineplus_max_retries == 5

    with pytest.raises(ConfigurationError, match="Invalid MEDLINEPLUS_API_URL"):
        Settings.from_env({"MEDLINEPLUS_API_URL": "ftp://bad-url"})

    with pytest.raises(ConfigurationError, match="Invalid MEDLINEPLUS_CONNECT_URL"):
        Settings.from_env({"MEDLINEPLUS_CONNECT_URL": "ftp://bad-url"})

    with pytest.raises(ConfigurationError, match="Invalid MEDLINEPLUS_TIMEOUT_SECONDS"):
        Settings.from_env({"MEDLINEPLUS_TIMEOUT_SECONDS": "-1"})

    with pytest.raises(ConfigurationError, match="Invalid MEDLINEPLUS_CACHE_TTL_SECONDS"):
        Settings.from_env({"MEDLINEPLUS_CACHE_TTL_SECONDS": "abc"})

    with pytest.raises(ConfigurationError, match="Invalid MEDLINEPLUS_MAX_RETRIES"):
        Settings.from_env({"MEDLINEPLUS_MAX_RETRIES": "-2"})
