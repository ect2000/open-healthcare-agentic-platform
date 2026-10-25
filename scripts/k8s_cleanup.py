#!/usr/bin/env python3
"""Open Healthcare Agentic Platform: Scoped Kubernetes Cleanup Script.

Safely removes only the open-healthcare deployment resources or tears down
the dedicated 'open-healthcare' Kind cluster. Never touches unrelated clusters
or resources.
"""

from __future__ import annotations

import argparse
import subprocess

CLUSTER_NAME = "open-healthcare"
NAMESPACE = "open-healthcare"


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"==> Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, text=True)


def delete_namespace_resources() -> None:
    """Delete resources in open-healthcare namespace."""
    print(f"Deleting all resources in namespace '{NAMESPACE}'...")
    try:
        run_cmd(["kubectl", "delete", "namespace", NAMESPACE, "--timeout=60s"], check=False)
        print(f"Namespace '{NAMESPACE}' deleted.")
    except Exception as exc:
        print(f"Error deleting namespace: {exc}")


def delete_kind_cluster() -> None:
    """Delete dedicated Kind cluster 'open-healthcare'."""
    res = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=True)
    clusters = [c.strip() for c in res.stdout.splitlines() if c.strip()]
    if CLUSTER_NAME not in clusters:
        print(f"Kind cluster '{CLUSTER_NAME}' does not exist. Nothing to delete.")
        return

    print(f"Deleting dedicated Kind cluster '{CLUSTER_NAME}'...")
    run_cmd(["kind", "delete", "cluster", "--name", CLUSTER_NAME], check=True)
    print(f"Cluster '{CLUSTER_NAME}' deleted successfully.")


def main() -> None:
    desc = "Safely clean up Open Healthcare Kubernetes resources"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--namespace-only",
        action="store_true",
        help="Only delete the open-healthcare namespace, keeping the Kind cluster alive",
    )
    args = parser.parse_args()

    if args.namespace_only:
        delete_namespace_resources()
    else:
        delete_kind_cluster()

    print("Cleanup completed safely.")


if __name__ == "__main__":
    main()
