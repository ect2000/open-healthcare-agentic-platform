# Milestone M7: Architectural Overview

```mermaid
graph TD
    UserQuery["User Healthcare Query"] --> PlannerNode["🧠 Planner Agent<br/>(Gemma 4 Intent Extraction)"]
    PlannerNode --> FanOut["🔀 Query Fan-Out Planner<br/>(Source-Specific Decompositions)"]
    
    subgraph Parallel_Retrieval ["📡 Concurrent Multi-Source Retrieval Engine"]
        FanOut --> NPPES["🩺 NPPES Registry Client<br/>(Provider Discovery)"]
        FanOut --> PubMed["🔬 PubMed NCBI Client<br/>(Biomedical Literature)"]
        FanOut --> Medline["📖 MedlinePlus Client<br/>(Consumer Education)"]
        NPPES -.->|"Discovered NPIs"| CMS["🏛️ CMS Provider Data<br/>(Quality & Measures)"]
    end
    
    NPPES --> Processor["⚖️ Unified Evidence Processing Layer<br/>(Normalization, Deduplication, Relevance Scoring)"]
    PubMed --> Processor
    Medline --> Processor
    CMS --> Processor
    
    Processor --> Validator["🛡️ Deterministic Validator<br/>(10-Digit NPI & Provenance Integrity)"]
    Validator --> Synthesis["✍️ Answer Synthesis<br/>(Gemma 4 Grounded Generation)"]
    Synthesis --> Presentation["📋 Grounded Summary & Telemetry Dashboard"]

    classDef agent fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
    classDef tool fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef storage fill:#fef3c7,stroke:#f59e0b,stroke-width:2px;
    class PlannerNode,FanOut,Synthesis agent;
    class NPPES,PubMed,Medline,CMS tool;
    class Processor,Validator storage;
```

---

## Architectural Principles

1. **Structured Query Fan-Out**: Single multi-faceted clinical questions (e.g. asking for local pediatric dentists while simultaneously seeking guidance on pediatric dental anxiety) are decomposed into distinct, source-aligned queries with validated parameters.
2. **Bounded Concurrency with Dependency Preservation**:
   - Independent sources (NPPES, PubMed, MedlinePlus) run concurrently via a bounded thread pool (`max_workers=4`).
   - Dependent retrieval (CMS quality lookup for outpatient clinicians) waits until candidate NPIs are extracted from NPPES records.
3. **Transparent Relevance & Explicit Exclusions**:
   - Items lacking topical keywords or addressing unrelated medical conditions (e.g. eating disorders on dental queries) are excluded with recorded justifications.
4. **OTel-Ready Monotonic Telemetry**:
   - Each executed stage and query captures `trace_id`, `span_id`, `parent_span_id`, `query_id`, and `dependency_ids` with monotonic execution duration tracking.
