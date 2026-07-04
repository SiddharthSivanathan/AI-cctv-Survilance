"""Object storage (S3 / MinIO) via boto3.

Provides a thin, typed wrapper used platform-wide for public assets (logos)
and later for camera snapshots, clips, and report PDFs. The bucket is created
on demand with a public-read policy so uploaded logos can be served directly.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("storage")


class StorageError(Exception):
    """Raised when an object storage operation fails."""


@lru_cache
def _client() -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def ensure_bucket() -> None:
    """Create the media bucket (idempotent) and apply a public-read policy.

    Safe to call on startup. Logs and returns on failure rather than crashing
    the API — storage being down should not prevent the control plane booting.
    """
    settings = get_settings()
    client = _client()
    try:
        existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
        if settings.s3_bucket not in existing:
            client.create_bucket(Bucket=settings.s3_bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{settings.s3_bucket}/public/*"],
                }
            ],
        }
        client.put_bucket_policy(Bucket=settings.s3_bucket, Policy=json.dumps(policy))
        logger.info("storage_bucket_ready", bucket=settings.s3_bucket)
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover - infra dependent
        logger.warning("storage_bucket_setup_failed", error=str(exc))


class ObjectStorage:
    """Use-case facing storage service (injected into services)."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def upload_public(self, fileobj: BinaryIO, *, key: str, content_type: str) -> str:
        """Upload an object under the public/ prefix and return its public URL."""
        object_key = f"public/{key}"
        try:
            _client().upload_fileobj(
                fileobj,
                self._settings.s3_bucket,
                object_key,
                ExtraArgs={"ContentType": content_type},
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Upload failed: {exc}") from exc
        return f"{self._settings.s3_public_base}/{self._settings.s3_bucket}/{object_key}"
