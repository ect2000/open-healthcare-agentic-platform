"""OpenTelemetry application metrics setup and recorded instruments.

Defines standardized Prometheus-compatible instruments for healthcare search,
parallel retrieval, evidence quality metrics, and Gemma 4 model inference.
"""

from __future__ import annotations

import logging

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from healthcare_agents.observability.config import ObservabilityConfig, get_observability_config

logger = logging.getLogger(__name__)

_METER_INITIALIZED = False


class HealthcareMetrics:
    """Central container for application OpenTelemetry metric instruments."""

    def __init__(self, meter: metrics.Meter) -> None:
        self.meter = meter

        # 1. Healthcare Search & Workflow Requests
        self.search_requests_total = meter.create_counter(
            name="healthcare_search_requests_total",
            description="Total number of healthcare search requests processed",
            unit="1",
        )
        self.search_duration_seconds = meter.create_histogram(
            name="healthcare_search_duration_seconds",
            description="End-to-end execution latency for healthcare search workflows",
            unit="s",
        )
        self.search_errors_total = meter.create_counter(
            name="healthcare_search_errors_total",
            description="Total number of failed healthcare search executions",
            unit="1",
        )

        # 2. Agent Workflow Stages
        self.stage_duration_seconds = meter.create_histogram(
            name="healthcare_stage_duration_seconds",
            description="Duration of LangGraph agent workflow stages",
            unit="s",
        )

        # 3. Parallel Retrieval Instruments (bounded labels: nppes, pubmed, medlineplus, cms)
        self.retrieval_requests_total = meter.create_counter(
            name="healthcare_retrieval_requests_total",
            description="Total retrieval queries executed against external sources",
            unit="1",
        )
        self.retrieval_duration_seconds = meter.create_histogram(
            name="healthcare_retrieval_duration_seconds",
            description="Latency of retrieval queries by source",
            unit="s",
        )
        self.retrieval_errors_total = meter.create_counter(
            name="healthcare_retrieval_errors_total",
            description="Total retrieval errors encountered by source",
            unit="1",
        )
        self.retrieval_timeouts_total = meter.create_counter(
            name="healthcare_retrieval_timeouts_total",
            description="Total retrieval timeouts encountered by source",
            unit="1",
        )
        self.retrieval_fallback_total = meter.create_counter(
            name="healthcare_retrieval_fallback_total",
            description="Total fallback queries attempted for zero-hit retrieval",
            unit="1",
        )

        # 4. Evidence Quality Metrics
        self.evidence_retrieved_total = meter.create_counter(
            name="healthcare_evidence_retrieved_total",
            description="Total evidence records retrieved from sources",
            unit="1",
        )
        self.evidence_deduplicated_total = meter.create_counter(
            name="healthcare_evidence_deduplicated_total",
            description="Total duplicate evidence items identified and removed",
            unit="1",
        )
        self.evidence_retained_total = meter.create_counter(
            name="healthcare_evidence_retained_total",
            description="Total verified relevant evidence records retained for clinical grounding",
            unit="1",
        )
        self.evidence_excluded_total = meter.create_counter(
            name="healthcare_evidence_excluded_total",
            description="Total topically irrelevant evidence records excluded",
            unit="1",
        )

        # 5. Model Inference (Gemma 4 via native Ollama)
        self.inference_requests_total = meter.create_counter(
            name="healthcare_inference_requests_total",
            description="Total LLM inference requests dispatched to Ollama",
            unit="1",
        )
        self.inference_duration_seconds = meter.create_histogram(
            name="healthcare_inference_duration_seconds",
            description="Latency of LLM inference requests in seconds",
            unit="s",
        )
        self.inference_errors_total = meter.create_counter(
            name="healthcare_inference_errors_total",
            description="Total LLM inference errors encountered",
            unit="1",
        )
        self.inference_prompt_tokens_total = meter.create_counter(
            name="healthcare_inference_prompt_tokens_total",
            description="Prompt token count as reported by the inference engine",
            unit="1",
        )
        self.inference_completion_tokens_total = meter.create_counter(
            name="healthcare_inference_completion_tokens_total",
            description="Completion token count as reported by the inference engine",
            unit="1",
        )


