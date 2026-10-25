#!/usr/bin/env python3
"""Open Healthcare Agentic Platform: Local Kubernetes Deployment Script.

Automates Kind cluster setup, local image loading, Kustomize overlay deployment,
and rollout verification.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CLUSTER_NAME = "open-healthcare"
KIND_CONFIG = ROOT_DIR / "deploy" / "kubernetes" / "overlays" / "local" / "kind-config.yaml"
KUSTOMIZE_OVERLAY = ROOT_DIR / "deploy" / "kubernetes" / "overlays" / "local"
NAMESPACE = "open-healthcare"

IMAGES = [
    "open-healthcare-api:latest",
    "open-healthcare-ui:latest",
]


def run_cmd(
    cmd: list[str], check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    """Execute a shell command with real-time logging."""
    print(f"==> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, text=True, capture_output=capture_output)
    return result


def check_prerequisites() -> None:
    """Verify docker, kind, and kubectl are installed."""
    for tool in ["docker", "kind", "kubectl"]:
        try:
            cmd = [tool, "version", "--client"] if tool == "kubectl" else [tool, "--version"]
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            msg = f"Error: Required tool '{tool}' is not installed or not in PATH."
            print(msg, file=sys.stderr)
            sys.exit(1)
    print("Prerequisites verified: docker, kind, and kubectl are present.")


def check_host_ollama() -> bool:
    """Check if native Ollama is running on localhost:11434 with gemma4:e2b."""
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        if req.status == 200:
            data = json.loads(req.read().decode())
            model_names = [m.get("name", "") for m in data.get("models", [])]
            has_gemma = any("gemma4:e2b" in name for name in model_names)
            if has_gemma:
                print("Host Ollama verified: http://localhost:11434 (model: gemma4:e2b available).")
                return True
            else:
                warn = (
                    f"Warning: Ollama running on host, but gemma4:e2b not found in: {model_names}"
                )
                print(warn)
                return False
    except Exception as exc:
        print(f"Warning: Could not connect to host Ollama (http://localhost:11434): {exc}")
        return False
    return False


def get_docker_bridge_gateway() -> str:
    """Determine Kind bridge network gateway IP for host communication."""
    try:
        res = subprocess.run(
            ["docker", "network", "inspect", "kind", "-f", "{{(index .IPAM.Config 0).Gateway}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        gw = res.stdout.strip()
        if gw:
            return gw
    except Exception:
        pass
    return "172.18.0.1"


def cluster_exists() -> bool:
    """Check if the Kind cluster already exists."""
    res = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=True)
    clusters = [c.strip() for c in res.stdout.splitlines() if c.strip()]
    return CLUSTER_NAME in clusters


def create_kind_cluster() -> None:
    """Create Kind cluster if not already present."""
    if cluster_exists():
        print(f"Kind cluster '{CLUSTER_NAME}' already exists. Skipping cluster creation.")
        return

    print(f"Creating Kind cluster '{CLUSTER_NAME}' with configuration: {KIND_CONFIG}")
    run_cmd(["kind", "create", "cluster", "--name", CLUSTER_NAME, "--config", str(KIND_CONFIG)])
    print(f"Cluster '{CLUSTER_NAME}' created successfully.")


def build_and_load_images(build: bool = False) -> None:
    """Build and load application images into Kind cluster."""
    if build:
        print("Building open-healthcare-api:latest...")
        cmd_api = [
            "docker",
            "build",
            "-t",
            "open-healthcare-api:latest",
            "-f",
            "Dockerfile.api",
            ".",
        ]
        run_cmd(cmd_api, check=True)
        print("Building open-healthcare-ui:latest...")
        cmd_ui = ["docker", "build", "-t", "open-healthcare-ui:latest", "-f", "Dockerfile.ui", "."]
        run_cmd(cmd_ui, check=True)

    print("Loading container images into Kind cluster...")
    for img in IMAGES:
        print(f"Loading image {img} into Kind cluster '{CLUSTER_NAME}'...")
        run_cmd(["kind", "load", "docker-image", img, "--name", CLUSTER_NAME], check=True)
    print("All required images loaded into Kind.")


def deploy_manifests() -> None:
    """Apply Kustomize manifests to Kind cluster."""
    print(f"Applying Kustomize overlay: {KUSTOMIZE_OVERLAY}")
    run_cmd(["kubectl", "apply", "-k", str(KUSTOMIZE_OVERLAY)], check=True)
    print("Manifests applied successfully.")


def wait_for_rollouts() -> None:
    """Wait for all deployments in the namespace to become ready."""
    deployments = [
        "open-healthcare-api",
        "open-healthcare-ui",
        "otel-collector",
        "prometheus",
        "tempo",
        "grafana",
    ]
    print("Waiting for deployments rollout in namespace 'open-healthcare'...")
    for dep in deployments:
        print(f"Waiting for deployment/{dep}...")
        status_cmd = [
            "kubectl",
            "rollout",
            "status",
            f"deployment/{dep}",
            "-n",
            NAMESPACE,
            "--timeout=180s",
        ]
        run_cmd(status_cmd, check=True)
    print("All deployments are ready!")


def print_service_endpoints() -> None:
    """Display local browser access endpoints."""
    print("\n========================================================")
    print("Open Healthcare Platform - Kubernetes Deployment Active")
    print("========================================================")
    print("Namespace:         open-healthcare")
    print("FastAPI Service:   http://localhost:8000 (Docs: http://localhost:8000/docs)")
    print("Streamlit UI:      http://localhost:8501")
    print("Grafana:           http://localhost:3000 (Dashboards pre-provisioned)")
    print("Prometheus:        http://localhost:9090")
    print("Grafana Tempo:     http://localhost:3200")
    print("========================================================\n")


def main() -> None:
    """Main CLI entrypoint."""
    desc = "Deploy Open Healthcare Platform on Kind Kubernetes"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--build", action="store_true", help="Rebuild Docker images before loading into Kind"
    )
    parser.add_argument(
        "--skip-wait", action="store_true", help="Skip waiting for deployment rollouts"
    )
    args = parser.parse_args()

    check_prerequisites()
    check_host_ollama()
    create_kind_cluster()
    build_and_load_images(build=args.build)
    deploy_manifests()

    if not args.skip_wait:
        wait_for_rollouts()

    print_service_endpoints()


if __name__ == "__main__":
    main()
