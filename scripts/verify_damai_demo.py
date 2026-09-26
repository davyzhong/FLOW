#!/usr/bin/env python3
"""大麦演示数据验收对账（Task C1）。

五类检查（每类产出结构化 check 行，任何失败即整体失败）：
1. release_manifest：发行包文件 SHA 与行数逐一与 manifest.json 对账；
2. db_counts：关键表计数（财报 2 / 批次 1 / 快照 12 / run 1 / finding/conclusion/冻结）；
3. freeze_hashes：客观财报快照与经营概览 payload_hash 由载荷重算；内部分析报告
   digest_view 重算；
4. api：--api-url 提供时对账 /metric-library/coverage 双数据集响应；
5. object_storage：--check-storage 时对账工作簿对象存储 SHA。

用法：
    python scripts/verify_damai_demo.py [--api-url http://localhost:8000] \
        [--check-storage] [--output work/damai-demo/verify_receipt.json]

纯函数（check_release_manifest / summarize）不依赖数据库，可单测。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services/api/src"))

DEFAULT_DATABASE_URL = "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow"

Check = dict[str, Any]


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(name: str, passed: bool, detail: str = "") -> Check:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _workbook_semantic_digest(path: Path) -> str:
    """xlsx 单元格值级指纹（与 scripts/build_damai_demo.py 同算法，本地复制以
    保持本脚本可在无 flow_api 依赖的系统 Python 下运行）。"""

    from openpyxl import load_workbook

    workbook = load_workbook(path, data_only=True, read_only=True)
    payload: list[Any] = []
    for sheet in workbook.worksheets:
        payload.append([sheet.title])
        for row in sheet.iter_rows(values_only=True):
            payload.append(["" if v is None else str(v) for v in row])
    workbook.close()
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return "semantic:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def check_release_manifest(root: Path = ROOT) -> list[Check]:
    """发行包零漂移：manifest.files 的 SHA 与 row_counts 逐一对账。"""

    manifest_path = root / "fixtures/damai/manifest.json"
    if not manifest_path.is_file():
        return [_check("release_manifest", False, "manifest.json 不存在")]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks: list[Check] = []
    mismatches = []
    for relative, expected_sha in sorted(manifest["files"].items()):
        path = root / "fixtures/damai" / relative
        if not path.is_file():
            mismatches.append(f"{relative}: 缺失")
            continue
        if expected_sha.startswith("semantic:"):
            # xlsx 容器字节非确定（zip 时间戳）：按单元格值级指纹对账
            actual = _workbook_semantic_digest(path)
        else:
            actual = _sha256_of(path)
        if actual != expected_sha:
            mismatches.append(f"{relative}: sha 漂移")
    checks.append(
        _check(
            "release_manifest.files",
            not mismatches,
            "；".join(mismatches) or f"{len(manifest['files'])} 个文件 SHA 全部一致",
        )
    )
    row_mismatches = []
    for relative, expected_rows in sorted(manifest["row_counts"].items()):
        path = root / "fixtures/damai" / relative
        if not path.is_file():
            row_mismatches.append(f"{relative}: 缺失")
            continue
        actual_rows = sum(
            1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        if actual_rows != expected_rows:
            row_mismatches.append(f"{relative}: {actual_rows} != {expected_rows}")
    checks.append(
        _check(
            "release_manifest.row_counts",
            not row_mismatches,
            "；".join(row_mismatches) or f"{len(manifest['row_counts'])} 个文件行数全部一致",
        )
    )
    return checks


def check_db_counts(database_url: str) -> list[Check]:
    """关键表计数对账（期望值来自计划 §4 验收口径）。"""

    from sqlalchemy import create_engine, text

    expectations = {
        "analysis_batch": ("=", 1),
        "metric_snapshot": ("=", 12),
        "analysis_run": ("=", 1),
        "finding": (">=", 1),
        "conclusion": (">=", 1),
        "report_snapshot": (">=", 1),
        "objective_report_snapshot": (">=", 4),
        "analysis_cycle": (">=", 1),
    }
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            checks = []
            damai_reports = count_latest_published_damai_reports(conn)
            checks.append(
                _check(
                    "db_counts.statement_report",
                    damai_reports == 2,
                    f"大麦最新已发布财报身份实际 {damai_reports}（期望 = 2）",
                )
            )
            for table, (op, expected) in expectations.items():
                actual = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
                passed = actual == expected if op == "=" else actual >= expected
                checks.append(
                    _check(
                        f"db_counts.{table}",
                        passed,
                        f"实际 {actual}（期望 {op} {expected}）",
                    )
                )
            batch = conn.execute(
                text(
                    "SELECT c.period_key FROM analysis_batch b"
                    " JOIN analysis_cycle c ON c.id = b.analysis_cycle_id"
                    " WHERE b.name = 'damai-demo-v1'"
                )
            ).scalar()
            checks.append(
                _check(
                    "db_counts.analysis_cycle_binding",
                    batch == "2026-08",
                    f"批次绑定周期 {batch}（期望 2026-08）",
                )
            )
            return checks
    finally:
        engine.dispose()


def count_latest_published_damai_reports(connection: Any) -> int:
    """计大麦FY2025/FY2026最新版本，不把保留的重述/历史版本当作额外报表。"""

    from sqlalchemy import text

    return int(
        connection.execute(
            text(
                "WITH latest AS ("
                " SELECT stock_code, period_label, report_kind, MAX(version) AS max_version"
                " FROM statement_report"
                " WHERE stock_code = 'DAMAI.SYN' AND report_kind = '年报'"
                "   AND period_label IN ('FY2025', 'FY2026')"
                " GROUP BY stock_code, period_label, report_kind"
                ")"
                " SELECT count(*) FROM statement_report r"
                " JOIN latest l ON r.stock_code = l.stock_code"
                "  AND r.period_label = l.period_label AND r.report_kind = l.report_kind"
                "  AND r.version = l.max_version"
                " WHERE r.status = 'published'"
            )
        ).scalar_one()
    )


def check_freeze_hashes(database_url: str) -> list[Check]:
    """冻结 SHA 重算：客观快照/经营概览 payload_hash；内部报告 digest_view。"""

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from flow_api.infrastructure.models.publishing import ReportSnapshot
    from flow_api.publishing.objective_freeze import (
        ObjectiveReportSnapshot,
        payload_hash,
    )
    from flow_api.publishing.service import build_report_view, digest_view
    engine = create_engine(database_url)
    checks: list[Check] = []
    try:
        with Session(engine) as session:
            objective_rows = session.scalars(select(ObjectiveReportSnapshot)).all()
            bad = [
                f"{row.report_type} v{row.version}"
                for row in objective_rows
                if payload_hash(row.payload) != row.payload_hash
            ]
            checks.append(
                _check(
                    "freeze_hashes.objective",
                    bool(objective_rows) and not bad,
                    f"{len(objective_rows)} 个客观快照全部可重算"
                    if not bad
                    else f"重算不一致：{bad}",
                )
            )
            report_rows = session.scalars(select(ReportSnapshot)).all()
            bad_reports = []
            for row in report_rows:
                try:
                    digest_view(build_report_view(session, row))
                except Exception as error:  # noqa: BLE001 - 验收需如实记录任何失败
                    bad_reports.append(f"{row.id}: {error}")
            checks.append(
                _check(
                    "freeze_hashes.internal_report",
                    bool(report_rows) and not bad_reports,
                    f"{len(report_rows)} 个内部报告冻结视图可重建"
                    if not bad_reports
                    else f"重建失败：{bad_reports}",
                )
            )
            return checks
    finally:
        engine.dispose()


def check_api(api_url: str) -> list[Check]:
    """API 对账：双数据集 coverage 响应。"""

    checks: list[Check] = []

    def fetch(path: str) -> tuple[int, dict[str, Any]]:
        with urllib.request.urlopen(f"{api_url}{path}", timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    try:
        status, body = fetch("/api/v1/metric-library/coverage")
        checks.append(
            _check(
                "api.coverage_public",
                status == 200 and body.get("dataset_id") == "flow.p5_metric_coverage.v1"
                and body.get("synthetic") is False,
                f"status={status} dataset={body.get('dataset_id')}",
            )
        )
        status, body = fetch("/api/v1/metric-library/coverage?dataset=damai")
        checks.append(
            _check(
                "api.coverage_damai",
                status == 200
                and body.get("dataset_id") == "flow.damai_demo_metric_coverage.v1"
                and body.get("synthetic") is True,
                f"status={status} dataset={body.get('dataset_id')}",
            )
        )
    except Exception as error:  # noqa: BLE001 - 验收需如实记录任何失败
        checks.append(_check("api.reachable", False, f"{api_url} 不可达：{error}"))
    return checks


def check_object_storage(database_url: str) -> list[Check]:
    """对象存储对账：stored_object 可读回且 SHA 完整；与发行版工作簿按语义指纹
    比对（xlsx zip 容器字节非确定，原始字节 SHA 漂移不算漂移）。"""

    import tempfile

    from sqlalchemy import create_engine, text

    from flow_api.infrastructure.object_store import ObjectStore
    from flow_api.infrastructure.s3_client import build_s3_client
    from flow_api.settings import get_settings
    workbook = ROOT / "fixtures/damai/workbooks/damai_logistics_full_v1.xlsx"
    engine = create_engine(database_url)
    checks: list[Check] = []
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT sha256, object_key, size_bytes FROM stored_object")
            ).fetchall()
        checks.append(
            _check(
                "object_storage.registered",
                len(rows) >= 1,
                f"stored_object {len(rows)} 个",
            )
        )
        if not rows:
            return checks
        settings = get_settings()
        store = ObjectStore(client=build_s3_client(settings), bucket=settings.s3_bucket)
        registered = rows[0]
        content = store.read_by_sha(registered.sha256)  # 读回路径内部即校验 SHA 完整性
        checks.append(
            _check(
                "object_storage.readback",
                len(content) == registered.size_bytes,
                f"读回 {len(content)} 字节（登记 {registered.size_bytes}），SHA 校验通过",
            )
        )
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as handle:
            handle.write(content)
            handle.flush()
            stored_semantic = _workbook_semantic_digest(Path(handle.name))
        current_semantic = _workbook_semantic_digest(workbook)
        checks.append(
            _check(
                "object_storage.semantic_match",
                stored_semantic == current_semantic,
                "存储对象与发行版工作簿单元格值级一致"
                if stored_semantic == current_semantic
                else f"语义漂移：{stored_semantic} vs {current_semantic}",
            )
        )
        return checks
    finally:
        engine.dispose()


def summarize(checks: list[Check]) -> dict[str, Any]:
    return {
        "ok": all(check["passed"] for check in checks),
        "total": len(checks),
        "failed": [check["name"] for check in checks if not check["passed"]],
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", help="API 基地址（提供时才做 API 对账）")
    parser.add_argument("--check-storage", action="store_true", help="对账对象存储 SHA")
    parser.add_argument("--output", help="验收 receipt JSON 落盘路径")
    args = parser.parse_args()

    checks: list[Check] = []
    checks += check_release_manifest()

    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    checks += check_db_counts(database_url)
    checks += check_freeze_hashes(database_url)
    if args.api_url:
        checks += check_api(args.api_url.rstrip("/"))
    if args.check_storage:
        checks += check_object_storage(database_url)

    verdict = {
        "schema_version": "damai-demo-verify-receipt/v1",
        **summarize(checks),
    }
    payload = json.dumps(verdict, ensure_ascii=False, indent=2, default=str)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
