#!/usr/bin/env bash
# Task 4: Deployment + Service + Ingress + HPA in namespace app.
set -euo pipefail
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml -f k8s/hpa.yaml
kubectl -n app rollout status deploy/parser --timeout=600s || true
kubectl -n app get deploy,svc,ingress,hpa,pods
