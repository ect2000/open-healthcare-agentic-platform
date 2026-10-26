# Open Healthcare Agentic Platform

[![PyPI version](https://img.shields.io/pypi/v/open-healthcare-agentic-platform.svg)](https://pypi.org/project/open-healthcare-agentic-platform/)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/LICENSE)

**Vendor-neutral, open-source, evidence-grounded healthcare search and agentic AI platform.**  
Anchors autonomous clinical and patient-oriented discovery to authoritative federal healthcare repositories (NPPES, PubMed, CMS, MedlinePlus) using local models (Gemma 4 via Ollama), LangGraph orchestration, and CNCF-standard OpenTelemetry observability.

---

## ⚡ Quick Start (Zero-Install)

Run the complete platform without cloning repositories or setting up virtual environments:

```bash
# 1. Run local diagnostic checks
uvx --from open-healthcare-agentic-platform healthcare-agents check

# 2. Launch the platform (FastAPI on :8000, Streamlit on :8501)
uvx --from open-healthcare-agentic-platform healthcare-agents start
```
The CLI automatically launches your default browser to `http://localhost:8501`.

To stop background services:
```bash
healthcare-agents stop
```

---

## 📦 Installation Options

### Option 1: Install with `pip`
```bash
pip install open-healthcare-agentic-platform
healthcare-agents check
healthcare-agents start
```

### Option 2: Docker Compose
```bash
# Launches FastAPI (:8000), Streamlit (:8501), OTel Collector, Prometheus, Tempo & Grafana
docker compose up -d
```

### Option 3: Kubernetes via Helm OCI
```bash
helm install healthcare oci://ghcr.io/hastimal/charts/open-healthcare \
  --version 0.10.2 \
  --namespace healthcare \
  --create-namespace
```

---

## 🏛️ Core Capabilities

- **4-Way Authoritative Healthcare Retrieval:**
  - **NPPES (CMS):** Provider verification, 10-digit NPIs, medical specialties, practice locations.
  - **PubMed (NCBI Entrez):** Peer-reviewed biomedical research, clinical trials, and PMIDs.
  - **CMS Provider Data:** Clinician MIPS quality scores, facility general info, and hospital star ratings.
  - **MedlinePlus (NLM):** Consumer health education, condition summaries, and patient literacy topics.
- **Evidence Processing & Grounded Synthesis:**
  - Deterministic deduplication, NPI verification, topical guardrails, and cryptographic provenance audit ledger.
  - Local model inference using Gemma 4 via Ollama (zero reliance on closed-source cloud APIs).
- **Production Observability:**
  - Full W3C distributed trace propagation across agents, retrievers, and LLM inference.
  - Pre-provisioned Grafana monitoring dashboards, Prometheus metrics, and Grafana Tempo trace waterfalls.

---

## 🖥️ Command Line Reference

```bash
# Verify version
healthcare-agents --version

# Diagnostics preflight (Python, Ports, Ollama, Gemma 4, Docker)
healthcare-agents check

# Start platform services in background
healthcare-agents start

# Stop managed platform services
healthcare-agents stop

# Execute multi-agent discovery directly in terminal
healthcare-agents search --query "Find pediatric dentists in Houston" --verbose

# Run interactive demonstration wizard
healthcare-agents demo
```

---

## 📖 Complete Documentation & Source Code

- **GitHub Repository:** [https://github.com/hastimal/open-healthcare-agentic-platform](https://github.com/hastimal/open-healthcare-agentic-platform)
- **Documentation Index:** [https://github.com/hastimal/open-healthcare-agentic-platform/tree/main/docs](https://github.com/hastimal/open-healthcare-agentic-platform/tree/main/docs)
- **CLI Reference:** [https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/getting-started/cli-reference.md](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/getting-started/cli-reference.md)
- **Architecture Overview:** [https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/architecture/overview.md](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/architecture/overview.md)
- **Observability Guide:** [https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/observability/README.md](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/docs/observability/README.md)
- **Contributor Guide:** [https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/CONTRIBUTING.md](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/CONTRIBUTING.md)

---

## ⚖️ Non-Clinical / Research Disclaimer

> **IMPORTANT**: This software is designed exclusively for research, education, and informational discovery. It is **NOT** a medical device, diagnostic tool, or clinical decision support system. Always consult a licensed clinician for medical advice.

---

## 📄 License

Licensed under the [Apache License 2.0](https://github.com/hastimal/open-healthcare-agentic-platform/blob/main/LICENSE).
