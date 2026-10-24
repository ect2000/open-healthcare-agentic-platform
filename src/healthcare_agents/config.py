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

        model_provider = source.get("MODEL_PROVIDER", "ollama").strip()
        model_name = source.get("MODEL_NAME", "gemma:4b").strip()
        ollama_base_url = source.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()

        if not ollama_base_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"Invalid OLLAMA_BASE_URL '{ollama_base_url}'. Must begin with http:// or https://."
            )

        return cls(
            app_name=app_name,
            environment=environment,
            log_level=log_level,
            model_provider=model_provider,
            model_name=model_name,
            ollama_base_url=ollama_base_url,
        )


def get_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Convenience getter returning resolved Settings."""
    return Settings.from_env(env=env)
