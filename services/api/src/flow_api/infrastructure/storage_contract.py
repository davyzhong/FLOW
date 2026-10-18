from __future__ import annotations

import re
from typing import Protocol

from flow_api.infrastructure.models.intake import StoredObject

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ImmutableObjectConflictError(RuntimeError):
    """A content-addressed key does not contain the expected bytes."""


class ImmutableObjectNotFoundError(FileNotFoundError):
    """A content-addressed object does not exist."""


class ObjectStorage(Protocol):
    def put_immutable(self, content: bytes, filename: str) -> StoredObject: ...

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> tuple[str, bool]: ...

    def read_by_sha(self, sha256: str) -> bytes: ...

    def read_by_key(self, object_key: str, sha256: str) -> bytes: ...


def object_key_for_sha(sha256: str) -> str:
    if not SHA256_PATTERN.fullmatch(sha256):
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return f"raw/{sha256[:2]}/{sha256}"
