# Milestone M8: Implementation Details

## Central Observability Architecture

Milestone M8 adds a unified, vendor-neutral observability subsystem to the platform located under `src/healthcare_agents/observability/`:

```
src/healthcare_agents/observability/
├── __init__.py          # Public exports (config, tracer, metrics, instrumenters)
├── config.py            # Environment-driven ObservabilityConfig
├── tracing.py           # TracerProvider, OTLP HTTP span exporter, trace_span context manager
├── metrics.py           # MeterProvider, OTLP metric exporter, HealthcareMetrics container
└── instrumentation.py   # FastAPI instrumentation, W3C traceparent injection/extraction
```

### 1. Core Modules

#### `config.py`
Defines `ObservabilityConfig` reading from environment variables:
- `OTEL_SERVICE_NAME` (`open-healthcare-api` by default)
- `OTEL_EXPORTER_OTLP_ENDPOINT` (`http://localhost:4318` by default)
- `OTEL_RESOURCE_ATTRIBUTES` (`deployment.environment=local`)
- `OTEL_TRACES_ENABLED` and `OTEL_METRICS_ENABLED` flags

#### `tracing.py`
- Sets up an OpenTelemetry `TracerProvider` with `BatchSpanProcessor` and `OTLPSpanExporter` targeting `/v1/traces`.
- Provides `trace_span(name, attributes)` context manager that gracefully creates spans, attaches safe attributes, catches exceptions to set span error status, and ensures execution never fails if tracing is misconfigured or the collector is unreachable.
- Helper functions `get_current_trace_id()` and `get_current_span_id()` for formatting standard 32-character hex trace identifiers.

#### `metrics.py`
- Sets up a `MeterProvider` with `PeriodicExportingMetricReader` and `OTLPMetricExporter` targeting `/v1/metrics`.
- Defines `HealthcareMetrics` container registering Prometheus-compatible instruments:
  - `healthcare_search_requests_total` (Counter)
  - `healthcare_search_duration_seconds` (Histogram)
  - `healthcare_stage_duration_seconds` (Histogram, labeled by stage and status)
  - `healthcare_retrieval_requests_total` (Counter, labeled by source and status)
  - `healthcare_retrieval_duration_seconds` (Histogram, labeled by source)
  - `healthcare_retrieval_fallback_total` (Counter, labeled by source and outcome)
  - `healthcare_evidence_retrieved_total` (Counter, labeled by source)
  - `healthcare_evidence_retained_total` (Counter, labeled by source)
  - `healthcare_evidence_excluded_total` (Counter, labeled by source)
  - `healthcare_evidence_deduplicated_total` (Counter, labeled by source)
  - `healthcare_inference_requests_total` (Counter, labeled by model and status)
  - `healthcare_inference_duration_seconds` (Histogram, labeled by model)
  - `healthcare_inference_tokens_total` (Counter, labeled by model and token_type: `prompt` / `completion`)

#### `instrumentation.py`
- `instrument_fastapi(app)`: Wraps FastAPI routes with OpenTelemetry middleware for W3C context propagation and HTTP-level telemetry without double-instrumentation.
- `inject_w3c_trace_headers(headers)`: Injects current trace context into outbound client HTTP headers.
- `extract_w3c_trace_context(headers)`: Extracts incoming W3C trace context for distributed context continuity.

---

### 2. Application & Workflow Instrumentation

#### FastAPI Integration (`src/healthcare_agents/api/`)
- Lifespan handler in `app.py` initializes providers on startup and executes flush/shutdown on teardown.
- `service.py`: Wrapped `execute_search()` in root trace span `healthcare.search`, recording overall request duration and setting `trace_id` and `span_id` on the response schema.
- Added `trace_id` and `span_id` attributes to `SearchResponse` schema.

#### LangGraph Agent Workflow (`src/healthcare_agents/workflows/healthcare_graph.py`)
- Instrumented workflow stages with discrete trace spans:
  - `agent.planner`
  - `agent.query_fanout`
  - `agent.parallel_retrieval`
  - `agent.evidence_processor`
  - `agent.deterministic_validator`
  - `agent.grounded_synthesis`
- Recorded execution durations in `healthcare_stage_duration_seconds`.
- Set safe span attributes: stage name, evidence item counts, status. Raw prompts and PHI are strictly excluded.

#### Parallel Retrieval Engine (`src/healthcare_agents/retrieval/parallel_retriever.py`)
- Independent retrievers dispatch concurrently in `ThreadPoolExecutor` under dedicated child spans:
  - `retrieval.nppes`
  - `retrieval.pubmed`
  - `retrieval.medlineplus`
  - `retrieval.cms` (dependent phase)
- Records per-source duration, success, timeout, failure, and MedlinePlus fallback activity in `healthcare_retrieval_*` metrics.

#### Evidence Processor (`src/healthcare_agents/agents/evidence_processor.py`)
- Increments `healthcare_evidence_retrieved_total`, `healthcare_evidence_retained_total`, `healthcare_evidence_excluded_total`, and `healthcare_evidence_deduplicated_total` labeled by source.
- Avoids UI re-render inflation by executing only during evidence pipeline processing.

#### Ollama / Gemma 4 Adapter (`src/healthcare_agents/models/ollama_adapter.py`)
- Wraps LLM calls in `model.inference` trace span.
- Records real token counts (`prompt_eval_count`, `eval_count`) from Ollama response metadata into `healthcare_inference_tokens_total`.
- Measures inference duration in `healthcare_inference_duration_seconds`.
- Zero prompt text, completion text, or synthetic token metrics are emitted.

#### Streamlit UI Trace Correlation (`src/healthcare_agents/ui/`)
- `api_client.py`: Propagates W3C `traceparent` headers on API requests.
- `components.py`: Renders a dedicated "🔗 Trace Details" card displaying the 32-character hexadecimal trace ID and an interactive link directly to the Grafana Tempo trace exploration view.

---

### 3. Docker Observability Infrastructure

Configured under `observability/`:
- **OpenTelemetry Collector** (`observability/otel-collector/config.yaml`):
  - Receives OTLP HTTP (`4318`) and gRPC (`4317`).
  - Exports traces directly to Grafana Tempo via OTLP (`tempo:4317`).
  - Exports metrics via Prometheus exporter endpoint on port `8889`.
- **Prometheus** (`observability/prometheus/prometheus.yml`):
  - Scrapes OTel Collector at `otel-collector:8889` every 5 seconds.
  - Exposes query interface and Prometheus web UI at port `9090`.
- **Grafana Tempo** (`observability/tempo/tempo.yaml`):
  - Ingests traces via OTLP gRPC/HTTP.
  - Stores trace blocks locally in `/tmp/tempo/blocks` with WAL.
  - Serves trace query API on port `3200`.
- **Grafana** (`observability/grafana/`):
  - Auto-provisions Prometheus datasource (`uid: prometheus`) and Tempo datasource (`uid: tempo`).
  - Auto-provisions the 6-section dashboard: **"Open Healthcare Agentic AI — Observability"** (`uid: healthcare-observability`).
  - Runs with anonymous editor access enabled for local inspection on port `3000`.
