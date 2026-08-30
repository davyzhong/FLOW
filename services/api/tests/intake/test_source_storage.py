from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest
from botocore.exceptions import ClientError

from flow_api.infrastructure.object_store import ObjectStore
from flow_api.intake.source_storage import (
    EmptySourceError,
    ImmutableObjectConflictError,
    SourceStorage,
    UnsupportedSourceTypeError,
)


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}
        self.put_calls = 0

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        del Bucket
        if Key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadObject",
            )
        content, content_type, metadata = self.objects[Key]
        return {
            "ContentLength": len(content),
            "ContentType": content_type,
            "Metadata": metadata,
        }

    def put_object(
        self,
        *,
        Bucket: str,  # noqa: N803
        Key: str,  # noqa: N803
        Body: bytes,  # noqa: N803
        ContentType: str,  # noqa: N803
        Metadata: dict[str, str],  # noqa: N803
    ) -> None:
        del Bucket
        self.put_calls += 1
        self.objects[Key] = (Body, ContentType, Metadata)

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        del Bucket
        if Key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "GetObject",
            )
        return {"Body": BytesIO(self.objects[Key][0])}


@pytest.fixture
def fake_client() -> FakeS3Client:
    return FakeS3Client()


@pytest.fixture
def source_storage(fake_client: FakeS3Client) -> SourceStorage:
    return SourceStorage(ObjectStore(client=fake_client, bucket="flow"))


def test_identical_source_bytes_reuse_identity_and_remain_readable(
    source_storage: SourceStorage, fake_client: FakeS3Client
) -> None:
    content = b"PK\x03\x04FLOW workbook bytes"

    first = source_storage.store(content, "august-actual.xlsx")
    second = source_storage.store(content, "renamed.xlsx")

    assert first.sha256 == second.sha256
    assert first.object_key == second.object_key
    assert first.original_filename == "august-actual.xlsx"
    assert second.original_filename == "renamed.xlsx"
    assert fake_client.put_calls == 1
    assert source_storage.read(first.sha256) == content


@pytest.mark.parametrize(
    ("content", "filename", "error_type"),
    [
        (b"", "empty.xlsx", EmptySourceError),
        (b"not excel", "source.csv", UnsupportedSourceTypeError),
        (b"macro workbook", "source.xlsm", UnsupportedSourceTypeError),
        (b"legacy workbook", "source.xls", UnsupportedSourceTypeError),
    ],
)
def test_invalid_source_is_rejected_before_object_storage(
    source_storage: SourceStorage,
    fake_client: FakeS3Client,
    content: bytes,
    filename: str,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        source_storage.store(content, filename)

    assert fake_client.put_calls == 0


def test_existing_content_address_with_different_bytes_is_never_reused(
    source_storage: SourceStorage, fake_client: FakeS3Client
) -> None:
    content = b"PK\x03\x04expected workbook"
    stored = source_storage.store(content, "source.xlsx")
    fake_client.objects[stored.object_key] = (
        b"PK\x03\x04tampered workbook",
        stored.content_type,
        {"sha256": stored.sha256},
    )

    with pytest.raises(ImmutableObjectConflictError):
        source_storage.store(content, "source.xlsx")


def test_existing_object_must_have_matching_hash_metadata(
    source_storage: SourceStorage, fake_client: FakeS3Client
) -> None:
    content = b"PK\x03\x04expected workbook"
    stored = source_storage.store(content, "source.xlsx")
    raw, content_type, _ = fake_client.objects[stored.object_key]
    fake_client.objects[stored.object_key] = (raw, content_type, {"sha256": "0" * 64})

    with pytest.raises(ImmutableObjectConflictError):
        source_storage.store(content, "source.xlsx")
