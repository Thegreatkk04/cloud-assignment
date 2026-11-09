#!/usr/bin/env bash
# make up: cluster + storage + images + deploy, from a fresh clone.
set -euo pipefail
[ -f .env ] || { echo "copy .env.example to .env first"; exit 1; }
set -a; source .env; set +a
k3d cluster list | grep -q cloud-mini || k3d cluster create --config cluster/k3d.yaml
kubectl apply -f k8s/00-namespaces.yaml
kubectl apply -f k8s/seaweedfs.yaml
kubectl -n data rollout status deploy/seaweedfs --timeout=180s
for ns in pipeline app; do
  kubectl -n $ns create secret generic s3-credentials \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -
done
S3_ENDPOINT=http://localhost:8333 python scripts/init_storage.py
docker build -f worker/Dockerfile -t cloud-mini/worker:v1 .
docker build -f service/Dockerfile -t cloud-mini/service:v1 .
k3d image import -c cloud-mini cloud-mini/worker:v1 cloud-mini/service:v1
bash scripts/deploy.sh
