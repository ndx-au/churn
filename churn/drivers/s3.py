"""S3 / GCS Driver (M002.003).

Functional when boto3 + [s3] extra present. Supports anonymous (UNSIGNED) access to public buckets
for smoke testing — especially useful with Backblaze B2 public buckets.

Falls back to informative stub if boto3 not available.

Config can come from:
- Passed dict to get_driver(..., config)
- CHURN_S3_* env vars (via ChurnSettings)
- Explicit keys: endpoint_url, region, aws_access_key_id, etc.

For anon public bucket tests (recommended for B2), pass {"anonymous": True} or omit keys.
"""

from __future__ import annotations

from typing import Any

from churn.drivers.base import FetchedContent, SourceDriver, SourceItem


class S3Driver(SourceDriver):
    name = "s3"
    description = "S3 / GCS compatible object storage (boto3)."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._boto = None
        self._client = None
        self._init_error: str | None = None
        cfg = dict(self.config or {})
        self.config = cfg

        # Merge with global settings if not provided in per-driver config
        try:
            from churn.config import settings
            if not cfg.get("endpoint_url") and settings.s3_endpoint:
                cfg["endpoint_url"] = settings.s3_endpoint
            if not cfg.get("region") and settings.s3_region:
                cfg["region"] = settings.s3_region
            if not cfg.get("aws_access_key_id") and settings.s3_access_key_id:
                cfg["aws_access_key_id"] = settings.s3_access_key_id
            if not cfg.get("aws_secret_access_key") and settings.s3_secret_access_key:
                cfg["aws_secret_access_key"] = settings.s3_secret_access_key
        except Exception:
            pass

        try:
            import boto3
            from botocore import UNSIGNED
            from botocore.client import Config

            self._boto = boto3

            access_key = cfg.get("aws_access_key_id") or cfg.get("access_key_id")
            secret_key = cfg.get("aws_secret_access_key") or cfg.get("secret_access_key")
            region = cfg.get("region") or "us-east-1"
            endpoint = cfg.get("endpoint_url") or cfg.get("endpoint")

            force_anon = cfg.get("anonymous", False) or not access_key

            client_kwargs = {
                "region_name": region,
            }
            if endpoint:
                client_kwargs["endpoint_url"] = endpoint

            if not force_anon:
                if access_key:
                    client_kwargs["aws_access_key_id"] = access_key
                if secret_key:
                    client_kwargs["aws_secret_access_key"] = secret_key
            else:
                # Anonymous / public bucket (ideal for B2 public bucket smoke tests)
                client_kwargs["config"] = Config(signature_version=UNSIGNED)

            self._client = boto3.client("s3", **client_kwargs)
        except Exception as exc:
            self._init_error = str(exc)

    def list_items(self, query: str | None = None, **kwargs: Any) -> list[SourceItem]:
        if not self._client:
            msg = self._init_error or "boto3 not installed (pip install churn[s3])"
            raise RuntimeError(f"S3 driver unavailable: {msg}")
        if not query:
            return []
        parts = query.strip("/").split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        items: list[SourceItem] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                items.append(
                    SourceItem(
                        id=key,
                        path_or_uri=f"s3://{bucket}/{key}",
                        size=obj.get("Size"),
                        metadata={"bucket": bucket, "key": key, "etag": obj.get("ETag")},
                    )
                )
        return items

    def fetch_item(self, item: SourceItem) -> FetchedContent:
        if not self._client:
            raise NotImplementedError("S3 driver requires 'boto3' (install with [s3]).")
        # Parse s3://bucket/key
        uri = item.path_or_uri
        if uri.startswith("s3://"):
            rest = uri[5:]
            if "/" not in rest:
                raise ValueError(f"Invalid S3 URI (missing object key): {uri}")
            bucket, key = rest.split("/", 1)
        else:
            bucket = item.metadata.get("bucket")
            key = item.metadata.get("key") or item.id
            if not bucket or not key:
                raise ValueError(f"Cannot resolve S3 bucket/key from item: {item!r}")
        obj = self._client.get_object(Bucket=bucket, Key=key)
        data = obj["Body"].read()
        import hashlib

        sha = hashlib.sha256(data).hexdigest()
        raw_mime = obj.get("ContentType")
        mime = raw_mime.split(";", 1)[0].strip() if raw_mime else None
        return FetchedContent(item=item, content=data, mime=mime, sha256=sha)
