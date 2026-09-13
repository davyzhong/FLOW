#!/usr/bin/env python3
"""U8-A 下载校验：对 attempts JSON 逐个下载并核对 SHA-256。

用法：bash 前置已 export PUB_SNAPSHOT/API；attempts 文件路径作为 argv[1]。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

def main() -> int:
    attempts_path = sys.argv[1]
    api = os.environ.get("API", "http://localhost:8000")
    attempts = json.load(open(attempts_path, encoding="utf-8")).get("attempts", [])
    ok = 0
    checked = 0
    for attempt in attempts:
        if attempt.get("download_available") is False:
            continue
        attempt_id = attempt["attempt_id"]
        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.close()
        proc = subprocess.run(
            ["curl", "-sf", "-o", handle.name,
             f"{api}/api/v1/publishing/attempts/{attempt_id}/download"],
            capture_output=True,
        )
        actual = ""
        if proc.returncode == 0:
            actual = hashlib.sha256(open(handle.name, "rb").read()).hexdigest()
        expected = attempt.get("stored_sha256") or ""
        match = bool(actual) and actual == expected
        checked += 1
        ok += 1 if match else 0
        print(f"DOWNLOAD format={attempt['format']} attempt={attempt_id} sha_match={match}")
        print(f"  expect={expected[:16]}… actual={actual[:16]}…")
        os.remove(handle.name)
    print(f"DOWNLOAD_SUMMARY checked={checked} sha_ok={ok}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
