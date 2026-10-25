#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Model Bootstrap Script for Containerized Ollama Profile
# ------------------------------------------------------------------------------

MODEL_NAME="${OLLAMA_MODEL:-${MODEL_NAME:-gemma4:e2b}}"
OLLAMA_HOST="${OLLAMA_BASE_URL:-http://ollama:11434}"

echo "=================================================================="
echo "Open Healthcare Agentic Platform: Ollama Model Bootstrap"
echo "Target Model: ${MODEL_NAME}"
echo "Ollama Endpoint: ${OLLAMA_HOST}"
echo "=================================================================="

# Wait for Ollama service port to respond
echo "Waiting for Ollama service to become healthy at ${OLLAMA_HOST}..."
MAX_ATTEMPTS=30
ATTEMPT=0
until curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
        echo "ERROR: Ollama service failed to become available after ${MAX_ATTEMPTS} attempts."
        exit 1
    fi
    echo "Waiting for Ollama service... (attempt ${ATTEMPT}/${MAX_ATTEMPTS})"
    sleep 2
done

echo "Ollama service is reachable."

# Check if model already exists in local tags
if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "\"name\":\"${MODEL_NAME}\""; then
    echo "Model '${MODEL_NAME}' is already present in persistent storage."
else
    echo "Model '${MODEL_NAME}' not found in storage. Initiating pull..."
    curl -s -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\":\"${MODEL_NAME}\"}"
    echo ""
    echo "Model pull command dispatched."
fi

# Confirm model readiness
echo "Verifying model readiness..."
MAX_MODEL_WAIT=60
MODEL_ATTEMPT=0
until curl -s "${OLLAMA_HOST}/api/tags" | grep -q "\"name\":\"${MODEL_NAME}\""; do
    MODEL_ATTEMPT=$((MODEL_ATTEMPT + 1))
    if [ "$MODEL_ATTEMPT" -ge "$MAX_MODEL_WAIT" ]; then
        echo "ERROR: Model '${MODEL_NAME}' did not become available in Ollama after ${MAX_MODEL_WAIT} checks."
        exit 1
    fi
    echo "Waiting for model '${MODEL_NAME}' to complete download and registration... (${MODEL_ATTEMPT}/${MAX_MODEL_WAIT})"
    sleep 5
done

echo "SUCCESS: Model '${MODEL_NAME}' is ready in Ollama."
exit 0
