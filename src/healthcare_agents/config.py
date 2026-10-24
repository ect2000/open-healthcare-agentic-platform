"""Configuration module for the healthcare agentic platform.

Reads configuration from environment variables with safe defaults.
Does not establish network connections or load heavy dependencies.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_VALID_ENVIRONMENTS = {"development", "staging", "production", "test"}
_VALID_MODEL_PROVIDERS = {"ollama", "vllm"}
_VALID_RETRIEVAL_MODES = {"live", "fixture"}


class ConfigurationError(ValueError):
    """Raised when configuration parameters are invalid."""


@dataclass(frozen=True)
class Settings:
    """Immutable application settings resolved from environment variables."""

    app_name: str
    environment: str
    log_level: str
    model_provider: str
    model_name: str
    ollama_base_url: str
    model_timeout_seconds: float
    retrieval_mode: str
    nppes_api_url: str
    nppes_timeout_seconds: float
    nppes_max_retries: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Create Settings instance from environment mapping or os.environ.

        Raises:
            ConfigurationError: If any setting has an invalid value.
        """
        source = os.environ if env is None else env

        raw_app_name = source.get("HEALTHCARE_AGENTS_APP_NAME", "open-healthcare-agentic-platform")
        app_name = raw_app_name.strip()
        if not app_name:
            raise ConfigurationError("HEALTHCARE_AGENTS_APP_NAME must not be empty.")

        environment = source.get("HEALTHCARE_AGENTS_ENV", "development").strip().lower()
        if environment not in _VALID_ENVIRONMENTS:
            raise ConfigurationError(
                f"Invalid HEALTHCARE_AGENTS_ENV '{environment}'. Expected one of: "
                f"{', '.join(sorted(_VALID_ENVIRONMENTS))}."
            )

        log_level = source.get("HEALTHCARE_AGENTS_LOG_LEVEL", "INFO").strip().upper()
        if log_level not in _VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"Invalid HEALTHCARE_AGENTS_LOG_LEVEL '{log_level}'. Expected one of: "
                f"{', '.join(sorted(_VALID_LOG_LEVELS))}."
            )

        model_provider = source.get("MODEL_PROVIDER", "ollama").strip().lower()
        if model_provider not in _VALID_MODEL_PROVIDERS:
            raise ConfigurationError(
                f"Invalid MODEL_PROVIDER '{model_provider}'. Expected one of: "
                f"{', '.join(sorted(_VALID_MODEL_PROVIDERS))}."
            )

        model_name = source.get("MODEL_NAME", "gemma4:e2b").strip()
        if not model_name:
            raise ConfigurationError("MODEL_NAME must not be empty.")

        ollama_base_url = source.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        if not ollama_base_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"Invalid OLLAMA_BASE_URL '{ollama_base_url}'. Must begin with http:// or https://."
            )

        raw_timeout = source.get("MODEL_TIMEOUT_SECONDS", "120")
        try:
            model_timeout_seconds = float(raw_timeout)
            if model_timeout_seconds <= 0:
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                f"Invalid MODEL_TIMEOUT_SECONDS '{raw_timeout}'. Must be a positive number."
            ) from None

        retrieval_mode = source.get("RETRIEVAL_MODE", "live").strip().lower()
        if retrieval_mode not in _VALID_RETRIEVAL_MODES:
            raise ConfigurationError(
                f"Invalid RETRIEVAL_MODE '{retrieval_mode}'. Expected one of: "
                f"{', '.join(sorted(_VALID_RETRIEVAL_MODES))}."
            )

        nppes_api_url = source.get("NPPES_API_URL", "https://npiregistry.cms.hhs.gov/api/").strip()
        if not nppes_api_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"Invalid NPPES_API_URL '{nppes_api_url}'. Must begin with http:// or https://."
            )

        raw_nppes_timeout = source.get("NPPES_TIMEOUT_SECONDS", "10")
        try:
            nppes_timeout_seconds = float(raw_nppes_timeout)
            if nppes_timeout_seconds <= 0:
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                f"Invalid NPPES_TIMEOUT_SECONDS '{raw_nppes_timeout}'. Must be a positive number."
            ) from None

        raw_nppes_retries = source.get("NPPES_MAX_RETRIES", "2")
        try:
            nppes_max_retries = int(raw_nppes_retries)
            if nppes_max_retries < 0:
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                f"Invalid NPPES_MAX_RETRIES '{raw_nppes_retries}'. Must be a non-negative integer."
            ) from None

        return cls(
            app_name=app_name,
            environment=environment,
            log_level=log_level,
            model_provider=model_provider,
            model_name=model_name,
            ollama_base_url=ollama_base_url,
            model_timeout_seconds=model_timeout_seconds,
            retrieval_mode=retrieval_mode,
            nppes_api_url=nppes_api_url,
            nppes_timeout_seconds=nppes_timeout_seconds,
            nppes_max_retries=nppes_max_retries,
        )


def get_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Convenience getter returning resolved Settings."""
    return Settings.from_env(env=env)
