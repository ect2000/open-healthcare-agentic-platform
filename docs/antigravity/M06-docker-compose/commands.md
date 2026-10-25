# Milestone M6 Commands & Verification Log

## 1. Baseline Verification
```bash
git status
git branch --show-current
git tag -l "v*"
curl -s http://localhost:11434/api/tags
docker info
```

## 2. Docker Image Builds
```bash
# Build FastAPI Container Image
docker build -t open-healthcare-api:latest -f Dockerfile.api .

# Build Streamlit Container Image
docker build -t open-healthcare-ui:latest -f Dockerfile.ui .

# Verify Image Sizes
docker image ls | grep open-healthcare
# Output:
# open-healthcare-api:latest   304a96303592        198MB
# open-healthcare-ui:latest    d800bbc11bbb        198MB
```

## 3. Docker Compose Configuration Validation
```bash
# Validate default profile (Host Ollama)
docker compose config

# Validate container-ollama profile
docker compose --profile container-ollama config
```

## 4. Container Deployment & Health Probes (Profile A: Host Ollama)
```bash
# Launch containers
docker compose up -d

# Check process and health status
docker compose ps
# Output:
# open-healthcare-api   Up (healthy)   0.0.0.0:8000->8000/tcp
# open-healthcare-ui    Up (healthy)   0.0.0.0:8501->8501/tcp

# Verify health and readiness endpoints
curl -s http://localhost:8000/health
# Output: {"status":"healthy","version":"0.6.0","environment":"development",...}

curl -s http://localhost:8000/ready
# Output: {"ready":true,"status":"ready","version":"0.6.0","ollama_service_available":true,"model_installed":true,"model_name":"gemma4:e2b",...}

curl -s http://localhost:8501/_stcore/health
# Output: ok
```

## 5. End-to-End Query Verification Against Containers
```bash
# Fixture-mode search query against containerized FastAPI
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find pediatric dentists in Houston and research on pediatric dental anxiety", "retrieval_mode": "fixtures", "result_limit": 3}'

# Live federal multi-source search query (NPPES, PubMed, CMS, MedlinePlus)
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find pediatric dentists in Houston and research on pediatric dental anxiety", "retrieval_mode": "live", "result_limit": 3}'
```

## 6. Playwright Browser Automation & UI Screenshots
```bash
# Capture initial container Streamlit UI
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.goto('http://localhost:8501', wait_until='networkidle', timeout=30000)
    page.wait_for_selector('h1', timeout=15000)
    page.screenshot(path='docs/images/m6_container_ui.png')
    browser.close()
"

# Execute search and capture discovery results
uv run python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1200})
    page.goto('http://localhost:8501', wait_until='networkidle', timeout=30000)
    page.wait_for_selector('h1', timeout=15000)
    page.click('button:has-text(\"🔍 Search\")')
    page.wait_for_selector('text=Grounded Healthcare Discovery Results', timeout=90000)
    page.wait_for_timeout(3000)
    page.screenshot(path='docs/images/m6_container_results.png')
    browser.close()
"
```

## 7. Container Lifecycle, Restart & Volume Persistence
```bash
# Test container restart and health recovery
docker compose restart
docker compose ps

# Profile B verification (containerized Ollama service + volume)
docker compose --profile container-ollama up -d ollama
curl -s http://localhost:11435/api/tags
docker volume ls | grep open-healthcare
docker compose --profile container-ollama down
```

## 8. Automated Test Suite & Code Quality Checks
```bash
# Ruff lint & format checks
uv run ruff check .
uv run ruff format --check .

# Mypy strict type checking
uv run mypy src tests

# Full Pytest Suite with Coverage
uv run pytest
# Output: 141 passed, 15 skipped in 51.74s, 90.97% coverage

# Distribution package build
uv build
```
