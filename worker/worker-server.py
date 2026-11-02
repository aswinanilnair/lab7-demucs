#!/usr/bin/env python3

import json
import os
import platform
import subprocess
import sys
import tempfile

import boto3
import redis
import requests
from botocore.client import Config
from botocore.exceptions import ClientError

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
s3Endpoint = os.getenv("S3_ENDPOINT") or "http://localhost:9000"
s3AccessKey = os.getenv("S3_ACCESS_KEY") or "rootuser"
s3SecretKey = os.getenv("S3_SECRET_KEY") or "rootpass123"

QUEUE_KEY = "toWorker"
QUEUE_BUCKET = "queue"
OUTPUT_BUCKET = "output"
PARTS = ["bass", "drums", "vocals", "other"]
DEFAULT_MODEL = "htdemucs"

## blpop waits indefinitely for work, so the default socket timeout can't apply
redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0, socket_timeout=None)
s3 = boto3.client("s3",
                  endpoint_url=s3Endpoint,
                  aws_access_key_id=s3AccessKey,
                  aws_secret_access_key=s3SecretKey,
                  region_name="us-east-1",
                  config=Config(signature_version="s3v4",
                                s3={"addressing_style": "path"}))

infoKey = "{}.worker.info".format(platform.node())
debugKey = "{}.worker.debug".format(platform.node())

def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout, flush=True)
    redisClient.lpush('logging', f"{key}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout, flush=True)
    redisClient.lpush('logging', f"{key}:{message}")

def ensure_bucket(bucket):
    try:
        s3.create_bucket(Bucket=bucket)
    except ClientError as exp:
        if exp.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise

def separate(songhash, model):
    with tempfile.TemporaryDirectory() as workdir:
        source = os.path.join(workdir, f"{songhash}.mp3")
        output = os.path.join(workdir, "output")
        s3.download_file(QUEUE_BUCKET, f"{songhash}.mp3", source)
        log_debug(f"Downloaded {songhash}, running demucs with model {model}")

        subprocess.run(
            ["python3", "-m", "demucs.separate", "-n", model, "-d", "cpu",
             "--mp3", "--out", output, source],
            check=True)

        for part in PARTS:
            s3.upload_file(os.path.join(output, model, songhash, f"{part}.mp3"),
                           OUTPUT_BUCKET, f"{songhash}-{part}.mp3")
            log_debug(f"Uploaded {songhash}-{part}.mp3")
    s3.delete_object(Bucket=QUEUE_BUCKET, Key=f"{songhash}.mp3")

##
## The callback is allowed to fail, e.g. a url of localhost won't reach
## anything from inside a pod.
##
def send_callback(callback):
    if not callback or not callback.get("url"):
        return
    try:
        requests.post(callback["url"], json=callback.get("data"), timeout=10)
    except requests.RequestException as exp:
        log_debug(f"Callback to {callback['url']} failed: {exp}")

def main():
    ensure_bucket(QUEUE_BUCKET)
    ensure_bucket(OUTPUT_BUCKET)
    log_info("Worker ready")
    while True:
        work = redisClient.blpop(QUEUE_KEY, timeout=0)
        try:
            job = json.loads(work[1])
            songhash = job["hash"]
            log_info(f"Starting {songhash}")
            separate(songhash, job.get("model") or DEFAULT_MODEL)
            log_info(f"Finished {songhash}")
            send_callback(job.get("callback"))
        except Exception as exp:
            log_info(f"Failed to process {work[1]}: {exp}")

if __name__ == "__main__":
    main()
