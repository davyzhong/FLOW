"""CFO 驾驶舱模块服务（批次 C-2：资产负债 + 营运资金）。

数据纪律（与批次 A 同源）：
- 只读已冻结事实：已发布报表（DAMAI.SYN FY2022/FY2023，菜鸟申请稿 IFRS
  披露值）的归一化行 + canonical 项目映射；不重算、不补零；
- 无来源的结构块显式 unavailable（债务期限拆分、应收账龄明细、多主体排名），
  不渲染假数据（设计文档 §5.5/§5.6 与研发期适配说明）；
- 金额单位统一换算为人民币百万元（报表原值千元 ÷ 1000）；
- 每个数值块携带 report_id/snapshot 上下文（可追溯铁律）。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from flow_api.infrastructure.models.analytics import MetricSnapshot
from flow_api.infrastructure.models.statement import (
    StatementNormalizedItem,
    StatementReport,
)

_UNIT_TO_MILLION = Decimal("1000")  # 千元 → 百万元


class ModuleDataUnavailableError(RuntimeError):
    """模块数据未就绪（无已发布报表/无归一化行）。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ModuleFactContext:
    """两个报告期的归一化事实（canonical item → 百万元值）。"""

    current_report_id: UUID
    prior_report_id: UUID
    period_label: str
    prior_period_label: str
    snapshot_id: str
    current: dict[str, Decimal]
    prior: dict[str, Decimal]


def load_fact_context(session: Session, stock_code: str) -> ModuleFactContext:
    """装载最新两期已发布报表的归一化事实（canonical item 级）。"""

    reports = list(
        session.scalars(
            select(StatementReport)
            .options(selectinload(StatementReport.items))
            .where(
                StatementReport.stock_code == stock_code,
                StatementReport.status == "published",
                StatementReport.period_label.in_(("FY2022", "FY2023")),
            )
            .order_by(StatementReport.period_label)
        )
    )
    by_period = {report.period_label: report for report in reports}
    if "FY2023" not in by_period or "FY2022" not in by_period:
        raise ModuleDataUnavailableError(
            "module_statements_not_published",
            "模块所需的两期披露财报尚未发布",
        )
    current = by_period["FY2023"]
    prior = by_period["FY2022"]

    snapshot = session.scalar(
        select(MetricSnapshot)
        .where(MetricSnapshot.batch_id == _latest_batch_id(session))
        .order_by(MetricSnapshot.version.desc())
        .limit(1)
    )

    def collect(report: StatementReport) -> dict[str, Decimal]:
        rows = session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report.id,
                StatementNormalizedItem.item_id.isnot(None),
            )
        ).all()
        facts: dict[str, Decimal] = {}
        for row in rows:
            if row.item_id is None:
                continue
            for column, value in (
                ("end", row.value_end),
                ("begin", row.value_begin),
                ("cur", row.value_current),
                ("prior", row.value_prior),
            ):
                if value is not None:
                    facts[f"{row.item_id}:{column}"] = Decimal(str(value)) / _UNIT_TO_MILLION
        return facts

    return ModuleFactContext(
        current_report_id=current.id,
        prior_report_id=prior.id,
        period_label=current.period_label,
        prior_period_label=prior.period_label,
        snapshot_id=str(snapshot.id) if snapshot else "",
        current=collect(current),
        prior=collect(prior),
    )


def _latest_batch_id(session: Session) -> Any:
    from flow_api.infrastructure.models.intake import AnalysisBatch

    return session.scalar(
        select(AnalysisBatch.id).order_by(AnalysisBatch.created_at.desc()).limit(1)
    )


def _fact(ctx: ModuleFactContext, item_id: str, role: str = "end") -> Decimal | None:
    return ctx.current.get(f"{item_id}:{role}")


def _prior_fact(ctx: ModuleFactContext, item_id: str, role: str = "end") -> Decimal | None:
    return ctx.prior.get(f"{item_id}:{role}")


def _ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator in (None, Decimal("0")):
        return None
    assert denominator is not None
    return (numerator / denominator).quantize(Decimal("0.0001"))


def _kpi(
    name: str,
    value: Decimal | None,
    prior: Decimal | None,
    *,
    unit: str,
    unavailable_code: str | None = None,
    caliber_note: str | None = None,
) -> dict[str, Any]:
    if value is None:
        return {
            "name": name,
            "status": "unavailable",
            "unavailable_code": unavailable_code or "not_disclosed",
            "unit": unit,
            "caliber_note": caliber_note,
        }
    return {
        "name": name,
        "status": "available",
        "value": str(value),
        "prior_value": str(prior) if prior is not None else None,
        "unit": unit,
        "caliber_note": caliber_note,
    }


