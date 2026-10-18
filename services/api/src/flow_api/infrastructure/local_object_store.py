from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from pathlib import Path

from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.object_store import (
    SHA256_PATTERN,
    ImmutableObjectConflictError,
    ImmutableObjectNotFoundError,
    ObjectStore,
)


class LocalObjectStore:
    """本地文件目录实现，保持 ObjectStore 的内容寻址与不可变语义。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).expanduser().resolve()

    @staticmethod
    def object_key_for_sha(sha256: str) -> str:
        return ObjectStore.object_key_for_sha(sha256)

    def _path_for_key(self, object_key: str) -> Path:
        relative = Path(object_key)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValueError("object_key must be a relative path without traversal")
        candidate = (self._root / relative).resolve()
        if not candidate.is_relative_to(self._root):
            raise ValueError("object_key escapes local object root")
        return candidate

    def put_immutable(self, content: bytes, filename: str) -> StoredObject:
        sha256 = hashlib.sha256(content).hexdigest()
        object_key = self.object_key_for_sha(sha256)
        self.write_if_absent(
            object_key=object_key,
            content=content,
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            content_sha256=sha256,
        )
        return StoredObject(
            sha256=sha256,
            object_key=object_key,
            size_bytes=len(content),
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
        )

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> tuple[str, bool]:
        del content_type  # 内容类型由数据库的 StoredObject 记录保存。
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if not SHA256_PATTERN.fullmatch(content_sha256):
            raise ValueError("content_sha256 must be 64 lowercase hexadecimal characters")
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != content_sha256:
            raise ValueError("content_sha256 does not match content")

        target = self._path_for_key(object_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            self._validate_existing(target, content, content_sha256, object_key)
            return (content_sha256, False)

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temp_path = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temp_path, target)
            except FileExistsError:
                self._validate_existing(target, content, content_sha256, object_key)
                return (content_sha256, False)
            return (content_sha256, True)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def read_by_sha(self, sha256: str) -> bytes:
        return self.read_by_key(self.object_key_for_sha(sha256), sha256)

    def read_by_key(self, object_key: str, sha256: str) -> bytes:
        if not SHA256_PATTERN.fullmatch(sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        path = self._path_for_key(object_key)
        try:
            content = path.read_bytes()
        except FileNotFoundError as error:
            raise ImmutableObjectNotFoundError(sha256) from error
        if hashlib.sha256(content).hexdigest() != sha256:
            raise ImmutableObjectConflictError(
                f"object {object_key} does not match its registered sha256"
            )
        return content

    @staticmethod
    def _validate_existing(
        path: Path, content: bytes, sha256: str, object_key: str
    ) -> None:
        existing = path.read_bytes()
        if existing != content or hashlib.sha256(existing).hexdigest() != sha256:
            raise ImmutableObjectConflictError(
                f"existing object {object_key} conflicts with content {sha256}"
            )


__all__ = ["LocalObjectStore"]
