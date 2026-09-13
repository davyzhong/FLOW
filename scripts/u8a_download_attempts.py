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
from pathlib import Path

def main() -> int:
    attempts_path = sys.argv[1]
    summary_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    api = os.environ.get("API", "http://localhost:8000")
    attempts = json.load(open(attempts_path, encoding="utf-8")).get("attempts", [])
    ok = 0
    checked = 0
    downloads = []
    for attempt in attempts:
        expected = attempt.get("stored_sha256") or ""
        if attempt.get("download_available") is False:
            downloads.append({"expected_sha256": expected, "actual_sha256": ""})
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
        match = bool(actual) and actual == expected
        downloads.append({"expected_sha256": expected, "actual_sha256": actual})
        checked += 1
        ok += 1 if match else 0
        print(f"DOWNLOAD format={attempt['format']} attempt={attempt_id} sha_match={match}")
        print(f"  expect={expected[:16]}… actual={actual[:16]}…")
        os.remove(handle.name)
    print(f"DOWNLOAD_SUMMARY checked={checked} sha_ok={ok}")
    if summary_path:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps({"downloads": downloads}, indent=2) + "\n", encoding="utf-8"
        )
    return 0 if attempts and checked == len(attempts) and ok == len(attempts) else 1

if __name__ == "__main__":
    raise SystemExit(main())