def build_balance_sheet_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """§5.5 资产负债：KPI ×8 + 结构 + 资本结构趋势；期限拆分 unavailable。"""

    total_assets = _fact(ctx, "bs.total_assets")
    total_liab = _fact(ctx, "bs.total_liab")
    equity = _fact(ctx, "bs.equity")
    cash = _fact(ctx, "bs.cash")
    ar = _fact(ctx, "bs.ar")
    inventory = _fact(ctx, "bs.inventory")
    debt = _fact(ctx, "bs.long_debt")  # 借款（长短期混合，口径注）
    debt_asset = _ratio(total_liab, total_assets)
    prior_total_assets = _prior_fact(ctx, "bs.total_assets")
    prior_total_liab = _prior_fact(ctx, "bs.total_liab")
    prior_equity = _prior_fact(ctx, "bs.equity")
    prior_cash = _prior_fact(ctx, "bs.cash")
    prior_ar = _prior_fact(ctx, "bs.ar")
    prior_inventory = _prior_fact(ctx, "bs.inventory")
    prior_debt = _prior_fact(ctx, "bs.long_debt")
    prior_debt_asset = _ratio(prior_total_liab, prior_total_assets)
    current_assets = _fact(ctx, "bs.current_assets")
    noncurrent_assets = (
        total_assets - current_assets
        if total_assets is not None and current_assets is not None
        else None
    )
    prior_current_assets = _prior_fact(ctx, "bs.current_assets")
    prior_noncurrent_assets = (
        prior_total_assets - prior_current_assets
        if prior_total_assets is not None and prior_current_assets is not None
        else None
    )

    kpis = [
        _kpi("总资产", total_assets, prior_total_assets, unit="百万元"),
        _kpi("总负债", total_liab, prior_total_liab, unit="百万元"),
        _kpi("所有者权益", equity, prior_equity, unit="百万元"),
        _kpi("资产负债率", debt_asset, prior_debt_asset, unit="ratio"),
        _kpi("货币资金", cash, prior_cash, unit="百万元"),
        _kpi("应收账款（含其他预付款）", ar, prior_ar, unit="百万元",
             caliber_note="申请稿混合口径行（贸易应收及其他预付款）"),
        _kpi("存货", inventory, prior_inventory, unit="百万元"),
        _kpi("有息负债（借款总额）", debt, prior_debt, unit="百万元",
             caliber_note="申请稿「借款」为长短期混合行；短债拆分未披露（U-CN 口径）"),
    ]
    charts: dict[str, Any] = {
        "asset_structure": {
            "title": "资产结构（流动/非流动）",
            "type": "treemap",
            "periods": [ctx.prior_period_label, ctx.period_label],
            "series": {
                "流动资产": [prior_current_assets, current_assets],
                "非流动资产": [prior_noncurrent_assets, noncurrent_assets],
            },
        },
        "liability_equity_structure": {
            "title": "负债与权益结构",
            "type": "ratio_bar",
            "periods": [ctx.prior_period_label, ctx.period_label],
            "series": {
                "负债合计": [prior_total_liab, total_liab],
                "所有者权益": [prior_equity, equity],
            },
        },
        "capital_structure_trend": {
            "title": "资本结构趋势",
            "type": "line",
            "periods": [ctx.prior_period_label, ctx.period_label],
            "series": {
                "资产负债率": [prior_debt_asset, debt_asset],
            },
            "note": "有息负债率需短债拆分，未披露 → unavailable",
        },
    }
    unavailable = [
        {
            "block": "债务期限结构",
            "code": "debt_maturity_split_not_disclosed",
            "reason": "申请稿「借款」为长短期混合行，期限拆分未披露",
        }
    ]
    return {
        "module": "balance-sheet",
        "title": "资产负债",
        "period": ctx.period_label,
        "prior_period": ctx.prior_period_label,
        "snapshot_id": ctx.snapshot_id,
        "report_ids": [str(ctx.current_report_id), str(ctx.prior_report_id)],
        "source_notice": (
            "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用；"
            "不构成公开财报 C 级能力证明"
        ),
        "unit": "百万元",
        "kpis": kpis,
        "charts": charts,
        "unavailable": unavailable,
    }


