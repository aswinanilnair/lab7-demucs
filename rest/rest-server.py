#!/usr/bin/env python3

import base64
import binascii
import hashlib
import io
import json
import os
import platform
import sys

import boto3
import redis
from botocore.client import Config
from botocore.exceptions import ClientError
from flask import Flask, jsonify, request, send_file

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
TRACKS = {"bass.mp3", "drums.mp3", "vocals.mp3", "other.mp3"}
MODELS = {"htdemucs", "htdemucs_ft", "hdemucs_mmi"}
DEFAULT_MODEL = "htdemucs"

redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)
s3 = boto3.client("s3",
                  endpoint_url=s3Endpoint,
                  aws_access_key_id=s3AccessKey,
                  aws_secret_access_key=s3SecretKey,
                  region_name="us-east-1",
                  config=Config(signature_version="s3v4",
                                s3={"addressing_style": "path"}))

infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())

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

app = Flask(__name__)

##
## GKE's load balancer uses this route as its health check
##
@app.route('/', methods=['GET'])
def hello():
    return '<h1> Music Separation Server</h1><p> Use a valid endpoint </p>'

@app.route('/apiv1/separate', methods=['POST'])
def separate():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("mp3"), str):
        return jsonify({"reason": "Request must be JSON with a base64 encoded mp3"}), 400
    model = body.get("model") or DEFAULT_MODEL
    if model not in MODELS:
        return jsonify({"reason": f"Unknown model, use one of {sorted(MODELS)}"}), 400
    try:
        mp3 = base64.b64decode(body["mp3"], validate=True)
    except binascii.Error:
        return jsonify({"reason": "mp3 is not valid base64"}), 400

    songhash = hashlib.sha224(mp3).hexdigest()
    s3.put_object(Bucket=QUEUE_BUCKET, Key=f"{songhash}.mp3", Body=mp3)
    redisClient.lpush(QUEUE_KEY, json.dumps({
        "hash": songhash,
        "model": model,
        "callback": body.get("callback"),
    }))
    log_info(f"Enqueued {songhash} with model {model}")
    return jsonify({"hash": songhash, "reason": "Song enqueued for separation"})

@app.route('/apiv1/queue', methods=['GET'], strict_slashes=False)
def queue():
    entries = redisClient.lrange(QUEUE_KEY, 0, -1)
    return jsonify({"queue": [json.loads(entry)["hash"] for entry in entries]})

@app.route('/apiv1/track/<songhash>/<track>', methods=['GET'])
def track(songhash, track):
    if track not in TRACKS:
        return jsonify({"reason": f"Unknown track, use one of {sorted(TRACKS)}"}), 404
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f"{songhash}-{track}")
    except ClientError as exp:
        if exp.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return jsonify({"reason": "Track not found"}), 404
        raise
    return send_file(io.BytesIO(obj["Body"].read()),
                     mimetype="audio/mpeg",
                     as_attachment=True,
                     download_name=f"{songhash}-{track}")

@app.route('/apiv1/remove/<songhash>/<track>', methods=['GET', 'DELETE'])
def remove(songhash, track):
    if track not in TRACKS:
        return jsonify({"reason": f"Unknown track, use one of {sorted(TRACKS)}"}), 404
    s3.delete_object(Bucket=OUTPUT_BUCKET, Key=f"{songhash}-{track}")
    log_info(f"Removed {songhash}-{track}")
    return jsonify({"hash": songhash, "track": track, "reason": "Track removed"})

if __name__ == "__main__":
    ensure_bucket(QUEUE_BUCKET)
    ensure_bucket(OUTPUT_BUCKET)
    app.run(host="0.0.0.0", port=5000)
