"""In-memory stub mimicking a subset of boto3's S3 client behaviour."""

from __future__ import annotations

from typing import Any

from app.services.storage import ClientError


class InMemoryS3Client:
    """Small stub of the S3 client surface used in unit tests."""

    def __init__(self) -> None:
        self._objects: dict[tuple[str, str], dict[str, Any]] = {}

    def put_object(self, **kwargs: Any) -> None:
        bucket = kwargs["Bucket"]
        key = kwargs["Key"]
        body: bytes = kwargs["Body"]
        content_type = kwargs.get("ContentType", "application/octet-stream")
        metadata = kwargs.get("Metadata", {}) or {}
        cache_control = kwargs.get("CacheControl")

        self._objects[(bucket, key)] = {
            "Body": body,
            "ContentType": content_type,
            "Metadata": {k.lower(): v for k, v in metadata.items()},
            "CacheControl": cache_control,
        }

    def delete_object(self, **kwargs: Any) -> None:
        bucket = kwargs["Bucket"]
        key = kwargs["Key"]
        self._objects.pop((bucket, key), None)

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        bucket = kwargs["Bucket"]
        key = kwargs["Key"]
        stored = self._objects.get((bucket, key))
        if stored is None:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")

        return {
            "ContentLength": len(stored["Body"]),
            "ContentType": stored["ContentType"],
            "Metadata": stored["Metadata"],
        }

    def generate_presigned_url(self, operation_name: str, **kwargs: Any) -> str:
        params = kwargs.get("Params", {})
        bucket = params.get("Bucket", "bucket")
        key = params.get("Key", "object")
        expires = kwargs.get("ExpiresIn", 0)
        return f"https://example.com/{bucket}/{key}?expires={expires}"


__all__ = ["InMemoryS3Client"]
