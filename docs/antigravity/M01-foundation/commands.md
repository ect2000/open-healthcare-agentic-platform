# Milestone M01: Commands Executed & Evidence

The following commands were executed to configure, test, verify, build, and deploy Milestone M1:

---

## 1. Environment & Dependency Setup

```bash
# Verify Python version and create virtual environment
/Users/hastimal.jangid/.local/bin/python3.12 -m venv .venv

# Upgrade pip and install development dependencies in editable mode
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
```

Output:
```
Successfully installed ast-serialize-0.13.1 build-1.6.1 coverage-7.17.0 healthcare-agents-0.1.0 iniconfig-2.3.1 librt-0.16.0 mypy-2.4.0 mypy_extensions-1.1.0 packaging-26.3 pathspec-1.1.1 pluggy-1.7.0 pygments-2.21.0 pyproject_hooks-1.3.3 pytest-9.1.1 pytest-cov-7.1.0 ruff-0.17.2 typing_extensions-4.16.0
```

---

## 2. Code Quality & Test Validation

```bash
# Run Ruff linting
.venv/bin/ruff check .

# Run Ruff format check
.venv/bin/ruff format --check .

# Run mypy static type checking
.venv/bin/mypy src tests

# Run pytest with test coverage
.venv/bin/pytest
```

Outputs:
```
All checks passed!
11 files already formatted
Success: no issues found in 6 source files
...............                                                          [100%]
================================ tests coverage ================================
TOTAL                                  76      1    99%
Required test coverage of 90.0% reached. Total coverage: 98.68%
15 passed in 0.05s
```

---

## 3. Package Build & Clean Virtualenv Verification

```bash
# Build wheel and source distribution
.venv/bin/python -m build

# Install wheel into isolated clean virtual environment
python3.12 -m venv /tmp/test_env
/tmp/test_env/bin/pip install dist/healthcare_agents-0.1.0-py3-none-any.whl

# Test CLI in clean environment
/tmp/test_env/bin/healthcare-agents --version
/tmp/test_env/bin/healthcare-agents health
/tmp/test_env/bin/healthcare-agents health --verbose
/tmp/test_env/bin/python -c "import healthcare_agents; print('Imported version:', healthcare_agents.__version__)"

# Cleanup
rm -rf /tmp/test_env
```

Outputs:
```
Successfully built healthcare_agents-0.1.0.tar.gz and healthcare_agents-0.1.0-py3-none-any.whl
healthcare-agents 0.1.0
Status: healthy
Environment: development
Log Level: INFO
Configured Model Provider: ollama
App Name: open-healthcare-agentic-platform
Configured Model: gemma:4b
Ollama URL: http://localhost:11434
Imported version: 0.1.0
```

---

## 4. Git Release & Tagging

```bash
# Commit M1 deliverables
git commit -m "feat(m01): repository foundation, python packaging, tests and CI"

# Tag milestone
git tag -a v0.1.0-m01 -m "Milestone M1: Repository Foundation, Python & CI"

# Push to GitHub
git push origin main
git push origin v0.1.0-m01
```

---

## 5. GitHub Actions Verification

```bash
gh run list --limit 3
gh run view 40091621046
```

Output:
```
✓ main CI · 40091621046
Triggered via push
JOBS
✓ test-and-lint in 21s (ID 120865299894)
```
