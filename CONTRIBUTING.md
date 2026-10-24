# Contributing to Open Healthcare Agentic Platform

Thank you for your interest in contributing to the Open Healthcare Agentic Platform! We welcome contributions from developers, researchers, healthcare informaticists, and open-source advocates.

---

## 1. Development Environment Setup

### Prerequisites
- Python 3.12 or newer
- Git

### Initial Setup
1. Clone the repository and navigate into the project directory:
   ```bash
   git clone https://github.com/hastimal/open-healthcare-agentic-platform.git
   cd open-healthcare-agentic-platform
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Upgrade pip and install development dependencies in editable mode:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

---

## 2. Code Quality Standards

Before submitting a pull request, ensure all checks pass:

- **Linting:**
  ```bash
  ruff check .
  ```
- **Formatting:**
  ```bash
  ruff format --check .
  ```
- **Type Checking:**
  ```bash
  mypy src tests
  ```
- **Testing & Coverage:**
  ```bash
  pytest
  ```

---

## 3. Contribution Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-feature-name
   ```
2. Write clean, typed, and well-tested code following the `src/` layout.
3. Ensure no secrets, logs, model weights, or unnecessary dependencies are introduced.
4. Open a pull request against `main` describing your changes and testing steps.