def build_working_capital_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """§5.6 营运资金：KPI ×8 + 趋势 + CCC 恒等；账龄/排名降级。"""

    revenue_cur = ctx.current.get("is.revenue:cur")
    cogs_cur = ctx.current.get("is.cogs:cur")
    ar_cur = _fact(ctx, "bs.ar")
    ar_begin = _fact(ctx, "bs.ar", "begin")
    inv_cur = _fact(ctx, "bs.inventory")
    inv_begin = _fact(ctx, "bs.inventory", "begin")
    ap_cur = _fact(ctx, "bs.ap")
    ap_begin = _fact(ctx, "bs.ap", "begin")

    def avg(cur: Decimal | None, begin: Decimal | None) -> Decimal | None:
        if cur is None or begin is None:
            return None
        return (cur + begin) / Decimal("2")

    ar_avg, inv_avg, ap_avg = avg(ar_cur, ar_begin), avg(inv_cur, inv_begin), avg(ap_cur, ap_begin)

    def days(avg_balance: Decimal | None, flow: Decimal | None) -> Decimal | None:
        if avg_balance is None or flow in (None, Decimal("0")):
            return None
        assert flow is not None
        return (avg_balance / flow * Decimal("365")).quantize(Decimal("0.0001"))

    dso = days(ar_avg, revenue_cur)
    dio = days(inv_avg, cogs_cur)
    dpo = days(ap_avg, cogs_cur)
    ccc = (
        dso + dio - dpo
        if dso is not None and dio is not None and dpo is not None
        else None
    )
    working_capital = (
        ar_cur + inv_cur - ap_cur
        if ar_cur is not None and inv_cur is not None and ap_cur is not None
        else None
    )

    kpis = [
        _kpi("应收账款", ar_cur, ar_begin, unit="百万元"),
        _kpi("存货", inv_cur, inv_begin, unit="百万元"),
        _kpi("应付账款（含其他应付款）", ap_cur, ap_begin, unit="百万元",
             caliber_note="申请稿混合口径行"),
        _kpi("营运资金占用", working_capital, None, unit="百万元"),
        _kpi("DSO", dso, None, unit="day", caliber_note="平均应收 / 收入 × 365"),
        _kpi("DIO", dio, None, unit="day", caliber_note="平均存货 / 营业成本 × 365"),
        _kpi("DPO", dpo, None, unit="day", caliber_note="平均应付 / 营业成本 × 365"),
        _kpi("CCC", ccc, None, unit="day", caliber_note="DSO + DIO − DPO（恒等式随图断言）"),
    ]
    charts: dict[str, Any] = {
        "ar_inv_ap_trend": {
            "title": "应收存货应付趋势",
            "type": "line",
            "periods": [ctx.period_label + " 期初", ctx.period_label + " 期末"],
            "series": {
                "应收": [ar_begin, ar_cur],
                "存货": [inv_begin, inv_cur],
                "应付": [ap_begin, ap_cur],
            },
        },
        "ccc_formula": {
            "title": "CCC 公式（DSO + DIO − DPO）",
            "type": "formula_card",
            "dso": str(dso) if dso is not None else None,
            "dio": str(dio) if dio is not None else None,
            "dpo": str(dpo) if dpo is not None else None,
            "ccc": str(ccc) if ccc is not None else None,
            "identity": "CCC = DSO + DIO − DPO",
        },
    }
    unavailable = [
        {
            "block": "应收账龄",
            "code": "ar_aging_not_disclosed",
            "reason": "申请稿无账龄明细；演示明细层（demo_detail）隔离展示，不在本模块冒充披露",
        },
        {
            "block": "主体/分部效率排名",
            "code": "multi_entity_not_applicable",
            "reason": "公开期单主体；分部披露止于 FY2025 且无周转口径",
        },
    ]
    return {
        "module": "working-capital",
        "title": "营运资金",
        "period": ctx.period_label,
        "prior_period": ctx.prior_period_label,
        "snapshot_id": ctx.snapshot_id,
        "report_ids": [str(ctx.current_report_id), str(ctx.prior_report_id)],
        "source_notice": (
            "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用；"
            "不构成公开财报 C 级能力证明"
        ),
        "unit": "百万元",
        "kpis": kpis,
        "charts": charts,
        "unavailable": unavailable,
    }
