"""Base interface protocol and exception hierarchy for model adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence

from healthcare_agents.models.schemas import (
    Message,
    ModelResponse,
    ModelStreamChunk,
)


class ModelError(Exception):
    """Base exception for all model and inference failures."""


class ModelUnavailableError(ModelError):
    """Raised when the model backend or service cannot be reached."""


class ModelNotFoundError(ModelError):
    """Raised when the specified model is not installed or available on the server."""


class ModelTimeoutError(ModelError):
    """Raised when a request exceeds the configured timeout."""


class ModelInferenceError(ModelError):
    """Raised when model inference execution fails."""


class BaseModelAdapter(ABC):
    """Abstract interface defining the contract for model adapters.

    Future adapters (e.g. vLLM, mock) must implement this interface.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the model provider service and target model are available."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        messages: Sequence[Message] | None = None,
        temperature: float | None = None,
    ) -> ModelResponse:
        """Synchronously generate a full response."""

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        messages: Sequence[Message] | None = None,
        temperature: float | None = None,
    ) -> Iterator[ModelStreamChunk]:
        """Stream response chunks incrementally."""
