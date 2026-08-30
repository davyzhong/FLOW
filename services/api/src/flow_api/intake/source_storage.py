from __future__ import annotations

from dataclasses import dataclass

from flow_api.infrastructure.object_store import (
    ImmutableObjectConflictError,
    ObjectStore,
)


class SourceStorageError(ValueError):
    """Base error for source workbook admission."""


class EmptySourceError(SourceStorageError):
    """Raised when an uploaded source has no bytes."""


class UnsupportedSourceTypeError(SourceStorageError):
    """Raised when a source is not a supported macro-free XLSX workbook."""


class InvalidWorkbookSourceError(SourceStorageError):
    """Raised when an XLSX filename does not contain ZIP workbook bytes."""


@dataclass(frozen=True, slots=True)
class StoredSource:
    sha256: str
    object_key: str
    size_bytes: int
    content_type: str
    original_filename: str


class SourceStorage:
    def __init__(self, object_store: ObjectStore) -> None:
        self._object_store = object_store

    def store(self, content: bytes, filename: str) -> StoredSource:
        if not content:
            raise EmptySourceError("source workbook is empty")
        if not filename.lower().endswith(".xlsx"):
            raise UnsupportedSourceTypeError("FLOW V1 accepts macro-free .xlsx workbooks only")
        if not content.startswith(b"PK\x03\x04"):
            raise InvalidWorkbookSourceError("source does not contain XLSX ZIP bytes")

        stored = self._object_store.put_immutable(content, filename)
        return StoredSource(
            sha256=stored.sha256,
            object_key=stored.object_key,
            size_bytes=stored.size_bytes,
            content_type=stored.content_type,
            original_filename=filename,
        )

    def read(self, sha256: str) -> bytes:
        return self._object_store.read_by_sha(sha256)


__all__ = [
    "EmptySourceError",
    "ImmutableObjectConflictError",
    "InvalidWorkbookSourceError",
    "SourceStorage",
    "StoredSource",
    "UnsupportedSourceTypeError",
]
