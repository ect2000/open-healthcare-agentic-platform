"""OpenTelemetry tracing setup and safe span management.

Initializes TracerProvider, OTLP HTTP span exporter, resource attributes,
and provides non-blocking, safe span utilities.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.trace import Span, Status, StatusCode

from healthcare_agents.observability.config import ObservabilityConfig, get_observability_config

logger = logging.getLogger(__name__)

_TRACER_INITIALIZED = False


def setup_tracing(config: ObservabilityConfig | None = None, sync_export: bool = False) -> None:
    """Initialize OpenTelemetry TracerProvider with OTLP HTTP exporter."""
    global _TRACER_INITIALIZED
    if _TRACER_INITIALIZED:
        return

    cfg = config or get_observability_config()
    if not cfg.enabled:
        logger.info("OpenTelemetry tracing is disabled by configuration.")
        _TRACER_INITIALIZED = True
        return

    try:
        resource = Resource.create(
            {
                "service.name": cfg.service_name,
                "service.version": cfg.service_version,
                "deployment.environment": cfg.environment,
            }
        )

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=cfg.traces_endpoint)

        # BatchSpanProcessor is production standard; SimpleSpanProcessor useful for testing
        processor = SimpleSpanProcessor(exporter) if sync_export else BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)
        _TRACER_INITIALIZED = True
        logger.info(
            "OpenTelemetry tracing initialized for '%s' -> %s",
            cfg.service_name,
            cfg.traces_endpoint,
        )
    except Exception as exc:
        logger.warning(
            "Failed to initialize OpenTelemetry tracing: %s. Telemetry will be disabled.",
            exc,
        )
        _TRACER_INITIALIZED = False


def shutdown_tracing() -> None:
    """Flush and shut down active TracerProvider."""
    global _TRACER_INITIALIZED
    try:
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            provider.shutdown()
    except Exception as exc:
        logger.debug("Error shutting down tracer provider: %s", exc)
    finally:
        _TRACER_INITIALIZED = False


def get_tracer(name: str = "open-healthcare") -> trace.Tracer:
    """Return active OpenTelemetry Tracer."""
    return trace.get_tracer(name)


def get_current_trace_id() -> str | None:
    """Return the active 32-character hex trace ID if present, else None."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_current_span_id() -> str | None:
    """Return the active 16-character hex span ID if present, else None."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    tracer_name: str = "open-healthcare",
) -> Generator[Span, None, None]:
    """Safe, non-blocking context manager for creating an OpenTelemetry span.

    Ensures that any OpenTelemetry failure never interrupts business logic.
    """
    tracer = get_tracer(tracer_name)
    safe_attrs = dict(attributes or {})
    span = tracer.start_span(name, attributes=safe_attrs)
    try:
        with trace.use_span(span, end_on_exit=True):
            yield span
    except Exception as exc:
        try:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
        except Exception:
            pass
        raise
