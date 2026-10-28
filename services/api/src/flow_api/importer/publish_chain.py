"""导入账套发布链桥接（R5 九页接线）。

把已校验的科目余额表数据集升格为治理发布链：
CanonicalPackage（科目类别→五管理科目聚合）→ load_canonical_package 直写
canonical（Period/Organization/ManagementAccount/FactFinancialActual + SourceRecord
溯源）→ 勾稽写 ReconciliationResult → IntakeService.publish_import 复用发布门禁
→ trial_balance_v1 目录逐期间 MetricSnapshot → 最新期间 AnalysisRun。

红线兑现：不改 dashboard service；不重复造业务事实源——导入行是唯一事实来源，
canonical 事实表是唯一治理事实存储，九页经 DashboardSourceRepository 读取。

口径对齐铁律：本模块的类别聚合算术必须与 normalization.derive_metrics 逐位一致
（revenue=Σ损益贷方、expenses=Σ损益借方、三类=Σ期末余额；成本类余额不进基座，
与直读口径一致），由 tests/importer 口径等价测试锁定。

不可变源工件：发布时把已校验行确定性 JSON 序列化写入 LocalObjectStore
（原始上传文件不留存于服务端；dataset 行保留 source_filename 供用户对照）。

删除语义：withdraw_dataset_chain 子表先行级联下线整条链；不可变对象存储的
工件字节保留（内容寻址，孤儿字节由备份/清理流程识别）。
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.data_contract.persistence import load_canonical_package
from flow_api.data_contract.records import (
    BatchRecord,
    CanonicalPackage,
    FinancialActualRecord,
    ManagementAccountRecord,
    OrganizationRecord,
    PeriodRecord,
    ScenarioVersionRecord,
)
from flow_api.importer.account_mapping import load_account_groups, map_balance_rows
from flow_api.importer.income_items import INCOME_ITEM_ACCOUNTS, map_income_items
from flow_api.importer.store import ImportStore
from flow_api.infrastructure.local_object_store import LocalObjectStore
from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    DriverContribution,
    Evidence,
    Finding,
    FindingScoreComponent,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.canonical import FactFinancialActual, Period
from flow_api.infrastructure.models.cockpit import ActionItem
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
    SourceRecord,
    WarningAcknowledgement,
)
from flow_api.intake.service import IntakeService
from flow_api.intake.source_storage import StoredSource
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService
from flow_api.settings import get_settings

_BATCH_NAME_PREFIX = "import-dataset-"
_ORG_CODE = "IMPORTED_ENTITY"
_ACTUAL_SCENARIO = "ACTUAL"
_BUDGET_SCENARIO = "BUDGET"
_ZERO = Decimal("0")
# (科目类别, 管理科目码, 管理科目名)；与 trial_balance_v1_metrics.yaml 的
# financial_account 声明一一对应
_CATEGORY_ACCOUNTS: tuple[tuple[str, str, str], ...] = (
    ("资产", "TB_ASSET", "资产类期末余额"),
    ("负债", "TB_LIABILITY", "负债类期末余额"),
    ("权益", "TB_EQUITY", "权益类期末余额"),
    ("损益", "TB_REVENUE", "损益贷方发生额（收入）"),
    ("损益", "TB_EXPENSE", "损益借方发生额（费用）"),
)
_ACCOUNT_CODES: tuple[str, ...] = tuple(code for _, code, _ in _CATEGORY_ACCOUNTS)


def _repository_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到仓库根（templates/excel/flow_v1_contract.yaml）")


def batch_name_for(dataset_id: str) -> str:
    return f"{_BATCH_NAME_PREFIX}{dataset_id}"


def find_chain_batch(session: Session, dataset_id: str) -> AnalysisBatch | None:
    return session.scalar(
        select(AnalysisBatch).where(AnalysisBatch.name == batch_name_for(dataset_id))
    )


def _period_amounts(
    balances: list[dict[str, object]],
) -> dict[str, dict[str, Decimal]]:
    """按期间×管理科目聚合；算术与 normalization.derive_metrics 逐位一致。"""
    periods: dict[str, dict[str, Decimal]] = {}
    for row in balances:
        period = str(row["period"])
        category = str(row["account_category"])
        bucket = periods.setdefault(period, {code: _ZERO for code in _ACCOUNT_CODES})
        if category == "损益":
            bucket["TB_REVENUE"] += row["credit_amount"]  # type: ignore[operator]
            bucket["TB_EXPENSE"] += row["debit_amount"]  # type: ignore[operator]
        elif category == "资产":
            bucket["TB_ASSET"] += row["closing_balance"]  # type: ignore[operator]
        elif category == "负债":
            bucket["TB_LIABILITY"] += row["closing_balance"]  # type: ignore[operator]
        elif category == "权益":
            bucket["TB_EQUITY"] += row["closing_balance"]  # type: ignore[operator]
        # 成本类余额不进基座（期末结转后应为 0；与直读口径一致，不虚构归属）
    return periods


def _artifact_bytes(
    dataset_name: str,
    balances: list[dict[str, object]],
    income_rows: list[dict[str, object]] | None = None,
    bank_rows: list[dict[str, object]] | None = None,
) -> bytes:
    """已校验行的确定性 JSON 序列化（sort_keys + 紧凑分隔符，同数据同 SHA）。"""
    payload = {
        "artifact": "flow.importer.trial-balance.v1",
        "dataset_name": dataset_name,
        "rows": [
            {
                "period": row["period"],
                "account_code": row["account_code"],
                "account_name": row["account_name"],
                "account_category": row["account_category"],
                "direction": row["direction"],
                "opening_balance": str(row["opening_balance"]),
                "debit_amount": str(row["debit_amount"]),
                "credit_amount": str(row["credit_amount"]),
                "closing_balance": str(row["closing_balance"]),
            }
            for row in balances
        ],
        "income_statement_rows": [
            {
                "period": row["period"],
                "item": row["item"],
                "current_amount": str(row["current_amount"]),
                "ytd_amount": str(row["ytd_amount"]),
            }
            for row in (income_rows or [])
        ],
        "bank_statement_rows": [
            {
                "period": row["period"],
                "trade_date": row["trade_date"],
                "summary": row["summary"],
                "income_amount": str(row["income_amount"]),
                "expense_amount": str(row["expense_amount"]),
                "account_balance": str(row["account_balance"]),
            }
            for row in (bank_rows or [])
        ],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


@dataclass(frozen=True, slots=True)
class _PackageDraft:
    package: CanonicalPackage
    identity: Decimal
    # M2 净利润勾稽：(期间, TB 净利润, IS 净利润) 差异超容差的清单
    net_mismatches: tuple[tuple[str, str, str], ...]


def _bank_flow_by_period(
    bank_rows: list[dict[str, object]] | None,
) -> dict[str, dict[str, Decimal]]:
    """期间 × 现金收付口径（CASH_INFLOW/CASH_OUTFLOW）聚合（M3）。"""
    flows: dict[str, dict[str, Decimal]] = {}
    for row in bank_rows or []:
        period = str(row["period"])
        bucket = flows.setdefault(period, {"CASH_INFLOW": _ZERO, "CASH_OUTFLOW": _ZERO})
        bucket["CASH_INFLOW"] += row["income_amount"]  # type: ignore[operator]
        bucket["CASH_OUTFLOW"] += row["expense_amount"]  # type: ignore[operator]
    return flows


def _tb_net_profit_by_period(balances: list[dict[str, object]]) -> dict[str, Decimal]:
    """期间 × TB 净利润（Σ损益贷 − Σ损益借，全部损益类科目）。"""
    nets: dict[str, Decimal] = {}
    for row in balances:
        if str(row["account_category"]) != "损益":
            continue
        period = str(row["period"])
        nets[period] = nets.get(period, _ZERO) + row["credit_amount"] - row["debit_amount"]  # type: ignore[operator]
    return nets


def _build_package(
    dataset_id: str,
    dataset_name: str,
    balances: list[dict[str, object]],
    income_rows: list[dict[str, object]] | None = None,
    bank_rows: list[dict[str, object]] | None = None,
) -> _PackageDraft:
    """构造 CanonicalPackage；返回包与勾稽信息。

    事实分层（R5 基线 → M1 → M2）：① 类别五科目（等价测试锚定，零扰动）；
    ② 科目级明细组（前缀映射、组内方向净额，未命中不进组不补零）；
    ③ 利润表 IS_* 项目（损益明细唯一来源；净利润与 TB 逐期勾稽）。
    期间集 = 余额表 ∪ 利润表（仅利润表期间的部分指标如实缺席）。
    """
    tb_periods = sorted({str(row["period"]) for row in balances})
    amounts = _period_amounts(balances)
    last = amounts[tb_periods[-1]]
    identity = last["TB_ASSET"] - last["TB_LIABILITY"] - last["TB_EQUITY"]
    groups = load_account_groups(_repository_root() / "config/importer/account_mapping_v1.yaml")
    mapping = map_balance_rows(balances, groups)
    detail_periods = sorted(mapping.amounts)

    income = map_income_items(income_rows or [])
    bank_flows = _bank_flow_by_period(bank_rows)
    periods = sorted({*tb_periods, *income.periods, *bank_flows})

    # M2 净利润勾稽：期间交集内 |TB 净利润 − IS 净利润| > 0.01 记不一致
    tb_nets = _tb_net_profit_by_period(balances)
    net_mismatches: list[tuple[str, str, str]] = []
    for period in sorted(set(tb_nets) & set(income.amounts)):
        if "IS_NET_PROFIT" not in income.amounts[period]:
            continue
        tb_net = tb_nets[period]
        is_net = income.amounts[period]["IS_NET_PROFIT"]
        if abs(tb_net - is_net) > Decimal("0.01"):
            net_mismatches.append((period, str(tb_net), str(is_net)))

    package = CanonicalPackage(
        batch=BatchRecord(
            batch_code=batch_name_for(dataset_id),
            contract_version="trial-balance-v1",
            analysis_start_month=periods[0],
            analysis_end_month=periods[-1],
            comparison_start_month=periods[0],
            comparison_end_month=periods[-1],
            currency="CNY",
            actual_scenario_code=_ACTUAL_SCENARIO,
            budget_scenario_code=_BUDGET_SCENARIO,
            budget_version_label="imported-trial-balance",
            generated_at=datetime.now(UTC).replace(microsecond=0),
        ),
        periods=tuple(
            PeriodRecord(
                month_key=period,
                year=int(period[:4]),
                quarter=(int(period[5:7]) - 1) // 3 + 1,
                month=int(period[5:7]),
                window="analysis",
            )
            for period in periods
        ),
        organizations=(
            OrganizationRecord(code=_ORG_CODE, name=dataset_name or "导入主体", level="entity"),
        ),
        customer_segments=(),
        customers=(),
        logistics_products=(),
        regions=(),
        management_accounts=tuple(
            ManagementAccountRecord(code=code, name=name, category=label)
            for label, code, name in _CATEGORY_ACCOUNTS
        )
        + tuple(
            ManagementAccountRecord(
                code=group.management_account, name=group.name, category="明细组"
            )
            for group in groups
        )
        + tuple(
            ManagementAccountRecord(code=account, name=item, category="利润表")
            for item, account in INCOME_ITEM_ACCOUNTS
            # 只登记实际映射到的 IS_* 科目（空项目不进包）
            if any(account in income.amounts[period] for period in income.periods)
        )
        + tuple(
            ManagementAccountRecord(code=code, name=name, category="现金口径")
            for code, name in (
                ("CASH_INFLOW", "现金流入（银行流水收付口径）"),
                ("CASH_OUTFLOW", "现金流出（银行流水收付口径）"),
            )
            if bank_flows
        ),
        scenario_versions=(
            ScenarioVersionRecord(code=_ACTUAL_SCENARIO, name="实际", scenario_type="actual"),
            ScenarioVersionRecord(code=_BUDGET_SCENARIO, name="预算", scenario_type="budget"),
        ),
        operating_actuals=(),
        financial_actuals=tuple(
            FinancialActualRecord(
                # canonical 载荷要求 record_id 为 UUID；uuid5 保证同数据集重复发布同 id
                record_id=str(
                    uuid.uuid5(NAMESPACE_URL, f"flow:importer:{dataset_id}:{period}:{code}")
                ),
                month_key=period,
                organization_code=_ORG_CODE,
                management_account_code=code,
                amount=amounts[period][code],
            )
            for period in periods
            for code in _ACCOUNT_CODES
        )
        + tuple(
            FinancialActualRecord(
                record_id=str(
                    uuid.uuid5(
                        NAMESPACE_URL,
                        f"flow:importer:{dataset_id}:{period}:{group.management_account}",
                    )
                ),
                month_key=period,
                organization_code=_ORG_CODE,
                management_account_code=group.management_account,
                amount=mapping.amounts[period][group.management_account],
            )
            # 空组不写 0 金额事实（缺席≠零：0 会冒充真实余额并让环比 0/0 硬崩）
            for period in detail_periods
            for group in groups
            if group.management_account in mapping.matched_by_period.get(period, set())
        )
        + tuple(
            FinancialActualRecord(
                record_id=str(
                    uuid.uuid5(
                        NAMESPACE_URL,
                        f"flow:importer:{dataset_id}:{period}:{account}",
                    )
                ),
                month_key=period,
                organization_code=_ORG_CODE,
                management_account_code=account,
                amount=income.amounts[period][account],
            )
            for period in income.periods
            for account in income.amounts[period]
        )
        + tuple(
            FinancialActualRecord(
                record_id=str(
                    uuid.uuid5(
                        NAMESPACE_URL,
                        f"flow:importer:{dataset_id}:{period}:{code}",
                    )
                ),
                month_key=period,
                organization_code=_ORG_CODE,
                management_account_code=code,
                amount=bank_flows[period][code],
            )
            for period in bank_flows
            for code in ("CASH_INFLOW", "CASH_OUTFLOW")
        ),
        monthly_budgets=(),
        ar_collections=(),
    )
    return _PackageDraft(package=package, identity=identity, net_mismatches=tuple(net_mismatches))


def publish_dataset(session: Session, store: ImportStore, dataset_id: str) -> dict[str, object]:
    """把导入数据集发布为治理链；幂等（同数据集重复发布返回既有 receipt）。"""
    dataset = next((row for row in store.list_datasets() if row["id"] == dataset_id), None)
    if dataset is None:
        raise LookupError(f"dataset not found: {dataset_id}")
    balances = store.dataset_balances(dataset_id)
    if not balances:
        raise ValueError("数据集没有科目余额行，无法发布")

    existing = find_chain_batch(session, dataset_id)
    if existing is not None:
        return chain_receipt(session, dataset_id)

    income_rows = store.dataset_income_items(dataset_id)
    bank_rows = store.dataset_bank_transactions(dataset_id)
    draft = _build_package(
        dataset_id,
        str(dataset["name"]),
        balances,
        income_rows or None,
        bank_rows or None,
    )
    package = draft.package
    uploaded = LocalObjectStore(get_settings().object_directory).put_immutable(
        _artifact_bytes(str(dataset["name"]), balances, income_rows, bank_rows),
        f"{dataset_id}-trial-balance.json",
    )

    intake = IntakeService(session)
    batch = intake.create_batch(
        batch_name_for(dataset_id),
        f"导入数据集发布链：{dataset['name']}",
    )
    source = intake.attach_source(
        batch.id,
        StoredSource(
            sha256=uploaded.sha256,
            object_key=uploaded.object_key,
            size_bytes=uploaded.size_bytes,
            content_type="application/json",
            original_filename=f"{dataset_id}-trial-balance.json",
        ),
    )
    version = ImportVersion(
        batch_id=batch.id,
        sequence=1,
        status="validating",
        is_published=False,
        summary={"dataset_id": dataset_id, "source": "importer.publish_chain"},
    )
    session.add(version)
    session.flush()
    load_canonical_package(session, package, source, import_version=version)

    session.add(
        ReconciliationResult(
            import_version_id=version.id,
            reconciliation_code="trial_balance_identity",
            passed=draft.identity == _ZERO,
            expected_value="0",
            actual_value=str(draft.identity),
            details={
                "difference": str(draft.identity),
                "tolerance": "0",
                "description": "资产总计 − 负债总计 − 权益总计（最新期间期末口径）",
            },
        )
    )
    # M2 净利润勾稽：余额表损益（Σ贷−Σ借）逐期对照利润表净利润
    session.add(
        ReconciliationResult(
            import_version_id=version.id,
            reconciliation_code="income_statement_net_profit",
            passed=not draft.net_mismatches,
            expected_value="0",
            actual_value=str(len(draft.net_mismatches)),
            details={
                "difference": ";".join(
                    f"{period}:TB={tb_net},IS={is_net}"
                    for period, tb_net, is_net in draft.net_mismatches
                ),
                "tolerance": "0.01",
                "description": "科目余额表损益净额 − 利润表净利润（逐期间，容差 0.01）",
            },
        )
    )
    session.flush()
    # 与 validate_import 同语义：无 blocking issue，勾稽决定 ready/blocked
    version.status = "ready"
    batch.status = "ready"
    session.flush()

    intake.publish_import(version.id)

    catalog = load_metric_catalog(
        _repository_root() / "config/metrics/trial_balance_v1_metrics.yaml"
    )
    snapshot_service = MetricSnapshotService()
    snapshots = [
        snapshot_service.create_snapshot(
            session,
            batch_id=batch.id,
            as_of_month=int(record.month_key.replace("-", "")),
            catalog=catalog,
        )
        for record in package.periods
    ]
    session.flush()
    policy = load_analysis_policy(
        _repository_root() / "services/api/config/analysis/flow-logistics-v1.yaml"
    )
    AnalysisRunService().create_run(session, snapshot_id=snapshots[-1].id, loaded_policy=policy)
    session.flush()
    return chain_receipt(session, dataset_id)


def chain_receipt(session: Session, dataset_id: str) -> dict[str, object]:
    """数据集发布链的只读回执；链不存在时 published=False。"""
    batch = find_chain_batch(session, dataset_id)
    if batch is None:
        return {"dataset_id": dataset_id, "published": False}
    version = session.scalar(
        select(ImportVersion)
        .where(ImportVersion.batch_id == batch.id, ImportVersion.is_published.is_(True))
        .order_by(ImportVersion.sequence.desc())
    )
    snapshots = tuple(
        session.scalars(
            select(MetricSnapshot)
            .join(Period, Period.id == MetricSnapshot.as_of_period_id)
            .where(MetricSnapshot.batch_id == batch.id)
            .order_by(Period.month_key, MetricSnapshot.version)
        )
    )
    run = (
        session.scalar(
            select(AnalysisRun)
            .where(AnalysisRun.import_version_id == version.id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
            .limit(1)
        )
        if version is not None
        else None
    )
    return {
        "dataset_id": dataset_id,
        "batch_id": str(batch.id),
        "import_version_id": str(version.id) if version is not None else None,
        "metric_snapshot_ids": [str(item.id) for item in snapshots],
        "analysis_run_id": str(run.id) if run is not None else None,
        "analysis_run_status": str(run.status) if run is not None else None,
        "published": batch.status == "published" and run is not None,
        "is_active_source": _is_latest_run(session, run.id) if run is not None else False,
    }


def _is_latest_run(session: Session, run_id: UUID) -> bool:
    """与 DashboardSourceRepository.get_latest 同口径：期间最新优先。"""
    latest = session.scalar(
        select(AnalysisRun.id)
        .join(MetricSnapshot, MetricSnapshot.id == AnalysisRun.metric_snapshot_id)
        .join(Period, Period.id == MetricSnapshot.as_of_period_id)
        .where(
            AnalysisRun.status == "published",
            MetricSnapshot.status == "published",
        )
        .order_by(
            Period.month_key.desc(),
            AnalysisRun.created_at.desc(),
            AnalysisRun.id.desc(),
        )
        .limit(1)
    )
    return latest == run_id


def withdraw_dataset_chain(session: Session, dataset_id: str) -> bool:
    """删除数据集时级联下线其发布链（子表先行）；返回是否找到链。"""
    batch = find_chain_batch(session, dataset_id)
    if batch is None:
        return False
    batch_id: UUID = batch.id
    version_ids = tuple(
        session.scalars(select(ImportVersion.id).where(ImportVersion.batch_id == batch_id))
    )
    snapshot_ids = tuple(
        session.scalars(select(MetricSnapshot.id).where(MetricSnapshot.batch_id == batch_id))
    )
    run_ids = tuple(
        session.scalars(
            select(AnalysisRun.id).where(AnalysisRun.import_version_id.in_(version_ids))
        )
    )
    finding_ids = tuple(
        session.scalars(select(Finding.id).where(Finding.analysis_run_id.in_(run_ids)))
    )
    result_ids = tuple(
        session.scalars(
            select(AnalysisResult.id).where(AnalysisResult.analysis_run_id.in_(run_ids))
        )
    )
    issue_ids = tuple(
        session.scalars(
            select(QualityIssue.id).where(QualityIssue.import_version_id.in_(version_ids))
        )
    )
    # 行动项按 finding 挂（本链 findings 的行动项全部下线）
    session.execute(sa_delete(ActionItem).where(ActionItem.finding_id.in_(finding_ids)))
    session.execute(
        sa_delete(WarningAcknowledgement).where(
            WarningAcknowledgement.quality_issue_id.in_(issue_ids)
        )
    )
    if finding_ids:
        session.execute(sa_delete(Evidence).where(Evidence.finding_id.in_(finding_ids)))
        session.execute(
            sa_delete(DriverContribution).where(DriverContribution.finding_id.in_(finding_ids))
        )
        session.execute(
            sa_delete(FindingScoreComponent).where(
                FindingScoreComponent.finding_id.in_(finding_ids)
            )
        )
    session.execute(sa_delete(Finding).where(Finding.id.in_(finding_ids)))
    if result_ids:
        session.execute(
            sa_delete(AnalysisDriver).where(AnalysisDriver.analysis_result_id.in_(result_ids))
        )
    session.execute(sa_delete(AnalysisResult).where(AnalysisResult.id.in_(result_ids)))
    session.execute(sa_delete(AnalysisRun).where(AnalysisRun.id.in_(run_ids)))
    session.execute(sa_delete(MetricValue).where(MetricValue.metric_snapshot_id.in_(snapshot_ids)))
    session.execute(sa_delete(MetricSnapshot).where(MetricSnapshot.id.in_(snapshot_ids)))
    session.execute(sa_delete(QualityIssue).where(QualityIssue.id.in_(issue_ids)))
    session.execute(
        sa_delete(ReconciliationResult).where(
            ReconciliationResult.import_version_id.in_(version_ids)
        )
    )
    # canonical 事实行先删（fact→source_record 为 RESTRICT FK）；
    # Period/Organization/ManagementAccount/ScenarioVersion 为共享维度，不删
    session.execute(
        sa_delete(FactFinancialActual).where(FactFinancialActual.import_version_id.in_(version_ids))
    )
    session.execute(sa_delete(SourceRecord).where(SourceRecord.import_version_id.in_(version_ids)))
    session.execute(sa_delete(SourceFile).where(SourceFile.batch_id == batch_id))
    session.execute(sa_delete(ImportVersion).where(ImportVersion.id.in_(version_ids)))
    session.execute(sa_delete(AnalysisBatch).where(AnalysisBatch.id == batch_id))
    session.flush()
    return True
