# Milestone M8: Observability Demonstration & Operations Guide

## Overview

Milestone M8 equips the platform with production-grade distributed tracing and telemetry. The full observability architecture is orchestrated via Docker Compose alongside the FastAPI application and Streamlit UI, communicating with the native host Ollama instance for local LLM inference.

```
                          ┌────────────────────────┐
                          │   Streamlit Web UI     │ (Port 8501)
                          └───────────┬────────────┘
                                      │ HTTP (W3C traceparent)
                                      ▼
                          ┌────────────────────────┐
                          │   FastAPI Service      │ (Port 8000)
                          └───────────┬────────────┘
                                      │ OTLP HTTP (4318)
                                      ▼
                          ┌────────────────────────┐
                          │ OpenTelemetry Collector│
                          └─────┬────────────┬─────┘
                     OTLP gRPC  │            │ Prometheus Exporter
                        (4317)  │            │ (8889)
                                ▼            ▼
┌──────────────────┐      ┌───────────┐  ┌───────────┐
│ Native macOS     │      │  Grafana  │  │Prometheus │ (Port 9090)
│ Ollama Instance  │      │   Tempo   │  └─────┬─────┘
│ (gemma4:e2b)     │      │(Port 3200)│        │ Scrapes
└──────────────────┘      └─────┬─────┘        │
                                │              │
                                ▼              ▼
                          ┌────────────────────────┐
                          │   Grafana Dashboards   │ (Port 3000)
                          └────────────────────────┘
```

---

## Service Endpoints & Ports

| Service | Local URL | Port | Purpose |
| :--- | :--- | :--- | :--- |
| **Streamlit UI** | [http://localhost:8501](http://localhost:8501) | `8501` | Interactive search UI & trace correlation |
| **FastAPI REST API** | [http://localhost:8000](http://localhost:8000) | `8000` | OpenAPI search & health endpoints |
| **Grafana** | [http://localhost:3000](http://localhost:3000) | `3000` | Provisioned dashboards & Tempo trace explorer |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | `9090` | Time-series metrics engine & PromQL |
| **Grafana Tempo** | [http://localhost:3200](http://localhost:3200) | `3200` | Distributed trace ingestion & query engine |
| **OTel Collector HTTP**| `http://localhost:4318` | `4318` | OTLP Protobuf HTTP endpoint |
| **OTel Collector gRPC**| `http://localhost:4317` | `4317` | OTLP Protobuf gRPC endpoint |
| **Native Ollama** | `http://localhost:11434` | `11434`| Native macOS LLM serving (`gemma4:e2b`) |

---

## One-Command Launcher

Run the automated launcher to verify prerequisites, check native Ollama connectivity, boot the Docker Compose stack, verify endpoints, open Streamlit in the browser, and print connection links:

```bash
uv run python scripts/run_demo.py
```
*(Pass `--no-browser` to prevent automatic browser launch).*

### Manual Docker Compose Commands

To start the observability stack:
```bash
docker compose up -d --build
```

To monitor container status and logs:
```bash
docker compose ps
docker compose logs -f otel-collector
```

To stop all containers:
```bash
docker compose down
```

---

## Executing the Demonstration Search

1. Navigate to **Streamlit UI** at [http://localhost:8501](http://localhost:8501).
2. Click **Preset 2**:
   > *"Find the best pediatric dentists in Houston, Texas, and research pediatric dental anxiety."*
3. Click **Execute Search**.
4. Observe the results tabs:
   - **Grounded Response**: Structured provider, clinical research, and patient education summaries.
   - **⚡ Agent Workflow & Query Fan-Out**: Real execution timeline and multi-stage status badges.
   - **🔗 Trace Details Card**: Inspect the generated 32-character Hex Trace ID (e.g. `22a62323cbffcd1c793cf7624706b245`).
   - Click **"View Distributed Trace in Grafana Tempo"** to jump straight into the visual trace timeline.

---

## Inspecting Telemetry in Grafana

1. Open **Grafana** at [http://localhost:3000](http://localhost:3000) (Anonymous access enabled).
2. Go to **Dashboards** $\rightarrow$ **Open Healthcare Agentic AI — Observability** (`uid: healthcare-observability`).
3. Explore the six provisioned monitoring sections:
   - **Section 1: Platform Overview**: Total requests, latency quantiles (P50, P95, P99), error rates.
   - **Section 2: Agent Workflow**: Execution duration breakdown per LangGraph node.
   - **Section 3: Retrieval Performance**: Request counts and latencies for NPPES, PubMed, MedlinePlus, CMS, and MedlinePlus zero-hit fallback activations.
   - **Section 4: Evidence Quality**: Volume of retrieved, retained, deduplicated, and excluded items.
   - **Section 5: Gemma 4 Inference**: Inference latencies and prompt/completion token counts.
   - **Section 6: Distributed Tracing**: Tempo trace query table and drill-down links.

---

## Automated Screenshot Generation

To capture updated screenshots of all dashboard sections, Streamlit trace cards, and Tempo spans:

```bash
uv run python scripts/capture_m8_screenshots.py
```
Screenshots are saved directly to `docs/images/m08_*.png`.