_METRICS_INSTANCE: HealthcareMetrics | None = None


def setup_metrics(config: ObservabilityConfig | None = None) -> HealthcareMetrics:
    """Initialize MeterProvider with OTLP HTTP metric exporter."""
    global _METER_INITIALIZED, _METRICS_INSTANCE
    if _METRICS_INSTANCE is not None:
        return _METRICS_INSTANCE

    cfg = config or get_observability_config()
    if not cfg.enabled:
        logger.info("OpenTelemetry metrics are disabled by configuration.")
        provider = MeterProvider()
        metrics.set_meter_provider(provider)
        _METRICS_INSTANCE = HealthcareMetrics(provider.get_meter("open-healthcare-metrics"))
        _METER_INITIALIZED = True
        return _METRICS_INSTANCE

    try:
        resource = Resource.create(
            {
                "service.name": cfg.service_name,
                "service.version": cfg.service_version,
                "deployment.environment": cfg.environment,
            }
        )
        exporter = OTLPMetricExporter(endpoint=cfg.metrics_endpoint)
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        _METRICS_INSTANCE = HealthcareMetrics(provider.get_meter("open-healthcare-metrics"))
        _METER_INITIALIZED = True
        logger.info(
            "OpenTelemetry metrics initialized for '%s' -> %s",
            cfg.service_name,
            cfg.metrics_endpoint,
        )
    except Exception as exc:
        logger.warning("Failed to initialize OpenTelemetry metrics: %s. Using fallback.", exc)
        provider = MeterProvider()
        metrics.set_meter_provider(provider)
        _METRICS_INSTANCE = HealthcareMetrics(provider.get_meter("open-healthcare-metrics"))
        _METER_INITIALIZED = False

    return _METRICS_INSTANCE


def get_metrics() -> HealthcareMetrics:
    """Return active HealthcareMetrics instance, initializing if necessary."""
    global _METRICS_INSTANCE
    if _METRICS_INSTANCE is None:
        return setup_metrics()
    return _METRICS_INSTANCE


def shutdown_metrics() -> None:
    """Flush and shut down active MeterProvider."""
    global _METER_INITIALIZED, _METRICS_INSTANCE
    try:
        provider = metrics.get_meter_provider()
        if isinstance(provider, MeterProvider):
            provider.shutdown()
    except Exception as exc:
        logger.debug("Error shutting down meter provider: %s", exc)
    finally:
        _METER_INITIALIZED = False
        _METRICS_INSTANCE = None


# Safe recording helpers to guarantee non-blocking execution
def safe_record_retrieval(
    source: str,
    duration_s: float,
    status: str,
    retrieved: int,
    error_type: str | None = None,
) -> None:
    """Safely record retrieval metrics without raising exceptions."""
    try:
        m = get_metrics()
        source_lbl = source.lower()
        attrs = {"source": source_lbl, "status": status}
        m.retrieval_requests_total.add(1, attrs)
        m.retrieval_duration_seconds.record(duration_s, {"source": source_lbl})
        if status == "failed":
            err_attrs = {"source": source_lbl, "error_type": error_type or "unknown"}
            m.retrieval_errors_total.add(1, err_attrs)
        elif status == "timeout":
            m.retrieval_timeouts_total.add(1, {"source": source_lbl})
        if retrieved > 0:
            m.evidence_retrieved_total.add(retrieved, {"source": source_lbl})
    except Exception as exc:
        logger.debug("Failed to record safe retrieval metric: %s", exc)


def safe_record_evidence_counts(
    source: str,
    retrieved: int,
    retained: int,
    excluded: int,
    deduplicated: int,
) -> None:
    """Safely record evidence quality metrics."""
    try:
        m = get_metrics()
        attrs = {"source": source.lower()}
        if retrieved > 0:
            m.evidence_retrieved_total.add(retrieved, attrs)
        if retained > 0:
            m.evidence_retained_total.add(retained, attrs)
        if excluded > 0:
            m.evidence_excluded_total.add(excluded, attrs)
        if deduplicated > 0:
            m.evidence_deduplicated_total.add(deduplicated, attrs)
    except Exception as exc:
        logger.debug("Failed to record safe evidence metric: %s", exc)
