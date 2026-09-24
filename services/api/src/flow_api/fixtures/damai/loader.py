"""大麦演示数据装载器（Task 4）：enterprise 幂等配置 + 财报装载子链。

装载顺序（每步过领域服务，不绕过质量/对账）：
1. 复用固定 bootstrap enterprise UUID（授权契约单企业），幂等改名为大麦；
2. 两份合成财报按 canonical yaml 导入（source SHA 非空）、归一化、发布；
3. 输出机器可读 receipt。

行名映射：大麦 canonical yaml 使用抽取脚本归一后的规范名，与
alibaba_9988 映射段一致，故导入用 stock_code 9988.HK 复用该段。
指标快照 / AnalysisRun / Finding 状态机 / 冻结在后续切片接入（规格 §4.3）。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import text

from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report


def _statements_dir() -> Path:
    """定位 docs/implementation/p5（容器/worktree 下从 cwd 向上遍历）。"""

    relative = Path("docs/implementation/p5")
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"未找到 {relative}（从 cwd 向上遍历失败）")


_DAMAI_FY: tuple[str, ...] = ("FY2025", "FY2026")
_BOOTSTRAP_ID = "00000000-0000-0000-0000-00000000d001"
_DAMAI_COMPANY_NAME = "大麦物流集团（synthetic 演示企业）"


def _upsert_enterprise(session: Any) -> dict[str, str]:
    """复用固定 bootstrap enterprise，幂等改名为大麦（授权契约单企业）。"""

    session.execute(
        text(
            "INSERT INTO enterprise (id, code, name, created_at)"
            " VALUES (:id, :code, :name, now())"
            " ON CONFLICT (id) DO UPDATE SET code = :code, name = :name"
        ),
        {"id": _BOOTSTRAP_ID, "code": "damai-logistics", "name": _DAMAI_COMPANY_NAME},
    )
    return {
        "id": _BOOTSTRAP_ID,
        "code": "damai-logistics",
        "name": _DAMAI_COMPANY_NAME,
    }


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_damai_demo(session: Any) -> dict[str, Any]:
    """装载大麦演示数据：enterprise 配置 + 两份财报导入/归一化/发布。"""

    enterprise = _upsert_enterprise(session)
    reports: list[dict[str, Any]] = []
    for fy in _DAMAI_FY:
        yaml_path = _statements_dir() / f"alibaba_{fy[2:].lower()}fy_statements.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(
                f"大麦财报 canonical yaml 缺失：{yaml_path}"
                "（先运行 scripts/p5_extract_alibaba.py）"
            )
        source_bytes = yaml_path.read_bytes()
        report = import_statement_report(
            session,
            company_name=_DAMAI_COMPANY_NAME,
            stock_code="9988.HK",
            report_kind="年报",
            period_label=fy,
            payload=yaml.safe_load(source_bytes.decode("utf-8")),
            source_ref=f"synthetic/damai-logistics-demo-v1/{fy}",
            source_sha256=_sha256_of(yaml_path),
        )
        report.status = "published"
        session.flush()
        normalize_report(session, report)
        normalized = session.execute(
            text(
                "SELECT count(*) FROM statement_normalized_item"
                " WHERE report_id = :rid AND item_id IS NOT NULL"
            ),
            {"rid": str(report.id)},
        ).scalar_one()
        reports.append(
            {
                "report_id": str(report.id),
                "fy": fy,
                "status": report.status,
                "normalized_rows": int(normalized),
                "source_sha256": report.source_sha256 or "",
            }
        )
    session.flush()
    return {"enterprise": enterprise, "reports": reports}


__all__ = ["seed_damai_demo"]
