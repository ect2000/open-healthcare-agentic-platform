"""Process and runtime launcher management for Open Healthcare Agentic Platform."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    status: bool
    message: str
    remediation: str = ""


def get_runtime_dir() -> Path:
    """Return local user cache directory for PID and state files."""
    base_dir = Path.home() / ".cache" / "open-healthcare"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_pid_file() -> Path:
    return get_runtime_dir() / "runtime_pids.json"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check whether a local TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_command_available(cmd_name: str) -> bool:
    """Check if command-line tool exists in PATH."""
    from shutil import which

    return which(cmd_name) is not None


def check_ollama(
    base_url: str = "http://localhost:11434", required_model: str = "gemma4:e2b"
) -> tuple[bool, str, list[str]]:
    """Check Ollama daemon reachability and available models."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                has_model = any(
                    required_model in m or required_model.split(":")[0] in m for m in models
                )
                return (
                    True,
                    (
                        "Model available"
                        if has_model
                        else f"Ollama reachable, but '{required_model}' not found"
                    ),
                    models,
                )
    except Exception as exc:
        return False, f"Ollama daemon unreachable at {base_url} ({exc})", []
    return False, "Ollama check failed", []


def run_prerequisite_checks(
    inference_url: str = "http://localhost:11434",
    model_name: str = "gemma4:e2b",
    api_port: int = 8000,
    ui_port: int = 8501,
) -> list[CheckResult]:
    """Execute preflight checks across Python, Ports, Ollama, and Optional Docker."""
    results: list[CheckResult] = []

    # 1. Python runtime
    py_ok = sys.version_info >= (3, 12)
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    results.append(
        CheckResult(
            name="Python Version",
            status=py_ok,
            message=f"Python {py_ver}" if py_ok else f"Python {py_ver} (< 3.12 unsupported)",
            remediation="Please install Python 3.12 or newer: https://www.python.org",
        )
    )

    # 2. Ports availability
    api_port_busy = is_port_in_use(api_port)
    results.append(
        CheckResult(
            name=f"Port {api_port} (FastAPI)",
            status=not api_port_busy,
            message="Available" if not api_port_busy else f"Port {api_port} is already in use",
            remediation=f"Stop process occupying port {api_port} or run with --api-port <port>",
        )
    )

    ui_port_busy = is_port_in_use(ui_port)
    results.append(
        CheckResult(
            name=f"Port {ui_port} (Streamlit)",
            status=not ui_port_busy,
            message="Available" if not ui_port_busy else f"Port {ui_port} is already in use",
            remediation=f"Stop process occupying port {ui_port} or run with --ui-port <port>",
        )
    )

    # 3. Inference / Ollama Backend
    ollama_ok, ollama_msg, models = check_ollama(base_url=inference_url, required_model=model_name)
    has_model = any(model_name in m or model_name.split(":")[0] in m for m in models)
    results.append(
        CheckResult(
            name="Inference Endpoint (Ollama)",
            status=ollama_ok,
            message=ollama_msg,
            remediation=(
                "Ensure Ollama is installed and running (`ollama serve`). "
                "Download: https://ollama.com"
            ),
        )
    )

    if ollama_ok:
        results.append(
            CheckResult(
                name=f"Model '{model_name}'",
                status=has_model,
                message=f"Model '{model_name}' found"
                if has_model
                else f"Model '{model_name}' missing",
                remediation=f"Pull model with: `ollama pull {model_name}`",
            )
        )

    # 4. Optional Docker daemon (informational, not strictly required for Native mode)
    docker_available = check_command_available("docker")
    results.append(
        CheckResult(
            name="Docker (Optional for Compose/K8s)",
            status=docker_available,
            message="Installed"
            if docker_available
            else "Not installed (Native mode remains available)",
            remediation=(
                "Docker is optional for Native Python mode. Required only for Compose and Kind."
            ),
        )
    )

    return results


