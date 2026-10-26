# Open Healthcare Agentic Platform Documentation Index

Welcome to the documentation for the **Open Healthcare Agentic Platform**, an open-source, vendor-neutral, evidence-grounded AI platform for healthcare discovery and clinical research.

---

## Documentation Categories

### 🚀 Getting Started
- [Platform Installation & Quick Start](getting-started/installation.md): Installation options via PyPI, `uvx`, Docker Compose, Kubernetes, and Helm.
- [First Healthcare Agent Walkthrough](getting-started/first-demo.md): Step-by-step guide to running your first clinical discovery query and inspecting results.
- [CLI Reference Guide](getting-started/cli-reference.md): Complete reference for the `healthcare-agents` command line interface.

### 🏛️ Architecture & Core Concepts
- [Architecture Overview](architecture/overview.md): System architecture, multi-agent engine, and design principles.
- [Multi-Agent Orchestration](architecture/overview.md#agentcore): LangGraph state graph, planner, parallel fan-out, and synthesis agents.
- [Authoritative Healthcare Sources](architecture/overview.md#externalsources): NPPES NPI Registry, PubMed, CMS Provider Data, and MedlinePlus integration.

### ☸️ Deployment & Cloud-Native
- [Kubernetes & Helm Deployment Guide](deployment/kubernetes.md): Declarative Kustomize manifests, Kind local testing, in-cluster `host-ollama-bridge`, and Helm OCI installation.

### 📊 Observability & Reliability
- [OpenTelemetry Observability Guide](observability/README.md): W3C distributed tracing, Prometheus metrics, Grafana dashboards, and Tempo trace explorer.

### 🛠️ Development & Community
- [Contributor Guide](../CONTRIBUTING.md): Local development workflow, code standards, testing gates, and PR guidelines.
- [Historical Milestones Index](antigravity/README.md): Chronological execution records and verification evidence from M1 through M10.2.
