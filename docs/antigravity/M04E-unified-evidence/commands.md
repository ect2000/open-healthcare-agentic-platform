# Commands Executed for Milestone M4E

## 1. Baseline Verification & Environment Inspection
```bash
git branch --show-current
# main

git status --porcelain
# clean working tree

git tag -l
# includes v0.4.3-m04d

uv run pytest
# 96 passed, 15 skipped in 31.86s
```

## 2. Evidence Package Implementation & Dependencies
```bash
# Package created in src/healthcare_agents/evidence/
# __init__.py, schemas.py, normalization.py, deduplication.py, relevance.py, ranking.py, provenance.py
uv pip install -e .
```

## 3. Full Test Suite & Coverage Verification
```bash
uv run pytest --cov=healthcare_agents --cov-report=term-missing
# Output:
# 114 passed, 15 skipped in 25.54s
# Required test coverage of 90.0% reached. Total coverage: 91.68%
```

## 4. Linting and Static Type Checking
```bash
uv run ruff check .
# Output: All checks passed!

uv run ruff format --check .
# Output: 92 files already formatted

uv run mypy src tests
# Output: Success: no issues found in 51 source files
```

## 5. Build Distribution & Clean Wheel Install Verification
```bash
uv build
# Output:
# Successfully built dist/healthcare_agents-0.4.4.tar.gz
# Successfully built dist/healthcare_agents-0.4.4-py3-none-any.whl

uv run python -c "import tempfile, subprocess; td = tempfile.mkdtemp(); subprocess.run(['uv', 'venv', td + '/testenv'], check=True); subprocess.run(['uv', 'pip', 'install', '--python', td + '/testenv/bin/python', 'dist/healthcare_agents-0.4.4-py3-none-any.whl'], check=True); res = subprocess.run([td + '/testenv/bin/healthcare-agents', '--version'], capture_output=True, text=True, check=True); print('Installed version:', res.stdout.strip())"
# Output: Installed version: healthcare-agents 0.4.4
```

## 6. Live Search Execution
```bash
RETRIEVAL_MODE=live uv run healthcare-agents search \
  --query "Find pediatric dentists in Houston and research on pediatric dental anxiety" \
  --verbose
# Output:
# Stage 1: Query Planning
# Stage 2: Provider Discovery (NPPES) -> Retrieved 5 live candidates
# Stage 3: Research Retrieval (PubMed) -> Retrieved 5 live biomedical publications
# Stage 4: Patient Education Retrieval (MedlinePlus) -> Retrieved 4 live topics
# Stage 4b: Quality Data Retrieval (CMS) -> Verified 0 false quality claims for individual dentists
# Stage 5: Evidence Processing (Normalization, Deduplication, Relevance/Ranking)
#   - Total Normalized: 14 items
#   - Total Deduplicated: 14 items
#   - Total Relevant: 13 items
#   - Excluded Evidence: 1 item (PMID 39046104 dementia / unrelated topical mismatch)
# Stage 5: Deterministic Validation
#   - Validated: 5 providers, 4 PubMed citations, 4 MedlinePlus citations
#   - Citations verified against live URLs and allowed domains
# Stage 6: Grounded Synthesis (Gemma 4)
#   - Grounded narrative generated with valid citations
```

## 7. Diagram Generation
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --screenshot=docs/images/m4e_workflow.png --window-size=1180,430 \
  "file:///Users/hastimal.jangid/Desktop/hmeb/GitHub/open-healthcare-agentic-platform/docs/images/m4e_workflow.svg"
# Output: 129034 bytes written to file docs/images/m4e_workflow.png
```
