from __future__ import annotations

import hashlib
import mimetypes
import re
from typing import Any

from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from flow_api.infrastructure.models.intake import StoredObject

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ImmutableObjectConflictError(RuntimeError):
    """An existing content-addressed key does not contain the expected bytes."""


class ImmutableObjectNotFoundError(FileNotFoundError):
    """A content-addressed object does not exist."""


class ObjectStore:
    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put_immutable(self, content: bytes, filename: str) -> StoredObject:
        sha256 = hashlib.sha256(content).hexdigest()
        object_key = self.object_key_for_sha(sha256)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        try:
            metadata = self._client.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status != 404:
                raise
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                Metadata={"original-filename": filename, "sha256": sha256},
            )
        else:
            self._validate_existing_object(object_key, sha256, len(content), metadata)

        return StoredObject(
            sha256=sha256,
            object_key=object_key,
            size_bytes=len(content),
            content_type=content_type,
        )

    @staticmethod
    def object_key_for_sha(sha256: str) -> str:
        if not SHA256_PATTERN.fullmatch(sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        return f"raw/{sha256[:2]}/{sha256}"

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> tuple[str, bool]:
        """§7.1 显式 write_if_absent Protocol。

        返回 (sha256, created)。`created=True` 表示本次写入了；`False` 表示已存在
        且字节级一致。content_sha256 与实际内容字节必须一致，否则抛
        ImmutableObjectConflictError。
        """
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes")
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != content_sha256:
            raise ValueError(
                f"content_sha256 mismatch: declared {content_sha256} but actual {actual_sha256}"
            )
        if not SHA256_PATTERN.fullmatch(content_sha256):
            raise ValueError("content_sha256 must be 64 lowercase hexadecimal characters")
        try:
            self._client.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status != 404:
                raise
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                Metadata={"sha256": content_sha256},
            )
            return (content_sha256, True)
        # 已存在：与新内容字节级一致
        head = self._client.head_object(Bucket=self._bucket, Key=object_key)
        if head.get("ContentLength") != len(content) or head.get("Metadata", {}).get(
            "sha256"
        ) != content_sha256:
            raise ImmutableObjectConflictError(
                f"existing object {object_key} conflicts with content {content_sha256}"
            )
        existing = bytes(
            self._client.get_object(Bucket=self._bucket, Key=object_key)["Body"].read()
        )
        if hashlib.sha256(existing).hexdigest() != content_sha256:
            raise ImmutableObjectConflictError(
                f"existing object {object_key} bytes conflict with content {content_sha256}"
            )
        return (content_sha256, False)

    def read_by_sha(self, sha256: str) -> bytes:
        object_key = self.object_key_for_sha(sha256)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=object_key)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status == 404:
                raise ImmutableObjectNotFoundError(sha256) from error
            raise
        content = bytes(response["Body"].read())
        if hashlib.sha256(content).hexdigest() != sha256:
            raise ImmutableObjectConflictError(
                f"object {object_key} does not match its content-addressed key"
            )
        return content

    def _validate_existing_object(
        self,
        object_key: str,
        sha256: str,
        expected_size: int,
        head: dict[str, Any],
    ) -> None:
        stored_metadata = head.get("Metadata", {})
        if head.get("ContentLength") != expected_size or stored_metadata.get("sha256") != sha256:
            raise ImmutableObjectConflictError(
                f"existing object metadata conflicts with content address {object_key}"
            )
        content = bytes(self._client.get_object(Bucket=self._bucket, Key=object_key)["Body"].read())
        if len(content) != expected_size or hashlib.sha256(content).hexdigest() != sha256:
            raise ImmutableObjectConflictError(
                f"existing object bytes conflict with content address {object_key}"
            )
