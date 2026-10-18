from __future__ import annotations

import hashlib
import sqlite3
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pytest

from flow_api.infrastructure.local_backup import (
    create_local_backup,
    restore_local_backup,
)
from flow_api.infrastructure.local_object_store import LocalObjectStore
from flow_api.infrastructure.object_store import (
    ImmutableObjectConflictError,
    ImmutableObjectNotFoundError,
)


def test_content_addressed_write_is_idempotent_and_readable(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)
    content = b"public filing source"

    first = store.put_immutable(content, "filing.xlsx")
    second = store.put_immutable(content, "renamed.xlsx")

    assert first.sha256 == second.sha256 == hashlib.sha256(content).hexdigest()
    assert first.object_key == second.object_key
    assert store.read_by_sha(first.sha256) == content


def test_write_if_absent_rejects_key_collision_and_wrong_digest(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)
    original = b"one"
    replacement = b"two"
    key = "raw/aa/object"
    store.write_if_absent(
        object_key=key,
        content=original,
        content_type="text/plain",
        content_sha256=hashlib.sha256(original).hexdigest(),
    )

    with pytest.raises(ImmutableObjectConflictError):
        store.write_if_absent(
            object_key=key,
            content=replacement,
            content_type="text/plain",
            content_sha256=hashlib.sha256(replacement).hexdigest(),
        )
    with pytest.raises(ValueError, match="does not match"):
        store.write_if_absent(
            object_key="raw/other",
            content=replacement,
            content_type="text/plain",
            content_sha256=hashlib.sha256(original).hexdigest(),
        )


def test_concurrent_single_user_writes_converge_on_one_immutable_object(tmp_path) -> None:
    content = b"same source bytes"
    digest = hashlib.sha256(content).hexdigest()

    def write() -> tuple[str, bool]:
        return LocalObjectStore(tmp_path).write_if_absent(
            object_key=LocalObjectStore.object_key_for_sha(digest),
            content=content,
            content_type="text/plain",
            content_sha256=digest,
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda _index: write(), range(12)))

    assert all(result[0] == digest for result in results)
    assert sum(created for _, created in results) == 1
    assert LocalObjectStore(tmp_path).read_by_sha(digest) == content


def test_read_reports_missing_and_corrupted_content(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)
    digest = hashlib.sha256(b"expected").hexdigest()
    key = store.object_key_for_sha(digest)

    with pytest.raises(ImmutableObjectNotFoundError):
        store.read_by_key(key, digest)

    target = tmp_path / key
    target.parent.mkdir(parents=True)
    target.write_bytes(b"corrupted")
    with pytest.raises(ImmutableObjectConflictError):
        store.read_by_sha(digest)


def test_key_cannot_escape_local_root(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)
    with pytest.raises(ValueError, match="traversal"):
        store.read_by_key("../outside", "0" * 64)


def test_backup_restores_database_and_objects_into_new_directory(tmp_path) -> None:
    database = tmp_path / "source" / "flow.sqlite3"
    database.parent.mkdir()
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE probe (value TEXT NOT NULL)")
        connection.execute("INSERT INTO probe VALUES ('finance facts')")
    object_root = tmp_path / "source" / "objects"
    store = LocalObjectStore(object_root)
    stored = store.put_immutable(b"source bytes", "source.csv")
    backup = create_local_backup(
        database_path=database,
        object_root=object_root,
        backup_path=tmp_path / "flow-backup.zip",
    )

    restored_db, restored_objects = restore_local_backup(
        backup_path=backup,
        destination=tmp_path / "restored",
    )

    with sqlite3.connect(restored_db) as connection:
        assert connection.execute("SELECT value FROM probe").fetchone() == (
            "finance facts",
        )
    assert LocalObjectStore(restored_objects).read_by_sha(stored.sha256) == b"source bytes"


def test_backup_restore_rejects_existing_destination_and_corrupt_archive(tmp_path) -> None:
    database = tmp_path / "flow.sqlite3"
    with sqlite3.connect(database):
        pass
    object_root = tmp_path / "objects"
    object_root.mkdir()
    backup = create_local_backup(
        database_path=database,
        object_root=object_root,
        backup_path=tmp_path / "flow-backup.zip",
    )

    with pytest.raises(FileExistsError):
        restore_local_backup(backup_path=backup, destination=tmp_path)
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(b"not a zip file")
    with pytest.raises(zipfile.BadZipFile):
        restore_local_backup(backup_path=corrupt, destination=tmp_path / "bad-restore")
