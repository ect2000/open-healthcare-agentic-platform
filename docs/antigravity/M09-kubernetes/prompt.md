# Milestone M9: Kubernetes-Native Deployment — Original Instructions

## Project Context
- **Repository:** hastimal/open-healthcare-agentic-platform
- **Milestone:** M9 — Kubernetes-Native Deployment for Healthcare Agents
- **GitHub Issue:** #4
- **Branch:** 4-m9-kubernetes-native-deployment-for-healthcare-agents
- **Base:** main

## Core Objectives
1. Implement a reproducible, vendor-neutral Kubernetes deployment using Kustomize (`deploy/kubernetes/`).
2. Deploy FastAPI, Streamlit, and an in-cluster OpenTelemetry/Prometheus/Tempo/Grafana observability stack.
3. Ensure Kubernetes-deployed applications communicate with the native macOS host Ollama runtime (`gemma4:e2b`).
4. Preserve all completed M1–M8 functionality, including Docker Compose launcher `scripts/run_demo.py` and 6 demo presets.
5. Provide dedicated deployment, smoke testing, and cleanup scripts.
6. Verify quality gates (Ruff, Mypy, pytest >=90% coverage, browser acceptance, screenshot generation).
