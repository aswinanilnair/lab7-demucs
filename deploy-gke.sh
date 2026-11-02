#!/bin/sh
#
# Same as deploy-all.sh, but uses the GKE load balancer as the ingress.
# Push the images first with "make push" in rest, worker and logs.
#
set -e

#
# Only continue if kubectl points at a GKE cluster, so that the GKE ingress
# can't replace the ingress of your local cluster.
#
CONTEXT=$(kubectl config current-context 2>/dev/null || true)
case "$CONTEXT" in
  gke_*) ;;
  *)
    echo "kubectl context is '$CONTEXT', not a GKE cluster." >&2
    echo "Run: gcloud container clusters get-credentials <cluster> --zone <zone>" >&2
    exit 1
    ;;
esac

kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

kubectl apply -f rustfs/rustfs.yaml
kubectl apply -f gke/rustfs-console-lb.yaml

kubectl apply -f rest/rest-deployment.yaml
kubectl apply -f rest/rest-service.yaml
kubectl apply -f gke/rest-ingress.yaml

kubectl apply -f logs/logs-deployment.yaml

kubectl apply -f worker/worker-deployment.yaml
