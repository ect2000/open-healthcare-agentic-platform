"""OpenTelemetry and observability configuration for the healthcare agentic platform."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ObservabilityConfig:
    """Configuration parameters for OpenTelemetry tracing and metrics."""

    enabled: bool
    service_name: str
    service_version: str
    environment: str
    exporter_otlp_endpoint: str
    exporter_otlp_protocol: str  # http/protobuf or grpc
    traces_endpoint: str
    metrics_endpoint: str
    grafana_tempo_url: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ObservabilityConfig:
        """Resolve observability settings from environment mapping or os.environ."""
        source = os.environ if env is None else env

        raw_enabled = source.get("OTEL_ENABLED", "true").strip().lower()
        enabled = raw_enabled in ("true", "1", "yes", "on")

        service_name = source.get("OTEL_SERVICE_NAME", "open-healthcare-api").strip()
        from healthcare_agents import __version__

        service_version = source.get("OTEL_SERVICE_VERSION", __version__).strip()

        # Parse resource attributes for environment if provided
        resource_attrs_raw = source.get("OTEL_RESOURCE_ATTRIBUTES", "")
        env_from_resource = ""
        for item in resource_attrs_raw.split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                if k.strip() in ("deployment.environment", "environment"):
                    env_from_resource = v.strip()

        environment = (
            env_from_resource or source.get("HEALTHCARE_AGENTS_ENV", "development").strip().lower()
        )

        base_endpoint = source.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318").rstrip(
            "/"
        )
        protocol = source.get("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf").strip().lower()

        # Endpoints for traces and metrics
        traces_endpoint = source.get(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"{base_endpoint}/v1/traces"
        )
        metrics_endpoint = source.get(
            "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", f"{base_endpoint}/v1/metrics"
        )

        # Tempo URL for trace link correlation in UI (defaults to local Grafana Tempo query URL)
        grafana_tempo_url = source.get("GRAFANA_TEMPO_URL", "http://localhost:3000/explore").strip()

        return cls(
            enabled=enabled,
            service_name=service_name,
            service_version=service_version,
            environment=environment,
            exporter_otlp_endpoint=base_endpoint,
            exporter_otlp_protocol=protocol,
            traces_endpoint=traces_endpoint,
            metrics_endpoint=metrics_endpoint,
            grafana_tempo_url=grafana_tempo_url,
        )


def get_observability_config() -> ObservabilityConfig:
    """Factory helper to fetch active observability configuration."""
    return ObservabilityConfig.from_env()
