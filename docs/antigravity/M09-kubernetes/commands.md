# Milestone M9: Executed Commands & Raw Outputs

## 1. Storage Diagnosis & Cleanup
```bash
# Host disk space before cleanup
df -h
# Output: Available: 9.8 GiB (98% capacity on /System/Volumes/Data)

# Docker builder cache inspection
docker builder du
# Output: Total: 16.65 GB (15.03 GB reclaimable private build cache)

# Targeted build cache cleanup
docker builder prune -f
# Output: Reclaimed 14.99 GB

# Host disk space after cleanup
df -h
# Output: Available: 26 GiB (94% capacity on /System/Volumes/Data)
```

## 2. Kubernetes Manifest Validation
```bash
kubectl kustomize deploy/kubernetes/base
kubectl kustomize deploy/kubernetes/overlays/local
# Output: Successful validation, manifests compiled without error.
```

## 3. Deployment to Kind
```bash
uv run python scripts/k8s_deploy.py
# Output:
# Prerequisites verified: docker, kind, and kubectl are present.
# Host Ollama verified: http://localhost:11434 (model: gemma4:e2b available).
# Kind cluster 'open-healthcare' created.
# Container images loaded into Kind.
# Kustomize overlay applied.
# All deployments successfully rolled out!
```

## 4. Smoke & Acceptance Verification
```bash
uv run python scripts/k8s_smoke_test.py
# Output:
# [PASS] Pods Running
# [PASS] FastAPI Health Probe
# [PASS] Streamlit Health Probe
# [PASS] Tempo Readiness
# [PASS] Grafana Health
# [PASS] Host Ollama Connectivity via Gateway
# [PASS] End-to-End Multi-Agent Search
# [PASS] Prometheus Healthcare Metrics Ingestion
# SUCCESS: All Kubernetes deployment smoke tests passed!
```
