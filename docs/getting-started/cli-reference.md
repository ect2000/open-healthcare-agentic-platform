# CLI Reference Guide: `healthcare-agents`

> **Platform:** Open Healthcare Agentic Platform  
> **Package:** `open-healthcare-agentic-platform`  
> **CLI Binary:** `healthcare-agents`  

---

## 1. Overview & General Options

The `healthcare-agents` CLI provides complete management for running preflight diagnostic checks, launching native platform services, executing multi-agent discovery queries from the terminal, inspecting model health, and starting the interactive Streamlit UI.

### Global Options
```bash
healthcare-agents --version
healthcare-agents --help
healthcare-agents [subcommand] --help
```

- `--version`: Displays the installed package version (e.g., `healthcare-agents 0.10.1`).
- `-h, --help`: Displays available subcommands and general usage instructions.
- `--inference-url <URL>`: Overrides the Ollama inference endpoint (default: `http://localhost:11434`).
- `--model <MODEL>`: Overrides the default model (default: `gemma4:e2b`).
- `--no-browser`: Prevents automatic browser launch when starting services.

---

## 2. Command Reference

### `healthcare-agents check`
Validates local prerequisites before launching services. Checks Python runtime version, port availability (API: 8000, UI: 8501), Ollama connectivity, Gemma 4 model installation, and Docker daemon readiness.

```bash
# Basic check
healthcare-agents check

# Check with custom ports
healthcare-agents check --api-port 9000 --ui-port 9501
```
- **Prerequisites:** Python 3.12+. Optional: Ollama running on `localhost:11434`.
- **Expected Output:** Table of checks with `PASS`, `FAIL`, or `WARN` indicators. Returns exit code 0 if critical checks pass.

---

### `healthcare-agents start` (Alias: `run`)
Launches the Open Healthcare Agentic Platform in **Native Local Mode**. Starts both the FastAPI REST backend and the Streamlit frontend in the background with automatic health polling, PID management, and optional browser launch.

```bash
# Start with default ports (API: 8000, UI: 8501)
healthcare-agents start

# Start on custom ports without opening browser
healthcare-agents start --api-port 9000 --ui-port 9501 --no-browser

# Start with custom Ollama endpoint
healthcare-agents start --inference-url http://192.168.1.100:11434 --model gemma4:e2b
```
- **Prerequisites:** Python 3.12, available ports.
- **Expected Output:** Logs confirmation of API and UI startup, PID assignments, readiness status, and URL endpoints (`http://localhost:8501`).

---

### `healthcare-agents stop`
Safely terminates managed native platform service instances running in the background.

```bash
healthcare-agents stop
```
- **Prerequisites:** Running platform services managed by `healthcare-agents start`.
- **Expected Output:** Confirmation of terminated process IDs and freed network ports.

---

### `healthcare-agents status` (Alias: `health`)
Displays configuration status, system environment variables, model provider settings, and live PID status of running background service instances.

```bash
# General status
healthcare-agents status

# Verbose configuration output
healthcare-agents status --verbose
```
- **Expected Output:** Summary of `Status: healthy`, active environment (`development` / `production`), configured model provider, and managed process table.

---

### `healthcare-agents search`
Executes the LangGraph multi-agent discovery workflow directly from the command line. Dispatches planning, query fan-out, parallel retrieval across NPPES, PubMed, CMS, and MedlinePlus, evidence validation, and grounded answer synthesis.

```bash
# Execute query
healthcare-agents search --query "Find pediatric dentists in Houston"

# Execute with verbose stage-by-stage multi-agent progression
healthcare-agents search --query "Find pediatric dentists in Houston" --verbose
```
- **Prerequisites:** Model endpoint (Ollama) or fallback deterministic mode.
- **Expected Output:** Synthesized clinical narrative, retrieved provider records with 10-digit NPIs, PubMed study citations with PMIDs/DOIs, and MedlinePlus consumer health guidance. In `--verbose` mode, prints each stage's timing and execution events.

---

### `healthcare-agents model`
Manages model inference connections and provides command-line conversational access to local Gemma 4 models.

```bash
# Check Ollama connectivity and verify gemma4:e2b installation
healthcare-agents model status

# Interactive command-line chat session with Gemma 4
healthcare-agents model chat --model gemma4:e2b
```
- **Prerequisites:** Ollama service running locally or reachable over the network.
- **Expected Output:** Model status reports latency and installed tags; `chat` opens an interactive prompt.

---

### `healthcare-agents serve`
Launches only the FastAPI REST backend service as a foreground process.

```bash
healthcare-agents serve --host 127.0.0.1 --port 8000
```
- **Endpoints Provided:**
  - `GET /health`: Basic service liveness.
  - `GET /ready`: Full dependency and Ollama model readiness check.
  - `POST /api/v1/search`: LangGraph multi-agent discovery endpoint.
  - `GET /docs`: Interactive Swagger API documentation.

---

### `healthcare-agents ui`
Launches only the Streamlit interactive web frontend as a foreground process.

```bash
healthcare-agents ui --port 8501
```
- **Prerequisites:** FastAPI service running on port 8000 (or custom configured API URL).

---

### `healthcare-agents demo`
Starts an interactive terminal-based demonstration wizard that guides users through preflight checks, local service startup, sample query execution, and browser launch.

```bash
healthcare-agents demo
```
