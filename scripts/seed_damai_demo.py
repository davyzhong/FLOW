#!/usr/bin/env python3
"""大麦演示数据一键装载（Task C1）。

用法：
    python scripts/seed_damai_demo.py [--output work/damai-demo/seed_receipt.json]

语义：
- 调用 fixtures.damai.loader.seed_damai_demo（全程 flush-only），本脚本负责顶层
  commit；任何失败即 rollback 并以非零码退出，不留部分数据；
- 输出机器可读 receipt（JSON）：release manifest SHA、enterprise/cycle、
  batch/import、snapshots/run、findings、三类冻结 SHA，供 verify 与 CI 对账。

环境：DATABASE_URL 必填（默认指向本地 compose 的 flow 库）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services/api/src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DEFAULT_DATABASE_URL = "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow"


def _release_manifest_sha256() -> str:
    return hashlib.sha256((ROOT / "fixtures/damai/manifest.json").read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="receipt JSON 落盘路径（同时打印到 stdout）")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    from flow_api.fixtures.damai.loader import seed_damai_demo

    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            try:
                receipt = seed_damai_demo(session)
            except Exception:
                session.rollback()
                raise
            session.commit()
    finally:
        engine.dispose()

    receipt = {
        "schema_version": "damai-demo-seed-receipt/v1",
        "release_manifest_sha256": _release_manifest_sha256(),
        **receipt,
    }
    payload = json.dumps(receipt, ensure_ascii=False, indent=2, default=str)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
