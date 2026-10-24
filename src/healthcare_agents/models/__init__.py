"""Models package providing interchangeable model adapters."""

from healthcare_agents.models.base import (
    BaseModelAdapter,
    ModelError,
    ModelInferenceError,
    ModelNotFoundError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from healthcare_agents.models.ollama_adapter import OllamaAdapter
from healthcare_agents.models.schemas import (
    CompletionUsage,
    Message,
    ModelResponse,
    ModelStreamChunk,
)


def get_model_adapter(
    provider: str = "ollama",
    base_url: str = "http://localhost:11434",
    model_name: str = "gemma4:e2b",
    timeout_seconds: float = 120.0,
) -> BaseModelAdapter:
    """Factory creating configured model adapter."""
    if provider.lower() == "ollama":
        return OllamaAdapter(
            base_url=base_url,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
        )
    raise ValueError(f"Unsupported model provider '{provider}'. Supported providers: ollama")


__all__ = [
    "BaseModelAdapter",
    "CompletionUsage",
    "Message",
    "ModelError",
    "ModelInferenceError",
    "ModelNotFoundError",
    "ModelResponse",
    "ModelStreamChunk",
    "ModelTimeoutError",
    "ModelUnavailableError",
    "OllamaAdapter",
    "get_model_adapter",
]
