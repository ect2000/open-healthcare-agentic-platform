"""Tests for Kubernetes deployment manifests and lifecycle scripts."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT_DIR / "deploy" / "kubernetes" / "base"
LOCAL_OVERLAY_DIR = ROOT_DIR / "deploy" / "kubernetes" / "overlays" / "local"


def test_kubernetes_manifest_directories_exist() -> None:
    """Verify standard deploy/kubernetes directory structure."""
    assert BASE_DIR.is_dir()
    assert LOCAL_OVERLAY_DIR.is_dir()
    assert (BASE_DIR / "kustomization.yaml").is_file()
    assert (LOCAL_OVERLAY_DIR / "kustomization.yaml").is_file()
    assert (LOCAL_OVERLAY_DIR / "kind-config.yaml").is_file()


def test_base_kustomize_manifest_validity() -> None:
    """Validate deploy/kubernetes/base renders valid manifests via kubectl or kustomize."""
    kubectl = shutil.which("kubectl")
    if not kubectl:
        pytest.skip("kubectl not installed in test environment")

    res = subprocess.run(
        [kubectl, "kustomize", str(BASE_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"kubectl kustomize base failed: {res.stderr}"
    assert "open-healthcare-api" in res.stdout
    assert "open-healthcare-ui" in res.stdout
    assert "otel-collector" in res.stdout
    assert "prometheus" in res.stdout
    assert "tempo" in res.stdout
    assert "grafana" in res.stdout


def test_local_overlay_kustomize_manifest_validity() -> None:
    """Validate deploy/kubernetes/overlays/local renders valid manifests with patches."""
    kubectl = shutil.which("kubectl")
    if not kubectl:
        pytest.skip("kubectl not installed in test environment")

    res = subprocess.run(
        [kubectl, "kustomize", str(LOCAL_OVERLAY_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"kubectl kustomize local overlay failed: {res.stderr}"
    assert "NodePort" in res.stdout
    assert "host-ollama-bridge" in res.stdout
    assert "30080" in res.stdout
    assert "30851" in res.stdout


def test_k8s_scripts_syntax_and_import() -> None:
    """Verify Kubernetes management scripts are valid Python modules."""
    for script_name in ["k8s_deploy.py", "k8s_smoke_test.py", "k8s_cleanup.py"]:
        script_path = ROOT_DIR / "scripts" / script_name
        assert script_path.is_file(), f"Script {script_name} missing"
        res = subprocess.run(
            ["python3", "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, f"Syntax error in {script_name}: {res.stderr}"
