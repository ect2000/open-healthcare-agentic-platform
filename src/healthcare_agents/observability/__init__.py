"""Centralized observability exports for Open Healthcare Agentic Platform."""

from __future__ import annotations

from healthcare_agents.observability.config import ObservabilityConfig, get_observability_config
from healthcare_agents.observability.instrumentation import (
    extract_w3c_trace_context,
    inject_w3c_trace_headers,
    instrument_fastapi,
)
from healthcare_agents.observability.metrics import (
    HealthcareMetrics,
    get_metrics,
    safe_record_evidence_counts,
    safe_record_retrieval,
    setup_metrics,
    shutdown_metrics,
)
from healthcare_agents.observability.tracing import (
    get_current_span_id,
    get_current_trace_id,
    get_tracer,
    setup_tracing,
    shutdown_tracing,
    trace_span,
)

__all__ = [
    "HealthcareMetrics",
    "ObservabilityConfig",
    "extract_w3c_trace_context",
    "get_current_span_id",
    "get_current_trace_id",
    "get_metrics",
    "get_observability_config",
    "get_tracer",
    "inject_w3c_trace_headers",
    "instrument_fastapi",
    "safe_record_evidence_counts",
    "safe_record_retrieval",
    "setup_metrics",
    "setup_tracing",
    "shutdown_metrics",
    "shutdown_tracing",
    "trace_span",
]
