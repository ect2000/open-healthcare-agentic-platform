# Observability Guide: OpenTelemetry, Prometheus, Tempo & Grafana

The platform includes a complete, production-grade cloud-native observability stack adhering to CNCF standards.

---

## 1. Architecture & Telemetry Pipeline

```mermaid
graph LR
    subgraph Instrumentation ["Instrumented Services"]
        UI["Streamlit Frontend (:8501)"]
        API["FastAPI REST Service (:8000)"]
        Agents["LangGraph Agent Workflow"]
        Ollama["Gemma 4 Inference Client"]
    end

    subgraph OTelCollector ["OpenTelemetry Collector (:4317/:4318)"]
        Receiver["OTLP Receiver (Protobuf / HTTP)"]
        Batch["Batch Processor"]
        ExporterProm["Prometheus Exporter (:8889)"]
        ExporterTempo["OTLP gRPC Exporter (:4317)"]
    end

    subgraph StorageAndViz ["Observability Backends"]
        Prom["Prometheus Server (:9090)"]
        Tempo["Grafana Tempo Tracing (:3200)"]
        Grafana["Grafana Dashboards (:3000)"]
    end

    UI --> API
    API --> Agents
    Agents --> Ollama
    
    UI -. W3C TraceContext .-> OTelCollector
    API -. Spans & Metrics .-> OTelCollector
    Agents -. Spans & Metrics .-> OTelCollector
    Ollama -. Tokens & Latencies .-> OTelCollector
    
    Receiver --> Batch
    Batch --> ExporterProm
    Batch --> ExporterTempo
    
    ExporterProm --> Prom
    ExporterTempo --> Tempo
    
    Grafana --> Prom
    Grafana --> Tempo
```

---

## 2. Ports & Endpoints

| Service | Host Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **Streamlit UI** | `8501` | HTTP | Interactive Web Frontend |
| **FastAPI Backend** | `8000` | HTTP | REST Service API & `/docs` Swagger |
| **Grafana UI** | `3000` | HTTP | Pre-provisioned dashboards (Anonymous viewer enabled) |
| **Prometheus** | `9090` | HTTP | Metrics scraping, TSDB storage & Prometheus Query UI |
| **Grafana Tempo** | `3200` | HTTP | Distributed trace ingestion & Jaeger/Tempo query API |
| **OTel Collector HTTP**| `4318` | HTTP/Protobuf | Ingestion endpoint for application traces and metrics |
| **OTel Collector gRPC**| `4317` | gRPC | Ingestion endpoint for OTLP gRPC telemetry |

---

## 3. Pre-Configured Grafana Dashboard

The dashboard **"Open Healthcare Agentic AI — Observability"** (`uid: healthcare-observability`) contains 6 dedicated sections:

1. **Section 1: Platform Overview & Latency Telemetry**: Total request throughput, error rates, P50/P95/P99 end-to-end latency.
2. **Section 2: LangGraph Agent Workflow Execution**: Per-stage execution duration (Planner, Fan-Out, Parallel Retrieval, Normalization, Synthesis).
3. **Section 3: Parallel Multi-Source Retrieval Metrics**: Throughput, latencies, failure rates, and zero-hit consumer fallback events across NPPES, PubMed, CMS, and MedlinePlus.
4. **Section 4: Evidence Processing & Filtering Quality**: Counts of retrieved, retained, deduplicated, and excluded items.
5. **Section 5: Local Gemma 4 / Ollama Inference Metrics**: Real prompt token count, completion token count, and inference durations.
6. **Section 6: Tempo Distributed Trace Explorer**: Deep-link trace exploration with span graphs and waterfalls.

---

## 4. How to Inspect Live Telemetry

1. **Start Observability Containers:**
   ```bash
   docker compose up -d
   ```
2. **Generate Telemetry:**
   Run a search query in Streamlit (`http://localhost:8501`) or via CLI:
   ```bash
   healthcare-agents search --query "Find cardiologists in Boston"
   ```
3. **Open Grafana:**
   Navigate to `http://localhost:3000/d/healthcare-observability/`.
4. **Follow a Trace in Tempo:**
   Copy the `Trace ID` displayed at the bottom of the Streamlit search results and search for it under Grafana Explore $\rightarrow$ Tempo.