def wait_for_endpoint(url: str, timeout_seconds: float = 30.0) -> bool:
    """Poll URL until HTTP 200/204 or timeout."""
    t0 = time.time()
    while time.time() - t0 < timeout_seconds:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def start_native_services(
    api_host: str = "127.0.0.1",
    api_port: int = 8000,
    ui_port: int = 8501,
    inference_url: str = "http://localhost:11434",
    model_name: str = "gemma4:e2b",
    open_browser: bool = True,
) -> int:
    """Start both FastAPI and Streamlit as managed child processes in native mode."""
    pid_file = get_pid_file()

    # Pass configuration to subprocesses via environment
    env = os.environ.copy()
    env["OLLAMA_BASE_URL"] = inference_url
    env["MODEL_NAME"] = model_name
    env["HEALTHCARE_AGENTS_API_URL"] = f"http://{api_host}:{api_port}"
    env["API_BASE_URL"] = f"http://{api_host}:{api_port}"

    from healthcare_agents.ui import app as ui_module

    ui_script = Path(ui_module.__file__).resolve()

    sys.stdout.write("==================================================================\n")
    sys.stdout.write("🚀 Starting Open Healthcare Agentic Platform (Native Mode)\n")
    sys.stdout.write("==================================================================\n")
    sys.stdout.write(f"Inference Backend: {inference_url} ({model_name})\n")
    sys.stdout.write(f"FastAPI Target:    http://{api_host}:{api_port}\n")
    sys.stdout.write(f"Streamlit UI:      http://localhost:{ui_port}\n")
    sys.stdout.write("------------------------------------------------------------------\n")

    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "healthcare_agents.api.app:app",
        "--host",
        api_host,
        "--port",
        str(api_port),
    ]

    ui_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_script),
        "--server.port",
        str(ui_port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    api_proc = subprocess.Popen(
        api_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ui_proc = subprocess.Popen(
        ui_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    pids_data = {
        "api_pid": api_proc.pid,
        "ui_pid": ui_proc.pid,
        "api_port": api_port,
        "ui_port": ui_port,
        "created_at": time.time(),
    }
    with open(pid_file, "w") as f:
        json.dump(pids_data, f, indent=2)

    sys.stdout.write(f"Started FastAPI backend (PID: {api_proc.pid})...\n")
    sys.stdout.write(f"Started Streamlit frontend (PID: {ui_proc.pid})...\n")

    sys.stdout.write("Waiting for application services to be ready...\n")
    api_ready = wait_for_endpoint(f"http://{api_host}:{api_port}/health", timeout_seconds=15.0)
    ui_ready = wait_for_endpoint(f"http://localhost:{ui_port}/_stcore/health", timeout_seconds=20.0)

    if not api_ready or not ui_ready:
        sys.stderr.write("⚠️ Warning: One or more services did not report ready in time.\n")
    else:
        sys.stdout.write("✅ All services are healthy and running!\n\n")
        sys.stdout.write(f"🔗 Streamlit Web UI:   http://localhost:{ui_port}\n")
        sys.stdout.write(f"🔗 FastAPI Docs:       http://{api_host}:{api_port}/docs\n")
        sys.stdout.write(f"🔗 Health Probe:       http://{api_host}:{api_port}/health\n\n")

    if open_browser and ui_ready:
        try:
            webbrowser.open(f"http://localhost:{ui_port}")
        except Exception:
            pass

    sys.stdout.write("Press Ctrl+C to stop services gracefully.\n")
    try:
        while True:
            time.sleep(1.0)
            if api_proc.poll() is not None or ui_proc.poll() is not None:
                sys.stderr.write("Service process terminated unexpectedly.\n")
                break
    except KeyboardInterrupt:
        sys.stdout.write("\nGracefully shutting down services...\n")
    finally:
        stop_native_services()

    return 0


def stop_native_services() -> int:
    """Stop only processes started and recorded by this CLI instance."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        sys.stdout.write("No active native service instances recorded.\n")
        return 0

    try:
        with open(pid_file) as f:
            data = json.load(f)
    except Exception:
        data = {}

    api_pid = data.get("api_pid")
    ui_pid = data.get("ui_pid")

    for name, pid in (("API", api_pid), ("UI", ui_pid)):
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                sys.stdout.write(f"Stopped {name} service (PID: {pid}).\n")
            except ProcessLookupError:
                pass
            except Exception as e:
                sys.stderr.write(f"Could not terminate PID {pid}: {e}\n")

    try:
        pid_file.unlink(missing_ok=True)
    except Exception:
        pass

    return 0


def get_runtime_status(api_port: int = 8000, ui_port: int = 8501) -> dict[str, str]:
    """Inspect status of local API and UI instances."""
    pid_file = get_pid_file()
    status = {"api": "stopped", "ui": "stopped"}

    if is_port_in_use(api_port):
        status["api"] = f"running (port {api_port})"
    if is_port_in_use(ui_port):
        status["ui"] = f"running (port {ui_port})"

    if pid_file.exists():
        try:
            with open(pid_file) as f:
                data = json.load(f)
            status["managed_pids"] = f"API PID {data.get('api_pid')}, UI PID {data.get('ui_pid')}"
        except Exception:
            pass

    return status
