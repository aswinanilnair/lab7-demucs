#!/bin/sh
#
# Deletes the GKE cluster created for this lab, which stops its charges.
# All songs and tracks in the cluster are lost. The images on Docker Hub
# are not affected.
#
# Usage: ./teardown-gke.sh [cluster] [zone]
#
set -e

CLUSTER=${1:-mykube}
ZONE=${2:-us-central1-a}

#
# Only continue if kubectl points at the cluster being deleted, so this
# can't run against your local cluster or a different GKE cluster.
#
CONTEXT=$(kubectl config current-context 2>/dev/null || true)
case "$CONTEXT" in
  gke_*_"$ZONE"_"$CLUSTER") ;;
  *)
    echo "kubectl context is '$CONTEXT', not GKE cluster $CLUSTER in $ZONE." >&2
    echo "Run: gcloud container clusters get-credentials $CLUSTER --zone $ZONE" >&2
    exit 1
    ;;
esac
PROJECT=${CONTEXT#gke_}
PROJECT=${PROJECT%_"$ZONE"_"$CLUSTER"}

#
# Delete the ingress and console service first and wait for them. That removes
# Google's load balancers, which could otherwise be left behind and keep costing money.
#
echo "Deleting the ingress, console service and their load balancers..."
kubectl delete -f gke/rest-ingress.yaml -f gke/rustfs-console-lb.yaml --ignore-not-found --timeout=10m

# gcloud asks you to confirm before deleting the cluster
gcloud container clusters delete "$CLUSTER" --zone "$ZONE" --project "$PROJECT"

kubectl config use-context docker-desktop || echo "Local context docker-desktop not found."
