"""大麦演示数据装载器（Task 4）：enterprise 幂等配置 + 财报装载子链。

装载顺序（每步过领域服务，不绕过质量/对账）：
1. 复用固定 bootstrap enterprise UUID（授权契约单企业），幂等改名为大麦；
2. 两份合成财报按 canonical yaml 导入（source SHA 非空）、归一化、发布；
3. 输出机器可读 receipt。

行名映射：大麦 canonical yaml 使用抽取脚本归一后的规范名，与
alibaba_9988 映射段一致，故导入用 stock_code 9988.HK 复用该段。
slice-2a：工作簿导入（IntakeService 全链）→ 12 个月指标快照 → 最新 AnalysisRun。
Finding 状态机推进与冻结 receipt 在下一切片（规格 §4.3 第 4-6 步）。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select, text

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.data_contract.contract import load_contract
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    QualityIssue,
    WarningAcknowledgement,
)
from flow_api.intake.detector import profile_workbook
from flow_api.intake.extractor import extract_candidate_package
from flow_api.intake.mapping import load_aliases, propose_mapping
from flow_api.intake.quality import evaluate_quality
from flow_api.intake.service import IntakeService
from flow_api.intake.source_storage import StoredSource
from flow_api.intake.transforms import load_transform_rules
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService
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
# 分析窗口：与大麦 profile 的 24 个月合同一致（后 12 个月为分析期）
_ANALYSIS_MONTH_KEYS: tuple[int, ...] = tuple(
    2025 * 100 + m for m in range(9, 13)
) + tuple(2026 * 100 + m for m in range(1, 9))
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
    receipt: dict[str, Any] = {"enterprise": enterprise, "reports": reports}
    receipt["analytics"] = _seed_analytics(session)
    session.flush()
    return receipt


def _repository_root() -> Path:
    """仓库根（含 templates/、config/、services/），从 cwd 向上探测。"""

    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到仓库根（templates/excel/flow_v1_contract.yaml）")


def _release_workbook_path() -> Path:
    """发行版标准工作簿（build_damai_demo.py 产物）。"""

    relative = Path("fixtures/damai/workbooks/damai_logistics_full_v1.xlsx")
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"未找到 {relative}（先运行 scripts/build_damai_demo.py 构建发行版）"
    )


def _intake_inputs(workbook: Path) -> tuple[StoredSource, Any, Any, Any]:
    """从标准工作簿构造 IntakeService 导入四件套（与契约同源，生产路径）。"""

    repo_root = _repository_root()
    contract = load_contract(repo_root / "templates/excel/flow_v1_contract.yaml")
    aliases = load_aliases(repo_root / "config/intake/flow_v1_aliases.yaml")
    transforms = load_transform_rules(repo_root / "config/intake/flow_v1_transforms.yaml")
    content = workbook.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    profile = profile_workbook(content)
    proposal = propose_mapping(profile, contract, aliases)
    candidate = extract_candidate_package(content, profile, proposal, contract, transforms)
    report = evaluate_quality(candidate.package, contract, proposal)
    stored = StoredSource(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=len(content),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        original_filename=workbook.name,
    )
    return stored, proposal, candidate, report


def _seed_analytics(session: Any) -> dict[str, Any]:
    """工作簿导入 → 12 个月指标快照 → 最新 AnalysisRun（全部走领域服务）。"""

    actor = "damai-demo-seed"
    batch = session.scalar(
        select(AnalysisBatch).where(AnalysisBatch.name == "damai-demo-v1")
    )
    if batch is None:
        # 首次装载：标准工作簿走完整 IntakeService 导入链
        workbook = _release_workbook_path()
        stored, proposal, candidate, report = _intake_inputs(workbook)
        intake = IntakeService(session)
        batch = intake.create_batch("damai-demo-v1")
        source = intake.attach_source(batch.id, stored)
        mapping = intake.propose_mapping(source.id, proposal, actor=actor)
        confirmed = intake.confirm_mapping(mapping.id, actor=actor)
        version = intake.validate_import(source.id, confirmed.id, candidate, report)
        acknowledged = select(WarningAcknowledgement.quality_issue_id)
        pending = session.execute(
            select(QualityIssue.id).where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "warning",
                QualityIssue.id.not_in(acknowledged),
            )
        ).fetchall()
        for (issue_id,) in pending:
            intake.acknowledge_warning(
                issue_id, actor=actor, reason="synthetic demo dataset (verified by generator)"
            )
        intake.publish_import(version.id)
        session.flush()
    else:
        version = session.scalar(
            select(ImportVersion).where(ImportVersion.batch_id == batch.id)
        )

    repo_root = _repository_root()
    catalog = load_metric_catalog(repo_root / "config/metrics/flow_v1_metrics.yaml")
    snapshot_service = MetricSnapshotService()
    snapshots = [
        snapshot_service.create_snapshot(
            session, batch_id=batch.id, as_of_month=month, catalog=catalog
        )
        for month in _ANALYSIS_MONTH_KEYS
    ]
    session.flush()
    policy = load_analysis_policy(
        repo_root / "services/api/config/analysis/flow-logistics-v1.yaml"
    )
    run = AnalysisRunService().create_run(
        session, snapshot_id=snapshots[-1].id, loaded_policy=policy
    )
    if version is None:
        raise RuntimeError(f"批次 {batch.id} 缺少已导入版本（装载状态不一致）")
    return {
        "batch_id": str(batch.id),
        "import_version_id": str(version.id),
        "metric_snapshot_ids": [str(s.id) for s in snapshots],
        "analysis_run_id": str(run.id),
        "analysis_run_status": run.status,
        "months": list(_ANALYSIS_MONTH_KEYS),
    }


__all__ = ["seed_damai_demo"]
