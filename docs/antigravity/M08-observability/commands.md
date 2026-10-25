# Milestone M8: Executed Commands & Verifications

```bash
# 1. Baseline verification & branch creation
git checkout main
git pull --ff-only origin main
git checkout -b feature/m08-opentelemetry-observability

# 2. Add OpenTelemetry dependencies
uv add opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http opentelemetry-instrumentation-fastapi

# 3. Create observability subsystem
# Created:
# - src/healthcare_agents/observability/config.py
# - src/healthcare_agents/observability/tracing.py
# - src/healthcare_agents/observability/metrics.py
# - src/healthcare_agents/observability/instrumentation.py
# - src/healthcare_agents/observability/__init__.py

# 4. Create comprehensive test suite
# - tests/observability/test_config.py
# - tests/observability/test_tracing.py
# - tests/observability/test_metrics.py
# - tests/observability/test_fastapi_instrumentation.py
# - tests/observability/test_failure_observability.py

# 5. Execute observability unit & integration tests
uv run pytest tests/observability/ -v
# Output: 20 passed in 1.48s

# 6. Instrument LangGraph workflow, parallel retriever, evidence processor, and Ollama adapter
# Modified:
# - src/healthcare_agents/api/app.py
# - src/healthcare_agents/api/schemas.py
# - src/healthcare_agents/api/service.py
# - src/healthcare_agents/workflows/healthcare_graph.py
# - src/healthcare_agents/retrieval/parallel_retriever.py
# - src/healthcare_agents/agents/evidence_processor.py
# - src/healthcare_agents/models/ollama_adapter.py
# - src/healthcare_agents/ui/components.py
# - src/healthcare_agents/ui/api_client.py

# 7. Provision Docker Compose observability stack
# Created:
# - observability/otel-collector/config.yaml
# - observability/prometheus/prometheus.yml
# - observability/tempo/tempo.yaml
# - observability/grafana/provisioning/datasources/datasources.yaml
# - observability/grafana/provisioning/dashboards/dashboards.yaml
# - observability/grafana/dashboards/healthcare_observability.json
# Updated docker-compose.yml with otel-collector, prometheus, tempo, grafana

# 8. Start full container stack
docker compose up -d --build
# Output:
# Container open-healthcare-prometheus      Started
# Container open-healthcare-tempo           Started
# Container open-healthcare-otel-collector  Started
# Container open-healthcare-grafana         Started
# Container open-healthcare-api             Started
# Container open-healthcare-ui              Started

# 9. Verify live telemetry pipeline
curl -s http://localhost:8000/health
# Output: {"status":"healthy", ...}

# Execute live search query to generate distributed traces and metrics:
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find the best pediatric dentists in Houston, Texas, and research pediatric dental anxiety."}'
# Output returned: "trace_id": "22a62323cbffcd1c793cf7624706b245"

# Query Prometheus metrics:
curl -s "http://localhost:9090/api/v1/query?query=healthcare_search_requests_total"
# Output: {"status":"success","data":{"result":[{"metric":{"__name__":"healthcare_search_requests_total","status":"success"},"value":[1774464188.423,"1"]}]}}

# 10. Automated browser screenshot capture via Playwright
uv run python scripts/capture_m8_screenshots.py
# Output: Successfully captured all 7 screenshots:
# - docs/images/m08_platform_overview.png
# - docs/images/m08_agent_workflow.png
# - docs/images/m08_retrieval_metrics.png
# - docs/images/m08_evidence_quality.png
# - docs/images/m08_gemma4_inference.png
# - docs/images/m08_tempo_trace.png
# - docs/images/m08_streamlit_trace.png

# 11. Run complete test suite and coverage check
uv run pytest --cov=healthcare_agents --cov-report=term-missing
# Output: 173 passed, 15 skipped in 76.54s
# TOTAL coverage: 90.21% (exceeds >= 90% quality gate)

# 12. Run code style and type checkers
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
# Output:
# All checks passed!
# 146 files already formatted.
# Success: no issues found in 77 source files.
```
