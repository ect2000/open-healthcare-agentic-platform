# Milestone M6.1 Commands & Execution Record

## Git & Environment Preparation
```bash
git checkout -b feature/m06-1-ui-observability
```

## Linting & Formatting Verification
```bash
uv run ruff check .
# Output: All checks passed!

uv run ruff format --check .
# Output: 120 files already formatted

uv run mypy src tests
# Output: Success: no issues found in 63 source files
```

## Unit & Integration Test Suite Verification
```bash
uv run pytest
# Output:
# 142 passed, 15 skipped, 1 warning in 36.57s
# Required test coverage of 90.0% reached. Total coverage: 90.45%
```

## Docker Compose Verification
```bash
docker compose config
# Output: Syntactically valid compose configuration

docker compose up -d --build
# Output:
# ✔ Container open-healthcare-api    Healthy
# ✔ Container open-healthcare-ui     Started
```

## Health & Readiness API Probing
```bash
curl -s http://localhost:8000/health
# Output:
# {"status":"healthy","version":"0.6.0","environment":"development","timestamp":"2026-10-25T14:53:10.675093+00:00"}

curl -s http://localhost:8000/ready
# Output:
# {"ready":true,"status":"ready","version":"0.6.0","ollama_service_available":true,"model_installed":true,"model_name":"gemma4:e2b","retrieval_mode":"live","four_sources_configured":true,"details":{"nppes_api_url":"https://npiregistry.cms.hhs.gov/api/","pubmed_api_url":"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/","cms_api_url":"https://data.cms.gov/provider-data/api/1/","medlineplus_api_url":"https://wsearch.nlm.nih.gov/ws/query"}}
```

## Playwright Browser Verification & Screenshot Capture
```bash
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.goto('http://localhost:8501', wait_until='networkidle')
    page.screenshot(path='docs/images/m6_1_header_branding.png')
    page.locator('button:has-text(\"🔍 Search\")').click()
    page.wait_for_selector('text=Grounded Healthcare Discovery Results', timeout=90000)
    page.screenshot(path='docs/images/m6_1_search_results.png', full_page=True)
    page.locator('[role=\"tab\"]:has-text(\"Patient Education\")').click()
    page.screenshot(path='docs/images/m6_1_patient_education_formatting.png')
    page.locator('[role=\"tab\"]:has-text(\"Agent Execution & Observability\")').click()
    page.screenshot(path='docs/images/m6_1_agent_execution_timeline.png')
    browser.close()
"
```
