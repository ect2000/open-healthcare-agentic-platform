"""Data schemas and types for model interaction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Message:
    """Chat message representation."""

    role: str
    content: str


@dataclass(frozen=True)
class CompletionUsage:
    """Token and duration metadata for model execution."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    total_duration_ms: float | None = None
    eval_duration_ms: float | None = None


@dataclass(frozen=True)
class ModelResponse:
    """Full generation result from a model."""

    content: str
    model: str
    usage: CompletionUsage = field(default_factory=CompletionUsage)
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelStreamChunk:
    """Incremental chunk produced during streaming generation."""

    content: str
    model: str
    done: bool = False
    usage: CompletionUsage | None = None
