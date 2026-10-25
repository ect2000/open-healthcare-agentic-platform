# Milestone M5 Execution Commands & Verification Log

## 1. Environment & Dependency Setup
```bash
# Add FastAPI, Uvicorn, Streamlit, and Playwright
uv add "fastapi>=0.110.0" "uvicorn>=0.29.0" "streamlit>=1.33.0" "httpx>=0.27.0"
uv add --dev playwright
uv run playwright install chromium
```

## 2. Static Analysis & Type Checking
```bash
# Ruff Lint check
uv run ruff check .
# Output: All checks passed!

# Ruff Format check
uv run ruff format --check .
# Output: 106 files already formatted

# Mypy Strict Type Checking
uv run mypy src tests
# Output: Success: no issues found in 62 source files
```

## 3. Test Suite & Coverage
```bash
uv run pytest
# Output:
# 133 passed, 15 skipped, 1 warning in 34.28s
# Required test coverage of 90.0% reached. Total coverage: 90.76%
```

## 4. Live Server Execution & Endpoints Verification
```bash
# Start FastAPI backend (Port 8000)
uv run python -m uvicorn healthcare_agents.api.app:app --host 127.0.0.1 --port 8000

# Test GET /health
curl -s http://127.0.0.1:8000/health
# Output: {"status":"healthy","version":"0.5.0","environment":"development","timestamp":"2026-10-25T12:19:23.646681+00:00"}

# Test GET /ready
curl -s http://127.0.0.1:8000/ready
# Output: {"ready":true,"status":"ready","version":"0.5.0","ollama_service_available":true,"model_installed":true,"model_name":"gemma4:e2b","retrieval_mode":"live","four_sources_configured":true,"details":{...}}

# Test POST /api/v1/search (Fixtures demonstration)
curl -s -X POST http://127.0.0.1:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find pediatric dentists in Houston and research on pediatric dental anxiety", "retrieval_mode": "fixtures", "result_limit": 3}'
# Output: Full SearchResponse JSON with validated provider records, literature, and grounded synthesis
```

## 5. Streamlit Browser Verification & Playwright Screenshots
```bash
# Start Streamlit Application (Port 8501)
uv run python -m streamlit run src/healthcare_agents/ui/app.py --server.port 8501 --server.headless true

# Check Streamlit Core Health
curl -s http://localhost:8501/_stcore/health
# Output: ok

# Capture Initial Streamlit UI
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.goto('http://localhost:8501', wait_until='networkidle', timeout=30000)
    page.wait_for_selector('h1', timeout=15000)
    page.screenshot(path='docs/images/m5_streamlit_ui.png')
    browser.close()
"

# Execute End-to-End Search via Streamlit and Capture Results
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1200})
    page.goto('http://localhost:8501', wait_until='networkidle', timeout=30000)
    page.wait_for_selector('h1', timeout=15000)
    page.click('button:has-text(\"🔍 Search\")')
    page.wait_for_selector('text=Grounded Healthcare Discovery Results', timeout=90000)
    page.wait_for_timeout(2000)
    page.screenshot(path='docs/images/m5_streamlit_results.png')
    browser.close()
"
```

## 6. Architecture Diagram Rendering
```bash
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 440})
    page.goto('file:///Users/hastimal.jangid/Desktop/hmeb/GitHub/open-healthcare-agentic-platform/docs/images/m5_workflow.svg')
    page.screenshot(path='docs/images/m5_workflow.png')
    browser.close()
"
```
