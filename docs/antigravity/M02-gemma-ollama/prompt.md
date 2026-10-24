# Milestone M02: Original Prompt & Instructions

The following is the complete, verbatim original prompt and instructions provided for Milestone M2:

```markdown
PROJECT: open-healthcare-agentic-platform

MILESTONE: M2 — Gemma 4 + Ollama Local Inference
TARGET TAG: v0.2.0-m02
BRANCH: main ONLY

Read AGENTS.md and all M1 documentation before starting.

Follow all permanent project rules.

==================================================
OBJECTIVE
==================================================

Implement real, local, self-hosted Gemma 4 inference
using Ollama.

Build a reusable Python model adapter that will later
support LangGraph agents, MCP tool calling, and vLLM.

M2 must remain independent of the future agent
orchestration framework.

Do NOT implement M3 or later milestones.

==================================================
STEP 1 — INSPECT ENVIRONMENT
==================================================

1. Confirm repository and main branch.
2. Verify working tree is clean.
3. Inspect existing Python code and tests.
4. Read pyproject.toml and .env.example.
5. Check:
   - Python version
   - Ollama installation/version
   - Ollama service availability
   - Already downloaded Ollama models
   - Available hardware/RAM

6. Do not remove existing models.
7. Do not overwrite user configuration.
8. Update outdated GitHub Actions versions if needed,
   keeping CI compatible and fully tested.

==================================================
STEP 2 — CONFIGURE GEMMA 4
==================================================

Use the official Ollama model:

gemma4:e2b

Default environment variables:

MODEL_PROVIDER=ollama
MODEL_NAME=gemma4:e2b
OLLAMA_BASE_URL=http://localhost:11434
MODEL_TIMEOUT_SECONDS=120

Allow users to override these settings.

Check Ollama is running.

If the model is missing:
- Explain the required download.
- Download with ollama pull gemma4:e2b when
  resources and network access permit.
- Verify ollama list includes the exact model.

Do not download unnecessary large models.

Do not use:
- Gemini API
- Vertex AI
- Cloud inference
- Hosted model services

==================================================
STEP 3 — IMPLEMENT MODEL ADAPTER
==================================================

Create an organized models package:

src/healthcare_agents/models/
    __init__.py
    base.py
    ollama_adapter.py
    schemas.py

Implement:

1. A reusable model interface/protocol.
2. Ollama model implementation.
3. Typed request/response schemas.
4. Text generation.
5. Streaming generation.
6. Optional system instructions.
7. Model availability check.
8. Request timeout and retry handling.
9. Explicit connection errors.
10. Basic inference metadata.

Where Ollama provides it, capture:
- Model name
- Total request duration
- Prompt token count
- Generated token count
- Evaluation duration

Use Ollama's documented /api/chat and
/api/tags endpoints as appropriate.

Handle streaming responses correctly.

Do not depend on LangGraph.

The adapter design must make it straightforward to
replace Ollama with a vLLM-compatible adapter later.

==================================================
STEP 4 — CLI INTEGRATION
==================================================

Extend the existing CLI.

Required commands:

healthcare-agents model status

healthcare-agents model chat
  --prompt "Explain what NPPES is."

healthcare-agents model chat
  --prompt "Explain PubMed."
  --stream

Keep existing commands functional:

healthcare-agents --version
healthcare-agents health

Implement informative errors when:
- Ollama service is unavailable.
- The model is not installed.
- A request times out.
- Model inference returns an error.

Do not expose private model reasoning or internal
thinking tokens in normal user-facing output.

==================================================
STEP 5 — TESTING
==================================================

Add offline unit tests covering:

- Model configuration
- Provider selection
- Request construction
- Response parsing
- Streaming chunks
- Empty responses
- Missing model
- Connection errors
- Timeouts
- Malformed API responses
- Usage metadata
- CLI behavior

Mock the Ollama HTTP API for offline tests.

Also implement opt-in LIVE integration tests.

Live tests must:
1. Connect to actual local Ollama.
2. Confirm Gemma 4 is installed.
3. Send a real inference request.
4. Verify a meaningful response.
5. Test streaming.
6. Record observed timing and usage metadata.
7. Verify failure handling where practical.

Do not silently skip mandatory M2 live acceptance.

If real inference is unavailable, document the
blocker and leave M2 incomplete.

Preserve every M1 test.

==================================================
STEP 6 — VALIDATION
==================================================

Run:

pytest
ruff check .
ruff format --check .
mypy src tests
python -m build

Also test:

healthcare-agents --version
healthcare-agents health
healthcare-agents model status
healthcare-agents model chat
healthcare-agents model chat --stream

Use the project's existing virtual environment
and actual installed tool paths.

Verify a fresh wheel installation.

Do not fabricate test results.

==================================================
STEP 7 — DOCUMENTATION
==================================================

Create:

docs/antigravity/M02-gemma-ollama/
    prompt.md
    commands.md
    implementation.md
    verification.md

Save the FULL original prompt in prompt.md.

Save actual shell commands and meaningful output
in commands.md.

Document:
- Ollama version
- Exact Gemma 4 model tag
- Model download/installation
- Model adapter architecture
- Real inference examples
- Actual test results
- Error handling
- Resource requirements
- Known limitations

Update:

docs/antigravity/README.md
docs/milestones/M02-gemma-ollama.md
docs/architecture/README.md
README.md
.env.example

Clearly mark future LangGraph, Docker, Kubernetes,
and vLLM features as planned, not implemented.

Do not commit model weights or sensitive data.

==================================================
STEP 8 — GIT WORKFLOW
==================================================

Work directly on main ONLY.

Do not create branches.

Follow:
Implement → Test → Verify → Document →
Commit → Push → Verify CI → Tag → Push Tag

After all required local tests pass:

1. Inspect git status and diff.
2. Verify no secrets or model weights are staged.
3. Commit code and documentation to main.
4. Push main.
5. Verify GitHub Actions CI passes.
6. Create annotated tag:

   v0.2.0-m02

7. Push tag to origin.
8. Verify remote tag points to the correct commit.

Never force-push.
Never overwrite existing tags.

If CI fails, fix and retest before tagging.

==================================================
STEP 9 — FINAL REPORT
==================================================

Provide:

1. Implementation summary
2. Final repository structure
3. Ollama version
4. Gemma 4 model and size
5. Actual inference response
6. Streaming verification
7. Test count and coverage
8. Ruff, mypy and build results
9. Commit SHA
10. Tag verification
11. GitHub Actions results
12. Any limitations or remaining blockers

Confirm whether M2 is COMPLETE.

Do not start M3.

==================================================
SUCCESS CRITERIA
==================================================

A developer can:

1. Clone the repository.
2. Install Python dependencies.
3. Run Ollama with Gemma 4.
4. Execute healthcare-agents model status.
5. Execute healthcare-agents model chat.
6. Receive a genuine locally generated answer.
7. Stream responses.
8. Run all automated tests successfully.

All tests and CI must pass before publishing
the M2 tag.
```
