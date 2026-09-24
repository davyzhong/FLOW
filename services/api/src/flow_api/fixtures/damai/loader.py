"""大麦演示数据装载器（Task 4 / Task A3 独立身份与审核链）。

装载顺序（每步过领域服务，不绕过质量/对账）：
1. 复用固定 bootstrap enterprise UUID（授权契约单企业），幂等改名为大麦；
2. 两份合成财报（FY2025/FY2026）从发行版 `fixtures/damai/statements/damai_fy*.yaml`
   以独立 synthetic 身份 `DAMAI.SYN` 导入（source SHA 来自发行版文件），
   经归一化（damai_syn 专属映射段）后由 ReviewService.publish 过勾稽门禁发布
   ——不直改 status，不读取/冒充 9988.HK 等任何真实公司 fixture；
3. 输出机器可读 receipt。

slice-2a：工作簿导入（IntakeService 全链）→ 12 个月指标快照 → 最新 AnalysisRun。
slice-2b（B2）：Finding 状态机推进（candidate→in_review→approved）、四段式结论
（含发行包 manifest SHA + canonical 记录集追溯）、三类冻结（内部分析报告 /
两年客观财报快照 / 经营概览）与信号 receipt。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import select, text

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.data_contract.contract import load_contract
from flow_api.fixtures.damai.generator import build_damai_package
from flow_api.fixtures.damai.validation import validate_damai_package
from flow_api.infrastructure.models.analytics import Conclusion, Finding
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
from flow_api.investigation.state_machines import apply_finding_decision
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService
from flow_api.operations.freeze import freeze_operations_overview
from flow_api.publishing.objective_freeze import freeze_objective_statement_report
from flow_api.publishing.service import digest_view, freeze_report_snapshot
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report
from flow_api.statements.review import ReviewService


def _release_statements_path(fy: str) -> Path:
    """发行版合成财报 yaml（fixtures/damai/statements/damai_fy*.yaml）。"""

    relative = Path(f"fixtures/damai/statements/damai_{fy.lower()}.yaml")
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"未找到 {relative}（先运行 scripts/build_damai_demo.py 构建发行版）"
    )


_DAMAI_FY: tuple[str, ...] = ("FY2025", "FY2026")
# 分析窗口：与大麦 profile 的 24 个月合同一致（后 12 个月为分析期）
_ANALYSIS_MONTH_KEYS: tuple[int, ...] = tuple(
    2025 * 100 + m for m in range(9, 13)
) + tuple(2026 * 100 + m for m in range(1, 9))
_BOOTSTRAP_ID = "00000000-0000-0000-0000-00000000d001"
_DAMAI_COMPANY_NAME = "大麦物流集团（synthetic 演示企业）"
_DAMAI_CYCLE_PERIOD_KEY = "2026-08"  # 分析周期截止月（B1：显式绑定，不依赖引导周期）


def _damai_analysis_cycle_id(session: Any) -> str:
    """建立/复用 bootstrap 企业下截止月 2026-08 的 AnalysisCycle（幂等）。"""

    row = session.execute(
        text(
            "INSERT INTO analysis_cycle (id, enterprise_id, period_key, status, created_at)"
            " VALUES (gen_random_uuid(), :eid, :period, 'open', now())"
            " ON CONFLICT (enterprise_id, period_key) DO NOTHING"
            " RETURNING id"
        ),
        {"eid": _BOOTSTRAP_ID, "period": _DAMAI_CYCLE_PERIOD_KEY},
    ).scalar()
    if row is not None:
        return str(row)
    return str(
        session.execute(
            text(
                "SELECT id FROM analysis_cycle"
                " WHERE enterprise_id = :eid AND period_key = :period"
            ),
            {"eid": _BOOTSTRAP_ID, "period": _DAMAI_CYCLE_PERIOD_KEY},
        ).scalar_one()
    )


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
    """装载大麦演示数据：enterprise 配置 + 两份财报导入/归一化/审核发布。

    事务语义（B1）：全程 flush-only，只在调用方顶层提交；任一步骤失败时
    调用方 rollback 即零部分数据。入口先过数据包不变量门禁，拒写半成品。
    """

    package_validation = validate_damai_package(build_damai_package())
    if not package_validation["valid"]:
        raise RuntimeError(
            "大麦数据包不变量校验失败，拒绝装载："
            + ",".join(package_validation["invariant_codes"])
        )

    enterprise = _upsert_enterprise(session)
    review = ReviewService(session)
    reports: list[dict[str, Any]] = []
    for fy in _DAMAI_FY:
        yaml_path = _release_statements_path(fy)
        source_bytes = yaml_path.read_bytes()
        report = import_statement_report(
            session,
            company_name="大麦物流",
            stock_code="DAMAI.SYN",
            report_kind="年报",
            period_label=fy,
            payload=yaml.safe_load(source_bytes.decode("utf-8")),
            source_ref=f"fixtures/damai/statements/damai_{fy.lower()}.yaml",
            source_sha256=_sha256_of(yaml_path),
        )
        session.flush()
        normalize_report(session, report)
        if report.status != "published":
            # 正式审核链：勾稽门禁通过才发布；已发布（二次 seed）则跳过
            review.publish(report.id, operator="damai-demo-seed")
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
                "stock_code": report.stock_code,
                "status": report.status,
                "normalized_rows": int(normalized),
                "source_sha256": report.source_sha256 or "",
            }
        )
    session.flush()
    receipt: dict[str, Any] = {"enterprise": enterprise, "reports": reports}
    receipt["analytics"] = _seed_analytics(session)
    receipt["workflow"] = _seed_workflow(session, reports, receipt["analytics"])
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
        # 首次装载：标准工作簿走完整 IntakeService 导入链；
        # B1：批次显式绑定截止月 2026-08 的 AnalysisCycle（不依赖全库最早周期）
        cycle_id = _damai_analysis_cycle_id(session)
        workbook = _release_workbook_path()
        stored, proposal, candidate, report = _intake_inputs(workbook)
        intake = IntakeService(session)
        batch = intake.create_batch("damai-demo-v1", analysis_cycle_id=cycle_id)
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


_WORKFLOW_ACTOR = "damai-demo-seed"


def _release_manifest_sha256() -> str:
    """发行包 manifest.json 的 SHA（结论与 receipt 的发行包追溯锚点）。"""

    relative = Path("fixtures/damai/manifest.json")
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file():
            return _sha256_of(candidate)
    raise FileNotFoundError(
        f"未找到 {relative}（先运行 scripts/build_damai_demo.py 构建发行版）"
    )


def _conclusion_sections(
    finding: Finding,
    *,
    manifest_sha: str,
    canonical_ref: str,
    evidence_refs: str,
) -> dict[str, str]:
    """四段式结论：业务叙事 + 发行包/canonical 双追溯（不伪造数值）。"""

    trace = (
        f"数据来源：发行包 fixtures/damai（manifest sha256={manifest_sha}）；"
        f"canonical 记录集 {canonical_ref}；证据引用：{evidence_refs}。"
    )
    impact = f"{finding.impact_amount}"
    if finding.finding_type == "revenue_growth":
        return {
            "verified_facts": (
                f"分析期收入同比增长，影响额 {impact} 百万元；"
                "植入事件 E1（电商大客户放量）与 E6（分析期后 6 月客户轮换）"
                f"为主要驱动，月度明细与客户维度交叉验证一致。{trace}"
            ),
            "analysis_judgment": (
                "增长集中在电商客群与跨境包裹产品线，属于结构性放量而非价格漂移；"
                "E6 客户轮换表明增长对新客户获取存在依赖，留存质量需持续跟踪。"
            ),
            "open_questions": (
                "E3（DM-CUST-007/019 逾期桶放大 1.35×、回款 0.75×）未触发 "
                "ar_cash_impact playbook 阈值，收入增长的现金转换质量待应收账龄切片复核；"
                "E5（2026-05/06 经营现金流收窄至 0.55×）与收入放量的背离需专项说明。"
            ),
            "recommendation": (
                "对电商客群续约账期与定价做专项复核；将 E3 逾期客户列入回款督办清单；"
                "下周期跟踪 E5 现金流收窄是否随收入放量收敛。"
            ),
        }
    if finding.finding_type == "fulfillment_cost_increase":
        return {
            "verified_facts": (
                f"分析期履约成本同比增加，影响额 {impact} 百万元；"
                "植入事件 E2（末端冷链运力扩张）为主要驱动，成本明细与分部序列"
                f"交叉验证一致。{trace}"
            ),
            "analysis_judgment": (
                "成本增加与冷链产品收入结构匹配，属于产能前置投入；"
                "E4（国内仓配事业部预算上调 1.12×，其余 1.03×）作为预算差异次级解释："
                "预算口径本身已上调，实际超预算幅度小于名义成本增幅。"
            ),
            "open_questions": (
                "E4 预算上调的审批依据与冷链产能利用率的爬坡曲线尚未入模；"
                "E3 逾期放大对履约资源占用的间接影响待应收切片数据补充后评估。"
            ),
            "recommendation": (
                "按 E4 调整后的预算口径重算履约成本差异；对冷链产能利用率设月度门槛，"
                "连续两月不达标即触发扩产复审。"
            ),
        }
    return {
        "verified_facts": f"Finding 影响额 {impact} 百万元，证据链齐备。{trace}",
        "analysis_judgment": "信号由 playbook 阈值过滤产生，业务解释见证据引用。",
        "open_questions": "待业务侧补充背景后复核。",
        "recommendation": "纳入下周期经营例会跟踪清单。",
    }


def _build_signals(
    findings: list[Finding], *, canonical_ref: str
) -> list[dict[str, str]]:
    """六个植入事件 → 可追溯信号：只挂到真实存在的 Finding/证据/结论。"""

    by_type = {finding.finding_type: finding for finding in findings}
    revenue = by_type.get("revenue_growth")
    fulfillment = by_type.get("fulfillment_cost_increase")
    any_finding = findings[0] if findings else None

    def finding_ref(finding: Finding | None, suffix: str = "") -> str:
        if finding is None:
            return canonical_ref
        return f"finding:{finding.id}{suffix}"

    return [
        {
            "event_code": "E1",
            "description": "电商大客户放量驱动收入增长",
            "channel": "finding" if revenue is not None else "conclusion",
            "reference": finding_ref(revenue or any_finding),
        },
        {
            "event_code": "E2",
            "description": "末端冷链运力扩张推高履约成本",
            "channel": "finding" if fulfillment is not None else "conclusion",
            "reference": finding_ref(fulfillment or any_finding),
        },
        {
            "event_code": "E3",
            "description": "DM-CUST-007/019 逾期桶放大 1.35×、回款 0.75×",
            "channel": "evidence",
            "reference": canonical_ref,
        },
        {
            "event_code": "E4",
            "description": "国内仓配事业部预算上调 1.12×（其余 1.03×）",
            "channel": "conclusion",
            "reference": finding_ref(
                fulfillment or any_finding, " conclusion.analysis_judgment"
            ),
        },
        {
            "event_code": "E5",
            "description": "2026-05/06 经营现金流收窄至 0.55×",
            "channel": "conclusion",
            "reference": finding_ref(
                revenue or any_finding, " conclusion.open_questions"
            ),
        },
        {
            "event_code": "E6",
            "description": "分析期后 6 月客户轮换（第二增长客户组）",
            "channel": "evidence" if revenue is not None else "conclusion",
            "reference": finding_ref(revenue or any_finding, " evidence"),
        },
    ]


def _seed_workflow(
    session: Any, reports: list[dict[str, Any]], analytics: dict[str, Any]
) -> dict[str, Any]:
    """Finding 状态机推进 + 四段式结论 + 三类冻结（全程 flush-only，幂等）。

    幂等约定：结论只在缺失时写入；状态机按当前状态推进（candidate→submitted，
    首个 Finding 进一步 approved）；三类冻结均为内容寻址，同内容复用版本。
    """

    run_id = UUID(analytics["analysis_run_id"])
    canonical_ref = f"import-version:{analytics['import_version_id']}"
    manifest_sha = _release_manifest_sha256()
    findings = list(
        session.scalars(
            select(Finding)
            .where(Finding.analysis_run_id == run_id)
            .order_by(Finding.finding_type, Finding.id)
        )
    )
    for index, finding in enumerate(findings):
        conclusion = session.scalar(
            select(Conclusion).where(Conclusion.finding_id == finding.id)
        )
        if conclusion is None:
            evidence_refs = ",".join(
                str(object_id)
                for object_id in session.scalars(
                    text("SELECT object_id FROM evidence WHERE finding_id = :fid"),
                    {"fid": str(finding.id)},
                )
            )
            conclusion = Conclusion(
                finding=finding,
                **_conclusion_sections(
                    finding,
                    manifest_sha=manifest_sha,
                    canonical_ref=canonical_ref,
                    evidence_refs=evidence_refs,
                ),
            )
            session.add(conclusion)
            session.flush()
        if finding.status == "candidate":
            apply_finding_decision(
                session,
                finding,
                "submitted",
                reviewer=_WORKFLOW_ACTOR,
                comment="演示数据：结论齐备，提交复核",
            )
        if index == 0 and finding.status == "in_review":
            apply_finding_decision(
                session,
                finding,
                "approved",
                reviewer=_WORKFLOW_ACTOR,
                comment="演示数据：证据全部已验证且结论四段齐备，签发",
            )
    session.flush()

    last_snapshot_id = UUID(analytics["metric_snapshot_ids"][-1])
    report_snapshot, view = freeze_report_snapshot(
        session, metric_snapshot_id=last_snapshot_id, analysis_run_id=run_id
    )
    objective_entries = []
    overview_entries = []
    for report in reports:
        frozen = freeze_objective_statement_report(
            session, report_id=UUID(report["report_id"])
        )
        objective_entries.append(
            {
                "fy": report["fy"],
                "snapshot_id": str(frozen.id),
                "version": int(frozen.version),
                "payload_hash": str(frozen.payload_hash),
            }
        )
        overview = freeze_operations_overview(
            session, report_id=UUID(report["report_id"])
        )
        overview_entries.append(
            {
                "fy": report["fy"],
                "snapshot_id": str(overview.id),
                "version": int(overview.version),
                "payload_hash": str(overview.payload_hash),
            }
        )
    session.flush()
    return {
        "manifest_sha256": manifest_sha,
        "findings": [
            {
                "finding_id": str(finding.id),
                "finding_type": str(finding.finding_type),
                "status": str(finding.status),
            }
            for finding in findings
        ],
        "signals": _build_signals(findings, canonical_ref=canonical_ref),
        "freezes": {
            "internal_report": {
                "report_snapshot_id": str(report_snapshot.id),
                "version": int(report_snapshot.version),
                "view_sha256": digest_view(view),
            },
            "objective_statements": objective_entries,
            "operations_overview": overview_entries,
        },
    }


__all__ = ["seed_damai_demo"]
