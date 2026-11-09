"""Small helper around boto3 for the SeaweedFS S3 endpoint.

Env vars:
  S3_ENDPOINT            e.g. http://seaweedfs-s3.data.svc.cluster.local:8333
  AWS_ACCESS_KEY_ID      from the Kubernetes Secret
  AWS_SECRET_ACCESS_KEY  from the Kubernetes Secret
"""
import os

import boto3
from botocore.config import Config


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:8333"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )


def get_text(bucket, key):
    body = client().get_object(Bucket=bucket, Key=key)["Body"].read()
    return body.decode("utf-8")


def put_text(bucket, key, text):
    client().put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"))


def list_keys(bucket, prefix):
    out = []
    paginator = client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            out.append(obj["Key"])
    return sorted(out)


def download_dir(bucket, prefix, dest):
    """Download every object under prefix into the local folder dest."""
    os.makedirs(dest, exist_ok=True)
    c = client()
    for key in list_keys(bucket, prefix):
        rel = key[len(prefix):].lstrip("/")
        if not rel:
            continue
        path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        c.download_file(bucket, key, path)
    return dest
