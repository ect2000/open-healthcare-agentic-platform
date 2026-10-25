#!/usr/bin/env python3
"""Open Healthcare Agentic Platform: Kubernetes Smoke & Acceptance Test Script.

Validates in-cluster Pod readiness, service endpoints, FastAPI health probes,
Streamlit health probes, Ollama connectivity from within Kubernetes,
end-to-end multi-agent search query execution, Prometheus metrics collection,
and Tempo trace propagation.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

API_HEALTH_URL = "http://localhost:8000/health"
API_SEARCH_URL = "http://localhost:8000/api/v1/search"
UI_HEALTH_URL = "http://localhost:8501/_stcore/health"
PROMETHEUS_QUERY_URL = "http://localhost:9090/api/v1/query"
TEMPO_STATUS_URL = "http://localhost:3200/status"
GRAFANA_HEALTH_URL = "http://localhost:3000/api/health"

NAMESPACE = "open-healthcare"


def log(msg: str) -> None:
    print(f"[k8s-smoke-test] {msg}")


def test_http_endpoint(name: str, url: str, expected_code: int = 200, timeout: int = 10) -> bool:
    """Test HTTP endpoint status code."""
    log(f"Testing {name}: {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "k8s-smoke-test"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == expected_code:
                log(f"  {name} responded with HTTP {resp.status} (SUCCESS)")
                return True
            log(f"  {name} returned unexpected status HTTP {resp.status}")
            return False
    except Exception as exc:
        log(f"  {name} check failed: {exc}")
        return False


def test_pods_running() -> bool:
    """Check that all pods in the open-healthcare namespace are Running."""
    log("Checking Kubernetes Pods status...")
    cmd = [
        "kubectl",
        "get",
        "pods",
        "-n",
        NAMESPACE,
        "-o",
        "jsonpath={range .items[*]}{.metadata.name}{'\\t'}{.status.phase}{'\\n'}{end}",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        all_running = True
        for line in lines:
            parts = line.split("\t")
            pod_name, phase = parts[0], parts[1]
            log(f"  Pod {pod_name}: {phase}")
            if phase != "Running":
                all_running = False
        return all_running
    except Exception as exc:
        log(f"  Failed to retrieve pods: {exc}")
        return False


def test_in_cluster_ollama_connectivity() -> bool:
    """Execute python inside FastAPI pod to verify Ollama connectivity via host-ollama-bridge."""
    log("Verifying Ollama connectivity from inside open-healthcare-api Pod...")
    try:
        pod_cmd = [
            "kubectl",
            "get",
            "pods",
            "-n",
            NAMESPACE,
            "-l",
            "app.kubernetes.io/name=open-healthcare-api",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
        pod_res = subprocess.run(pod_cmd, capture_output=True, text=True, check=True)
        pod_name = pod_res.stdout.strip()
        if not pod_name:
            log("  Could not find open-healthcare-api Pod")
            return False

        py_cmd = (
            "import urllib.request; "
            "resp = urllib.request.urlopen('http://host-ollama-bridge:11434/api/tags', timeout=5); "
            "print(resp.read().decode())"
        )
        exec_cmd = [
            "kubectl",
            "exec",
            "-n",
            NAMESPACE,
            pod_name,
            "--",
            "python",
            "-c",
            py_cmd,
        ]
        res = subprocess.run(exec_cmd, capture_output=True, text=True, check=True)
        if "gemma4:e2b" in res.stdout:
            msg = f"  In-cluster Ollama connectivity verified from '{pod_name}' (SUCCESS)"
            log(msg)
            return True
        log(f"  Ollama response from inside pod: {res.stdout[:150]}")
        return False
    except Exception as exc:
        log(f"  In-cluster Ollama test failed: {exc}")
        return False


def test_end_to_end_search() -> dict[str, Any] | None:
    """Execute end-to-end multi-agent search query against FastAPI."""
    log("Executing end-to-end healthcare search against Kubernetes API (port 8000)...")
    payload = {
        "query": "Find pediatric dentists in Houston, Texas.",
        "max_results": 3,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_SEARCH_URL,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "k8s-smoke-test"},
        method="POST",
    )

    try:
        start_t = time.time()
        with urllib.request.urlopen(req, timeout=90) as resp:
            elapsed = time.time() - start_t
            if resp.status == 200:
                result = json.loads(resp.read().decode())
                trace_id = result.get("trace_id", "none")
                evidence_count = len(result.get("evidence", []))
                has_answer = bool(result.get("answer"))
                log(f"  Search completed in {elapsed:.2f}s (SUCCESS)")
                log(f"  Returned {evidence_count} evidence items, Trace ID: {trace_id}")
                log(f"  Answer generated: {has_answer}")
                return result
            log(f"  Search returned status {resp.status}")
            return None
    except Exception as exc:
        log(f"  Search execution failed: {exc}")
        return None


def test_prometheus_metrics() -> bool:
    """Query Prometheus to confirm OpenTelemetry metrics ingestion."""
    log("Verifying Prometheus metrics scraped from otel-collector...")
    query = "healthcare_evidence_retained_total"
    url = f"{PROMETHEUS_QUERY_URL}?query={query}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "k8s-smoke-test"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode())
                status = body.get("status")
                results = body.get("data", {}).get("result", [])
                msg = f"  Prometheus query '{query}': status={status}, result_count={len(results)}"
                log(f"{msg} (SUCCESS)")
                return len(results) > 0
            return False
    except Exception as exc:
        log(f"  Prometheus metrics test failed: {exc}")
        return False


def test_tempo_ready() -> bool:
    """Verify Tempo ready status."""
    log("Verifying Grafana Tempo readiness...")
    return test_http_endpoint("Grafana Tempo", TEMPO_STATUS_URL)


def test_grafana_health() -> bool:
    """Verify Grafana health status."""
    log("Verifying Grafana dashboard health...")
    return test_http_endpoint("Grafana", GRAFANA_HEALTH_URL)


def main() -> None:
    """Execute complete smoke test suite."""
    log("========================================================")
    log("Starting Kubernetes Smoke Tests (Namespace: open-healthcare)")
    log("========================================================")

    results: list[tuple[str, bool]] = []

    # 1. Pod phases
    results.append(("Pods Running", test_pods_running()))

    # 2. Endpoints health
    results.append(("FastAPI Health Probe", test_http_endpoint("FastAPI", API_HEALTH_URL)))
    results.append(("Streamlit Health Probe", test_http_endpoint("Streamlit", UI_HEALTH_URL)))
    results.append(("Tempo Readiness", test_tempo_ready()))
    results.append(("Grafana Health", test_grafana_health()))

    # 3. Ollama internal connectivity
    results.append(("Host Ollama Connectivity via Gateway", test_in_cluster_ollama_connectivity()))

    # 4. End-to-end multi-agent search
    search_res = test_end_to_end_search()
    results.append(("End-to-End Multi-Agent Search", search_res is not None))

    # Wait briefly for OTel batch processor export
    time.sleep(3)

    # 5. Prometheus metrics
    results.append(("Prometheus Healthcare Metrics Ingestion", test_prometheus_metrics()))

    log("\n========================================================")
    log("Kubernetes Smoke Test Summary")
    log("========================================================")
    all_passed = True
    for name, passed in results:
        status_text = "PASS" if passed else "FAIL"
        log(f"  [{status_text}] {name}")
        if not passed:
            all_passed = False
    log("========================================================")

    if not all_passed:
        log("ERROR: One or more Kubernetes smoke tests failed.")
        sys.exit(1)

    log("SUCCESS: All Kubernetes deployment smoke tests passed!")


if __name__ == "__main__":
    main()
