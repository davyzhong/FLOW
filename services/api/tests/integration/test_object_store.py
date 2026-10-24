from pathlib import Path
from uuid import uuid4

from flow_api.infrastructure.local_object_store import LocalObjectStore


def test_identical_bytes_reuse_content_addressed_object(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path)
    content = f"FLOW-{uuid4()}".encode()

    first = store.put_immutable(content, "source.xlsx")
    second = store.put_immutable(content, "renamed.xlsx")

    assert first.sha256 == second.sha256
    assert first.object_key == second.object_key
    assert store.read_by_sha(first.sha256) == content
