from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

BACKUP_MANIFEST = "manifest.json"
DATABASE_MEMBER = "database.sqlite3"


def create_local_backup(
    *, database_path: str | Path, object_root: str | Path, backup_path: str | Path
) -> Path:
    """创建包含 SQLite 一致性快照与本地对象文件的自校验 ZIP 包。"""
    database = Path(database_path).expanduser().resolve()
    objects = Path(object_root).expanduser().resolve()
    output = Path(backup_path).expanduser().resolve()
    if not database.is_file():
        raise FileNotFoundError(database)
    if not objects.is_dir():
        raise FileNotFoundError(objects)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=output.parent) as temp_dir:
        staging = Path(temp_dir)
        db_copy = staging / DATABASE_MEMBER
        with (
            sqlite3.connect(f"file:{database}?mode=ro", uri=True) as source,
            sqlite3.connect(db_copy) as target,
        ):
            source.backup(target)

        members: list[dict[str, Any]] = []
        files: list[tuple[Path, str]] = [(db_copy, DATABASE_MEMBER)]
        for path in sorted(objects.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"object store cannot contain symlinks: {path}")
            if path.is_file():
                relative = path.relative_to(objects).as_posix()
                files.append((path, f"objects/{relative}"))

        for file_path, archive_name in files:
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            members.append({"path": archive_name, "sha256": digest})
        manifest = json.dumps(
            {"format": 1, "files": members}, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")

        fd, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(BACKUP_MANIFEST, manifest)
                for file_path, archive_name in files:
                    archive.write(file_path, archive_name)
            os.link(temp_name, output)
        finally:
            Path(temp_name).unlink(missing_ok=True)
    return output


def restore_local_backup(
    *, backup_path: str | Path, destination: str | Path
) -> tuple[Path, Path]:
    """校验备份包后恢复到必须为空的目标目录，返回数据库和对象目录路径。"""
    archive_path = Path(backup_path).expanduser().resolve()
    target = Path(destination).expanduser().resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    if target.exists():
        raise FileExistsError(target)

    staging_parent = target.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging_parent) as temp_dir:
        staging = Path(temp_dir) / "restore"
        staging.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            try:
                manifest = json.loads(archive.read(BACKUP_MANIFEST))
            except (KeyError, json.JSONDecodeError) as error:
                raise ValueError("backup manifest is missing or invalid") from error
            if manifest.get("format") != 1 or not isinstance(manifest.get("files"), list):
                raise ValueError("unsupported backup format")

            expected: dict[str, str] = {}
            for entry in manifest["files"]:
                relative = PurePosixPath(entry.get("path", ""))
                digest = entry.get("sha256", "")
                if (
                    relative.is_absolute()
                    or not relative.parts
                    or any(part in {"", ".", ".."} for part in relative.parts)
                    or not isinstance(digest, str)
                    or len(digest) != 64
                ):
                    raise ValueError("backup manifest contains an unsafe file entry")
                expected[relative.as_posix()] = digest

            archive_names = set(archive.namelist()) - {BACKUP_MANIFEST}
            if archive_names != set(expected):
                raise ValueError("backup archive contents do not match manifest")
            for name, digest in expected.items():
                content = archive.read(name)
                if hashlib.sha256(content).hexdigest() != digest:
                    raise ValueError(f"backup file failed integrity check: {name}")
                output_path = staging.joinpath(*PurePosixPath(name).parts)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(content)

        database = staging / DATABASE_MEMBER
        objects = staging / "objects"
        if not database.is_file() or not objects.is_dir():
            raise ValueError("backup must include database.sqlite3 and objects/")
        os.replace(staging, target)
    return target / DATABASE_MEMBER, target / "objects"


__all__ = ["create_local_backup", "restore_local_backup"]
