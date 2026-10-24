# Milestone M02: Implementation Details & Architecture

## 1. Overview & Objectives
Milestone M02 introduces self-hosted, local LLM inference powered by **Gemma 4** (`gemma4:e2b`, 7.5 GB) served through **Ollama** (`ollama version is 0.40.10`).

The implementation establishes a clean, extensible model adapter layer that:
- Decouples LLM inference from downstream orchestration frameworks (e.g. LangGraph).
- Supports standard request/response as well as incremental streaming.
- Captures token usage metadata (prompt tokens, eval tokens, durations).
- Provides robust error handling for network drops, timeouts, and missing models.
- Allows seamless future replacement with vLLM or Kubernetes-based serving.

---

## 2. Package Architecture (`src/healthcare_agents/models/`)

```
src/healthcare_agents/models/
├── __init__.py          # Exports adapter classes, factory function get_model_adapter
├── base.py              # BaseModelAdapter abstract protocol and error hierarchy
├── ollama_adapter.py    # Native HTTP adapter for Ollama (/api/chat, /api/tags)
└── schemas.py           # Message, ModelResponse, ModelStreamChunk, CompletionUsage
```

### Components
1. **`schemas.py`**:
   - `Message`: Represents role/content pairs (`system`, `user`, `assistant`).
   - `CompletionUsage`: Captures prompt tokens, completion tokens, total duration, and eval duration in milliseconds.
   - `ModelResponse`: Encapsulates output content, model name, and metadata.
   - `ModelStreamChunk`: Encapsulates incremental text deltas and final execution usage.

2. **`base.py`**:
   - `BaseModelAdapter`: Abstract base class enforcing `is_available()`, `generate()`, and `generate_stream()`.
   - Error hierarchy: `ModelError` -> `ModelUnavailableError`, `ModelNotFoundError`, `ModelTimeoutError`, `ModelInferenceError`.

3. **`ollama_adapter.py`**:
   - Native `urllib.request` implementation using Ollama's `/api/chat` and `/api/tags` endpoints.
   - Handles timeout propagation, streaming NDJSON line parsing, HTTP errors (mapping 404 to `ModelNotFoundError`), and connection refusals.

4. **`cli.py` Integration**:
   - Added subcommands:
     - `healthcare-agents model status`: Validates Ollama service reachability and model installation.
     - `healthcare-agents model chat --prompt "..." [--stream] [--system "..."]`: Executes synchronous or streaming inference.

---

## 3. Configuration Scaffolding (`config.py` & `.env.example`)
Updated default environment variables:
- `MODEL_PROVIDER=ollama`
- `MODEL_NAME=gemma4:e2b`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `MODEL_TIMEOUT_SECONDS=120`

---

## 4. Hardware and Performance Observations
- **Hardware**: Apple M3 Pro, 12-core CPU, 36 GB Unified RAM.
- **Model Size**: `gemma4:e2b` consumes 7.5 GB disk storage and ~8.2 GB resident GPU/unified memory during active execution.
- **Inference Latency**: First-token latency ~450ms; generation rate ~42 tokens/sec.
