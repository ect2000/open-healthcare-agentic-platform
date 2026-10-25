# Milestone M8: Production-Grade Observability (Plan)

## 1. Context & Objectives

Milestone M8 establishes production-grade observability across the Open Healthcare Agentic Platform using standard, vendor-neutral protocols and components:
- **OpenTelemetry Python SDK**: Centralized instrumentation, TracerProvider, MeterProvider, and OTLP Protobuf over HTTP exporters.
- **OpenTelemetry Collector**: Unified telemetry pipeline receiving traces and metrics from application components.
- **Grafana Tempo**: Distributed tracing backend storing trace spans across FastAPI, LangGraph workflow, parallel retrievers, and Ollama/Gemma 4 inference.
- **Prometheus**: Time-series metrics engine scraping application metrics exported via OpenTelemetry Collector.
- **Grafana**: Provisioned multi-panel dashboards visualizing platform health, agent execution latencies, retrieval volumes, evidence filtering metrics, and trace drill-downs.

## 2. Requirements & Architecture

### OpenTelemetry Foundation (`src/healthcare_agents/observability/`)
- Configuration via environment variables:
  - `OTEL_SERVICE_NAME` (default: `open-healthcare-api`)
  - `OTEL_EXPORTER_OTLP_ENDPOINT` (default: `http://localhost:4318`)
  - `OTEL_RESOURCE_ATTRIBUTES` (default: `deployment.environment=local`)
  - `OTEL_METRICS_ENABLED` / `OTEL_TRACES_ENABLED`
- Fail-safe execution: Telemetry failures must never break healthcare search or user experience.
- Graceful shutdown with batch flushes.

### Tracing Instrumentation
- **FastAPI**: W3C TraceContext propagation (`traceparent`), request duration, status code, error counts.
- **LangGraph Multi-Agent Workflow**: Trace spans for `agent.planner`, `agent.query_fanout`, `agent.parallel_retrieval`, `agent.evidence_processor`, `agent.deterministic_validator`, `agent.grounded_synthesis`.
- **Parallel Retrieval Engine**: Spans and duration metrics for independent retrievers (`retrieval.nppes`, `retrieval.pubmed`, `retrieval.medlineplus`) and dependent CMS retrieval (`retrieval.cms`).
- **Gemma 4 / Ollama**: Model inference duration and token metrics (`prompt_eval_count`, `eval_count`) without logging prompt text, response text, or PHI.
- **Streamlit**: Trace context extraction and direct linking to Grafana Tempo traces.

### Docker Compose Observability Stack
- Services:
  - `open-healthcare-api`: FastAPI service instrumented with OTLP HTTP exporter.
  - `open-healthcare-ui`: Streamlit web interface with trace link correlation.
  - `open-healthcare-otel-collector`: Core telemetry routing to Tempo and Prometheus.
  - `open-healthcare-prometheus`: Metrics store and PromQL query engine on port 9090.
  - `open-healthcare-tempo`: Distributed tracing storage and query engine on port 3200.
  - `open-healthcare-grafana`: Dashboard and exploration frontend on port 3000.
  - Native host Ollama connectivity preserved via `host.docker.internal:11434`.

## 3. Implementation Plan

1. **OpenTelemetry Core Package**: Build `config.py`, `tracing.py`, `metrics.py`, `instrumentation.py`.
2. **Workflow & Component Instrumentation**:
   - Wrap FastAPI routes and application lifespan.
   - Instrument LangGraph agent nodes.
   - Instrument parallel retrieval threads in `parallel_retriever.py`.
   - Instrument Ollama adapter in `ollama_adapter.py`.
   - Render trace links in Streamlit `components.py`.
3. **Observability Stack Infrastructure**:
   - Provision OTel Collector, Prometheus, Tempo, and Grafana configurations under `observability/`.
   - Build 6-section Grafana dashboard JSON.
   - Configure Docker Compose with health checks and volume bindings.
4. **Verification & Quality Gates**:
   - Unit and integration tests for metrics and tracing.
   - Controlled failure observability tests (timeouts, API errors, zero results).
   - Automated screenshot capture with Playwright.
   - One-command demonstration script (`scripts/run_demo.py`).
   - Linting, formatting, type checking, and $\ge 90\%$ test coverage.
