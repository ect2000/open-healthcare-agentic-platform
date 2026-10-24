# Milestone M02: Commands Executed & Raw Evidence

The following commands were executed to configure, test, verify, and validate Milestone M2:

---

## 1. Environment & Hardware Inspection

```bash
which ollama && ollama --version && ollama list && curl -s http://localhost:11434/api/tags
sysctl hw.memsize hw.ncpu machdep.cpu.brand_string
```

Output:
```
/opt/homebrew/bin/ollama
ollama version is 0.40.10
NAME          ID              SIZE      MODIFIED    
gemma4:12b    6114515d63c1    8.0 GB    3 weeks ago

hw.memsize: 38654705664 (36 GB Unified Memory)
hw.ncpu: 12
machdep.cpu.brand_string: Apple M3 Pro
```

---

## 2. Gemma 4 Model Download

```bash
ollama pull gemma4:e2b
ollama list
```

Output:
```
pulling manifest 
pulling model: 100% ▕█████████████████████████▏ 7.5 GB                         
writing manifest 
success 

NAME          ID              SIZE      MODIFIED      
gemma4:e2b    45d11505b91d    7.5 GB    6 seconds ago    
gemma4:12b    6114515d63c1    8.0 GB    3 weeks ago      
```

---

## 3. Automated Unit & Live Tests Execution

```bash
.venv/bin/pytest
```

Output:
```
.........................................                                [100%]
================================ tests coverage ================================
______________ coverage: platform darwin, python 3.12.15-final-0 _______________

Name                                             Stmts   Miss  Cover   Missing
------------------------------------------------------------------------------
src/healthcare_agents/__init__.py                    3      0   100%
src/healthcare_agents/cli.py                       114     16    86%   112-114, 140-142, 160-162, 169-171, 222, 229-230, 237
src/healthcare_agents/config.py                     49      0   100%
src/healthcare_agents/models/__init__.py             8      0   100%
src/healthcare_agents/models/base.py                16      0   100%
src/healthcare_agents/models/ollama_adapter.py     130      8    94%   74-75, 161-165, 236, 250, 253
src/healthcare_agents/models/schemas.py             27      0   100%
------------------------------------------------------------------------------
TOTAL                                              347     24    93%
Required test coverage of 90.0% reached. Total coverage: 93.08%
41 passed in 8.06s
```

---

## 4. Linting, Formatting & Type Checks

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src tests
```

Output:
```
All checks passed!
25 files already formatted
Success: no issues found in 14 source files
```

---

## 5. Live CLI Inference Verification

```bash
# Model status
.venv/bin/healthcare-agents model status

# Synchronous inference
.venv/bin/healthcare-agents model chat --prompt "Explain what NPPES is in one concise sentence."

# Streaming inference
.venv/bin/healthcare-agents model chat --prompt "Explain PubMed in one concise sentence." --stream
```

Outputs:
```
=== Model Service Status ===
Provider: ollama
Model: gemma4:e2b
Endpoint: http://localhost:11434
Service Status: reachable
Model Availability: installed (gemma4:e2b)

PubMed is a free search engine accessing millions of biomedical literature citations and abstracts from various scientific journals to aid in medical research.
```

---

## 6. Package Build & Clean Virtualenv Verification

```bash
# Build wheel
.venv/bin/python -m build

# Install and verify in clean venv
python3.12 -m venv /tmp/clean_env
/tmp/clean_env/bin/pip install dist/healthcare_agents-0.1.0-py3-none-any.whl
/tmp/clean_env/bin/healthcare-agents --version
/tmp/clean_env/bin/healthcare-agents health
/tmp/clean_env/bin/healthcare-agents model status
rm -rf /tmp/clean_env
```

Output:
```
Successfully built healthcare_agents-0.1.0.tar.gz and healthcare_agents-0.1.0-py3-none-any.whl
healthcare-agents 0.1.0
Status: healthy
Environment: development
Log Level: INFO
Configured Model Provider: ollama
=== Model Service Status ===
Provider: ollama
Model: gemma4:e2b
Endpoint: http://localhost:11434
Service Status: reachable
Model Availability: installed (gemma4:e2b)
```
