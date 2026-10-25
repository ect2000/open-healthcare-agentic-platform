"""Unit tests for OpenTelemetry configuration and setup."""

from __future__ import annotations

from unittest.mock import patch

from healthcare_agents.observability.config import ObservabilityConfig
from healthcare_agents.observability.instrumentation import (
    extract_w3c_trace_context,
    inject_w3c_trace_headers,
)
from healthcare_agents.observability.metrics import (
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


def test_observability_config_defaults() -> None:
    cfg = ObservabilityConfig.from_env({})
    assert cfg.enabled is True
    assert cfg.service_name == "open-healthcare-api"
    assert cfg.environment == "development"
    assert cfg.exporter_otlp_endpoint == "http://localhost:4318"
    assert cfg.traces_endpoint == "http://localhost:4318/v1/traces"
    assert cfg.metrics_endpoint == "http://localhost:4318/v1/metrics"


def test_observability_config_custom_env() -> None:
    env = {
        "OTEL_ENABLED": "false",
        "OTEL_SERVICE_NAME": "test-service",
        "OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=staging",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel:4318",
    }
    cfg = ObservabilityConfig.from_env(env)
    assert cfg.enabled is False
    assert cfg.service_name == "test-service"
    assert cfg.environment == "staging"
    assert cfg.exporter_otlp_endpoint == "http://otel:4318"
    assert cfg.traces_endpoint == "http://otel:4318/v1/traces"


def test_tracing_and_span_creation() -> None:
    shutdown_tracing()
    cfg = ObservabilityConfig.from_env({"OTEL_ENABLED": "true"})
    setup_tracing(config=cfg, sync_export=True)

    tracer = get_tracer("test-tracer")
    assert tracer is not None

    with trace_span("test.operation", attributes={"test.attr": "value"}):
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        assert trace_id is not None
        assert len(trace_id) == 32
        assert span_id is not None
        assert len(span_id) == 16

    shutdown_tracing()


def test_trace_span_exception_recording() -> None:
    shutdown_tracing()
    cfg = ObservabilityConfig.from_env({"OTEL_ENABLED": "true"})
    setup_tracing(config=cfg, sync_export=True)

    try:
        with trace_span("failing.operation"):
            raise ValueError("Controlled test error")
    except ValueError:
        pass

    shutdown_tracing()


def test_w3c_trace_headers_propagation() -> None:
    shutdown_tracing()
    cfg = ObservabilityConfig.from_env({"OTEL_ENABLED": "true"})
    setup_tracing(config=cfg, sync_export=True)

    with trace_span("parent.span"):
        headers = inject_w3c_trace_headers({})
        assert "traceparent" in headers

        ctx = extract_w3c_trace_context(headers)
        assert ctx is not None

    shutdown_tracing()


def test_metrics_initialization_and_recording() -> None:
    shutdown_metrics()
    cfg = ObservabilityConfig.from_env({"OTEL_ENABLED": "false"})
    m = setup_metrics(config=cfg)
    assert m is not None

    # Safe records should not fail even if disabled
    safe_record_retrieval(
        source="nppes",
        duration_s=0.15,
        status="completed",
        retrieved=5,
    )
    safe_record_retrieval(
        source="pubmed",
        duration_s=0.25,
        status="failed",
        retrieved=0,
        error_type="TimeoutError",
    )
    safe_record_retrieval(
        source="medlineplus",
        duration_s=0.10,
        status="timeout",
        retrieved=0,
    )
    safe_record_evidence_counts(
        source="nppes",
        retrieved=10,
        retained=8,
        excluded=2,
        deduplicated=1,
    )
    shutdown_metrics()


def test_safe_metric_recording_handles_exceptions() -> None:
    with patch(
        "healthcare_agents.observability.metrics.get_metrics",
        side_effect=RuntimeError("Collector down"),
    ):
        # Should not raise any exception
        safe_record_retrieval(source="nppes", duration_s=0.1, status="completed", retrieved=1)
        safe_record_evidence_counts(
            source="nppes", retrieved=1, retained=1, excluded=0, deduplicated=0
        )
