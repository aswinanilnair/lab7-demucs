#!/bin/sh
#
# You can use this script to launch Redis and RustFS on Kubernetes
# and forward their connections to your local computer. That means
# you can then work on your worker-server.py and rest-server.py
# on your local computer rather than pushing to Kubernetes with each change.
#
# To kill the port-forward processes us e.g. "ps augxww | grep port-forward"
# to identify the processes ids
#
kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

kubectl apply -f rustfs/rustfs.yaml

kubectl rollout status deployment/redis
kubectl rollout status deployment/rustfs

kubectl port-forward service/redis 6379:6379 &

kubectl port-forward service/rustfs 9000:9000 &
kubectl port-forward service/rustfs 9001:9001 &
