#!/usr/bin/env python3
"""One-command demo launcher for M8: Production-Grade Observability.

Validates Docker, native Ollama, starts the full Compose stack (API, Streamlit,
OpenTelemetry Collector, Prometheus, Tempo, Grafana), waits for health/readiness,
and prints URLs.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


def log(msg: str) -> None:
    print(f"[M8-LAUNCHER] {msg}", flush=True)


def check_command(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def wait_for_url(url: str, timeout_seconds: float = 60.0, description: str = "") -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_seconds:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status in (200, 204):
                    log(f"✅ {description} is ready ({url})")
                    return True
        except Exception:
            time.sleep(2.0)
    log(f"⚠️ {description} was not ready within {timeout_seconds}s ({url})")
    return False


def main() -> int:
    log("==================================================================")
    log("🚀 OPEN HEALTHCARE AGENTIC PLATFORM — M8 DEMO LAUNCHER")
    log("==================================================================")

    # 1. Check Docker
    if not check_command(["docker", "info"]):
        log("❌ Docker daemon is not running. Please start Docker Desktop.")
        return 1
    log("✅ Docker daemon is active.")

    # 2. Check native Ollama connectivity
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                log(f"✅ Native Ollama reachable. Installed models: {', '.join(models) or 'None'}")
    except Exception as exc:
        log(f"ℹ️ Native Ollama at http://localhost:11434 was not reached: {exc}")

    # 3. Start Docker Compose Stack
    log(
        "📦 Starting Docker Compose services (API, UI, OTel Collector, Prometheus, Tempo, Grafana)..."
    )
    res = subprocess.run(["docker", "compose", "up", "-d", "--build"], check=False)
    if res.returncode != 0:
        log("❌ Failed to start Docker Compose stack.")
        return 1

    # 4. Wait for Service Readiness
    log("⏳ Verifying service health and readiness...")
    wait_for_url(
        "http://localhost:8000/health", timeout_seconds=45.0, description="FastAPI Gateway"
    )
    wait_for_url(
        "http://localhost:8501/_stcore/health", timeout_seconds=45.0, description="Streamlit UI"
    )
    wait_for_url(
        "http://localhost:9090/-/healthy", timeout_seconds=30.0, description="Prometheus Engine"
    )
    wait_for_url(
        "http://localhost:3200/ready", timeout_seconds=30.0, description="Grafana Tempo Tracing"
    )
    wait_for_url(
        "http://localhost:3000/api/health", timeout_seconds=30.0, description="Grafana Dashboards"
    )

    # 5. Summary and URLs
    log("==================================================================")
    log("🎉 PLATFORM & OBSERVABILITY SERVICES READY")
    log("==================================================================")
    print("  • Streamlit Web UI:        http://localhost:8501")
    print("  • FastAPI API & Docs:      http://localhost:8000/docs")
    print("  • Grafana Dashboards:      http://localhost:3000 (UID: healthcare-observability)")
    print("  • Prometheus Metrics:      http://localhost:9090")
    print("  • Tempo Tracing:           http://localhost:3200")
    print("  • OTLP Exporter Endpoints: http://localhost:4318 (HTTP), localhost:4317 (gRPC)")
    log("==================================================================")
    log("Primary demonstration query:")
    log(
        '"Find the best pediatric dentists in Houston, Texas, and research pediatric dental anxiety."'
    )
    log("==================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
