"""OpenTelemetry instrumentation helpers for FastAPI, HTTP clients, and W3C context."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from healthcare_agents.observability.config import ObservabilityConfig, get_observability_config
from healthcare_agents.observability.metrics import setup_metrics
from healthcare_agents.observability.tracing import setup_tracing

logger = logging.getLogger(__name__)

_FASTAPI_INSTRUMENTED = False


def instrument_fastapi(app: FastAPI, config: ObservabilityConfig | None = None) -> None:
    """Instrument a FastAPI application with OpenTelemetry tracing and middleware."""
    global _FASTAPI_INSTRUMENTED
    if _FASTAPI_INSTRUMENTED:
        return

    cfg = config or get_observability_config()
    setup_tracing(cfg)
    setup_metrics(cfg)

    if not cfg.enabled:
        _FASTAPI_INSTRUMENTED = True
        return

    try:
        # Instrument FastAPI app
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,ready,metrics,docs,redoc,openapi.json",
        )
        _FASTAPI_INSTRUMENTED = True
        logger.info("FastAPI successfully instrumented with OpenTelemetry.")
    except Exception as exc:
        logger.warning("Failed to instrument FastAPI: %s", exc)


def inject_w3c_trace_headers(carrier: dict[str, str] | None = None) -> dict[str, str]:
    """Inject W3C traceparent and tracestate headers into an HTTP headers dictionary."""
    headers = {} if carrier is None else carrier
    try:
        TraceContextTextMapPropagator().inject(headers)
    except Exception as exc:
        logger.debug("Failed to inject W3C trace headers: %s", exc)
    return headers


def extract_w3c_trace_context(carrier: dict[str, Any]) -> Any:
    """Extract W3C trace context from incoming request headers."""
    try:
        # Convert all header keys to lowercase strings for case-insensitive lookup
        header_map = {str(k).lower(): str(v) for k, v in carrier.items()}
        return TraceContextTextMapPropagator().extract(carrier=header_map)
    except Exception as exc:
        logger.debug("Failed to extract W3C trace context: %s", exc)
        return trace.get_current_span().get_span_context()
