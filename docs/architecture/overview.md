# Platform Architecture Overview

The **Open Healthcare Agentic Platform** is built from the ground up as a vendor-neutral, cloud-native system designed for verifiable healthcare discovery.

```mermaid
graph TB
    subgraph PresentationLayer ["Presentation & Ingestion Layer"]
        StreamlitUI["Streamlit Frontend UI (:8501)"]
        FastAPIGW["FastAPI REST API Gateway (:8000)"]
        CLITool["healthcare-agents CLI Launcher"]
    end

    subgraph AgentCore ["Multi-Agent Execution Engine (LangGraph)"]
        Planner["Planner & Fan-Out Agent"]
        ParallelEngine["Parallel Retrieval Coordinator (Workers: 4)"]
        EvidenceEngine["Evidence Normalization & Provenance Ledger"]
        Validator["Deterministic Clinical Validator"]
        Synthesizer["Answer Synthesis Agent"]
    end

    subgraph ExternalSources ["Authoritative Federal Healthcare Sources"]
        NPPES["NPPES NPI Registry v2.1 (HHS/CMS)"]
        PubMed["PubMed Entrez E-utilities (NCBI/NLM)"]
        CMS["CMS Provider Quality & Star Ratings (CMS.gov)"]
        MedlinePlus["MedlinePlus Health Web Service (NLM/NIH)"]
    end

    subgraph ModelServing ["Local & Cluster Model Intelligence"]
        OllamaLocal["Ollama Service (:11434)<br/>Model: gemma4:e2b"]
        ModelAdapter["Unified Model Adapter Layer"]
    end

    subgraph ObservabilityStack ["OpenTelemetry Observability Subsystem"]
        OTelSDK["OTel Tracing & Metrics SDK (W3C TraceContext)"]
        OTelCol["OTel Collector (:4317/:4318)"]
        Prom["Prometheus TSDB (:9090)"]
        Tempo["Grafana Tempo Tracing (:3200)"]
        Grafana["Grafana Dashboards (:3000)"]
    end

    StreamlitUI --> FastAPIGW
    CLITool --> FastAPIGW
    FastAPIGW --> AgentCore
    
    Planner --> ParallelEngine
    ParallelEngine --> NPPES
    ParallelEngine --> PubMed
    ParallelEngine --> CMS
    ParallelEngine --> MedlinePlus
    
    NPPES --> EvidenceEngine
    PubMed --> EvidenceEngine
    CMS --> EvidenceEngine
    MedlinePlus --> EvidenceEngine
    
    EvidenceEngine --> Validator
    Validator --> Synthesizer
    Synthesizer --> ModelAdapter
    ModelAdapter --> OllamaLocal
    
    AgentCore -.-> OTelSDK
    FastAPIGW -.-> OTelSDK
    OTelSDK --> OTelCol
    OTelCol --> Prom
    OTelCol --> Tempo
    Grafana --> Prom
    Grafana --> Tempo
```

---

## Architectural Principles

1. **Deterministic Grounding First:** Language models are strictly bound to authoritative retrieved evidence. Synthesis cannot invent clinicians, affiliations, or studies.
2. **Authoritative Public Registries:** All provider data originates from CMS NPPES; research literature originates from NCBI PubMed; consumer education originates from NLM MedlinePlus; quality metrics originate from CMS Provider Data.
3. **No Lock-in (Vendor Neutral):** Zero proprietary cloud LLM APIs. Local models (Gemma 4 via Ollama) and standard protocols (OpenTelemetry, OCI, W3C TraceContext) allow complete air-gapped operation.
4. **Cloud-Native by Design:** Packaged with PEP 517 wheels, multi-arch Docker containers (`Dockerfile.api`, `Dockerfile.ui`), Kubernetes Kustomize manifests, and Helm OCI distribution charts.
