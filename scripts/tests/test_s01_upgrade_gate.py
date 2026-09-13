"""S01 升级验证门禁测试（Task 9 / 6A）。

仅标准库：不启动 docker，验证 runner 脚本的关键前置逻辑——
fast-fail 顺序（缺变量 → SHA 不匹配）、脚本语法与必需文件存在。
"""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/verify_s01_upgrade_from_u8.sh"
COMPOSE_OVERRIDE = ROOT / "infra/compose.s01-acceptance.yaml"


def _module():
    spec = importlib.util.spec_from_file_location(
        "verify_s01_upgrade_from_u8", RUNNER
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_and_compose_exist() -> None:
    assert RUNNER.is_file()
    assert COMPOSE_OVERRIDE.is_file()
    assert "s01accept" in COMPOSE_OVERRIDE.read_text(encoding="utf-8")


def test_runner_is_valid_bash() -> None:
    proc = subprocess.run(["bash", "-n", str(RUNNER)], capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode()


def test_runner_fast_fails_on_missing_env() -> None:
    proc = subprocess.run(
        ["bash", str(RUNNER)],
        capture_output=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode != 0
    assert b"FLOW_U8_BACKUP_PATH" in proc.stderr


def test_runner_fast_fails_on_sha_mismatch(tmp_path: Path) -> None:
    dump = tmp_path / "backup.dump"
    dump.write_bytes(b"payload")
    bad_sha = hashlib.sha256(b"other").hexdigest()
    proc = subprocess.run(
        ["bash", str(RUNNER)],
        capture_output=True,
        env={
            "PATH": "/usr/bin:/bin",
            "FLOW_U8_BACKUP_PATH": str(dump),
            "FLOW_U8_BACKUP_SHA256": bad_sha,
            "FLOW_U8_CA_CERT": str(tmp_path / "ca.crt"),
        },
    )
    assert proc.returncode != 0
    assert b"VERIFY_FAIL" in proc.stderr
    assert b"docker" not in proc.stderr.split(b"VERIFY_FAIL")[0]


def test_gate_test_uses_recorded_u8_backup_constants() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "alembic upgrade head" in text
    assert "https://localhost" in text
    assert "菜鸟网络" in text
