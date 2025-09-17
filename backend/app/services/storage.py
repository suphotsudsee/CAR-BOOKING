"""S3-compatible storage helpers for managing uploaded media files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

try:  # pragma: no cover - optional dependency
    import boto3
    from botocore.client import BaseClient
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ModuleNotFoundError:  # pragma: no cover - testing fallback
    boto3 = None
    BaseClient = Any  # type: ignore[assignment]
    Config = object  # type: ignore[assignment]

    class ClientError(Exception):
        """Fallback error matching botocore's interface when unavailable."""

        def __init__(self, error_response: dict[str, Any], operation_name: str) -> None:
            super().__init__(str(error_response))
            self.response = error_response
            self.operation_name = operation_name


class StorageError(RuntimeError):
    """Base error for storage related operations."""


class ObjectNotFoundError(StorageError):
    """Raised when a storage object cannot be located."""


def _normalise_prefix(prefix: str) -> str:
    return prefix.strip("/")


def _parse_int(value: Any) -> Optional[int]:
    """Safely convert ``value`` to ``int`` when possible."""

    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class StoredImage:
    """Descriptor for an image stored in object storage."""

    key: str
    url: str
    content_type: str
    width: Optional[int]
    height: Optional[int]
    size: Optional[int]
    preview_key: Optional[str]
    preview_url: Optional[str]
    preview_width: Optional[int]
    preview_height: Optional[int]
    expires_in: int
    metadata: dict[str, str]


class S3StorageService:
    """Wrapper around a boto3 client for simplified S3 operations."""

    def __init__(
        self,
        *,
        client: BaseClient,
        bucket: str,
        base_prefix: str = "",
        default_expiration: int = 900,
        object_acl: Optional[str] = "private",
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._base_prefix = _normalise_prefix(base_prefix)
        self._default_expiration = default_expiration
        self._object_acl = object_acl

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def default_expiration(self) -> int:
        return self._default_expiration

    def build_object_key(self, *, prefix: str, extension: str) -> str:
        """Return a unique object key under ``prefix`` with ``extension``."""

        normalised_prefix = _normalise_prefix(prefix)
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        parts = [self._base_prefix, normalised_prefix, date_path]
        path = "/".join(part for part in parts if part)
        suffix = extension.lstrip(".")
        return f"{path}/{uuid4().hex}.{suffix}" if path else f"{uuid4().hex}.{suffix}"

    async def upload_file(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Optional[dict[str, Optional[str]]] = None,
        cache_control: Optional[str] = None,
    ) -> None:
        """Upload ``content`` to S3 under ``key`` with metadata."""

        metadata_payload = {
            str(k).lower(): str(v)
            for k, v in (metadata or {}).items()
            if v not in (None, "")
        }

        def _put_object() -> None:
            params: dict[str, Any] = {
                "Bucket": self._bucket,
                "Key": key,
                "Body": content,
                "ContentType": content_type,
                "Metadata": metadata_payload,
            }
            if self._object_acl:
                params["ACL"] = self._object_acl
            if cache_control:
                params["CacheControl"] = cache_control
            self._client.put_object(**params)

        try:
            await run_in_threadpool(_put_object)
        except ClientError as exc:  # pragma: no cover - boto3 provides error details
            raise StorageError(f"Failed to upload object '{key}': {exc}") from exc

    async def delete_file(self, key: str) -> None:
        """Remove ``key`` from the bucket if it exists."""

        def _delete() -> None:
            self._client.delete_object(Bucket=self._bucket, Key=key)

        try:
            await run_in_threadpool(_delete)
        except ClientError as exc:  # pragma: no cover - boto3 provides error details
            raise StorageError(f"Failed to delete object '{key}': {exc}") from exc

    async def generate_presigned_url(
        self, key: str, *, expires_in: Optional[int] = None
    ) -> str:
        """Return a presigned download URL for ``key``."""

        expiration = expires_in or self._default_expiration

        def _generate() -> str:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expiration,
            )

        try:
            return await run_in_threadpool(_generate)
        except ClientError as exc:  # pragma: no cover
            raise StorageError(
                f"Failed to generate signed URL for '{key}': {exc}"
            ) from exc

    async def get_object_metadata(self, key: str) -> dict[str, str]:
        """Return object metadata for ``key``."""

        def _head() -> dict[str, Any]:
            return self._client.head_object(Bucket=self._bucket, Key=key)

        try:
            response = await run_in_threadpool(_head)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey"}:
                raise ObjectNotFoundError(f"Object '{key}' not found") from exc
            raise StorageError(f"Failed to inspect object '{key}': {exc}") from exc

        metadata = {k.lower(): v for k, v in response.get("Metadata", {}).items()}
        content_type = response.get("ContentType")
        if content_type:
            metadata.setdefault("content-type", content_type)
        if "ContentLength" in response:
            metadata.setdefault("content-length", str(response["ContentLength"]))
        return metadata

    async def describe_image(
        self, key: str, *, expires_in: Optional[int] = None
    ) -> StoredImage:
        """Return a :class:`StoredImage` populated from metadata for ``key``."""

        metadata = await self.get_object_metadata(key)
        url = await self.generate_presigned_url(key, expires_in=expires_in)
        preview_key = metadata.get("preview-key")
        preview_url = None
        if preview_key:
            try:
                preview_url = await self.generate_presigned_url(
                    preview_key, expires_in=expires_in
                )
            except ObjectNotFoundError:
                preview_url = None

        return StoredImage(
            key=key,
            url=url,
            content_type=metadata.get("content-type", "application/octet-stream"),
            width=_parse_int(metadata.get("image-width")),
            height=_parse_int(metadata.get("image-height")),
            size=_parse_int(metadata.get("content-length")),
            preview_key=preview_key,
            preview_url=preview_url,
            preview_width=_parse_int(metadata.get("preview-width")),
            preview_height=_parse_int(metadata.get("preview-height")),
            expires_in=expires_in or self._default_expiration,
            metadata=metadata,
        )

    @classmethod
    def from_settings(cls) -> "S3StorageService":
        """Create a storage service using global application settings."""

        if boto3 is None:  # pragma: no cover - requires optional dependency
            msg = "boto3 is required to build a storage client from settings"
            raise StorageError(msg)

        session = boto3.session.Session(
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION_NAME,
        )

        config_kwargs: dict[str, Any] = {}
        if settings.S3_SIGNATURE_VERSION:
            config_kwargs["signature_version"] = settings.S3_SIGNATURE_VERSION
        if settings.S3_FORCE_PATH_STYLE:
            config_kwargs.setdefault("s3", {})["addressing_style"] = "path"

        config = Config(**config_kwargs) if config_kwargs else None
        client_kwargs: dict[str, Any] = {}
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        if config is not None:
            client_kwargs["config"] = config

        client = session.client("s3", **client_kwargs)
        return cls(
            client=client,
            bucket=settings.S3_BUCKET_NAME,
            base_prefix=settings.UPLOAD_DIR,
            default_expiration=settings.S3_URL_EXPIRATION,
        )


__all__ = [
    "ObjectNotFoundError",
    "S3StorageService",
    "StorageError",
    "StoredImage",
]
