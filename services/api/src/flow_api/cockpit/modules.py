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

from dataclasses import dataclass, field
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
    raw_current: dict[tuple[str, str, str], Decimal] = field(
        default_factory=dict
    )


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

    def collect(
        report: StatementReport,
    ) -> tuple[dict[str, Decimal], dict[tuple[str, str, str], Decimal]]:
        rows = session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report.id,
                StatementNormalizedItem.item_id.isnot(None),
            )
        ).all()
        facts: dict[str, Decimal] = {}
        raw: dict[tuple[str, str, str], Decimal] = {}
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
        return facts, raw

    return ModuleFactContext(
        current_report_id=current.id,
        prior_report_id=prior.id,
        period_label=current.period_label,
        prior_period_label=prior.period_label,
        snapshot_id=str(snapshot.id) if snapshot else "",
        current=collect(current)[0],
        prior=collect(prior)[0],
        raw_current=collect(current)[1],
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
            "unit": "百万元",
            "periods": [ctx.prior_period_label, ctx.period_label],
            "series": {
                "流动资产": [prior_current_assets, current_assets],
                "非流动资产": [prior_noncurrent_assets, noncurrent_assets],
            },
        },
        "liability_equity_structure": {
            "title": "负债与权益结构",
            "type": "ratio_bar",
            "unit": "百万元",
            "periods": [ctx.prior_period_label, ctx.period_label],
            "series": {
                "负债合计": [prior_total_liab, total_liab],
                "所有者权益": [prior_equity, equity],
            },
        },
        "capital_structure_trend": {
            "title": "资本结构趋势",
            "type": "line",
            "unit": "ratio",
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
            "unit": "百万元",
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
            "unit": "day",
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


def build_risk_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """§5.8 财务风险：偿债比率 + Findings 预警清单；利息/净杠杆缺省。"""

    current_assets = _fact(ctx, "bs.current_assets")
    inventory = _fact(ctx, "bs.inventory")
    cash = _fact(ctx, "bs.cash")
    current_liab = _fact(ctx, "bs.current_liab")
    total_liab = _fact(ctx, "bs.total_liab")
    equity = _fact(ctx, "bs.equity")
    total_assets = _fact(ctx, "bs.total_assets")
    ocf = ctx.current.get("cf.ocf:cur")

    def ratio(n: Decimal | None, d: Decimal | None) -> Decimal | None:
        if n is None or d in (None, Decimal("0")):
            return None
        assert d is not None
        return (n / d).quantize(Decimal("0.0001"))

    quick = ratio(
        (
            current_assets - inventory
            if current_assets is not None and inventory is not None
            else None
        ),
        current_liab,
    )
    prior_current_assets = _prior_fact(ctx, "bs.current_assets")
    prior_inventory = _prior_fact(ctx, "bs.inventory")
    prior_cash = _prior_fact(ctx, "bs.cash")
    prior_current_liab = _prior_fact(ctx, "bs.current_liab")
    prior_total_liab = _prior_fact(ctx, "bs.total_liab")
    prior_total_assets = _prior_fact(ctx, "bs.total_assets")
    prior_equity = _prior_fact(ctx, "bs.equity")
    prior_ocf = ctx.prior.get("cf.ocf:cur")
    prior_quick = ratio(
        prior_current_assets - prior_inventory
        if prior_current_assets is not None and prior_inventory is not None
        else None,
        prior_current_liab,
    )
    current_ratio = ratio(current_assets, current_liab)
    cash_ratio = ratio(cash, current_liab)
    debt_asset_ratio = ratio(total_liab, total_assets)
    equity_multiplier = ratio(total_assets, equity)
    ocf_current_liab_ratio = ratio(ocf, current_liab)
    kpis = [
        _kpi("流动比率", current_ratio, ratio(prior_current_assets, _prior_fact(ctx, "bs.current_liab")), unit="ratio",
             caliber_note="经验参考约 2；过高可能资金闲置"),
        _kpi("速动比率", quick, prior_quick, unit="ratio"),
        _kpi("现金比率", cash_ratio, ratio(prior_cash, prior_current_liab), unit="ratio"),
        _kpi("资产负债率", debt_asset_ratio, ratio(prior_total_liab, prior_total_assets), unit="ratio"),
        _kpi("权益乘数", equity_multiplier, ratio(prior_total_assets, prior_equity), unit="ratio"),
        _kpi("OCF/流动负债", ocf_current_liab_ratio, ratio(prior_ocf, prior_current_liab), unit="ratio"),
        _kpi("利息保障倍数", None, None, unit="ratio",
             unavailable_code="is.interest_exp",
             caliber_note="申请稿利润表无独立利息费用行（U-DM-INTEREST-SPLIT）"),
        _kpi("净负债/EBITDA", None, None, unit="ratio",
             unavailable_code="bs.short_debt + is.interest_exp",
             caliber_note="需短债拆分与 EBITDA（均未披露）"),
    ]
    unavailable = [
        {"block": "预警阈值配置", "code": "threshold_config_c06",
         "reason": "管控线阈值属 C06 配置层，公开期使用经验参考值标注"},
        {"block": "利息保障 / 净杠杆", "code": "interest_exp_not_disclosed",
         "reason": "申请稿无独立利息费用行、无短债拆分"},
    ]
    return {
        "module": "risk",
        "title": "财务风险",
        "period": ctx.period_label,
        "prior_period": ctx.prior_period_label,
        "snapshot_id": ctx.snapshot_id,
        "report_ids": [str(ctx.current_report_id), str(ctx.prior_report_id)],
        "source_notice": (
            "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用；"
            "不构成公开财报 C 级能力证明"
        ),
        "unit": "ratio", "kpis": kpis,
        "charts": {
            "liquidity_ratios": {
                "title": "短期偿债能力对比", "type": "line", "unit": "倍",
                "periods": [ctx.prior_period_label, ctx.period_label],
                "series": {
                    "流动比率": [ratio(prior_current_assets, prior_current_liab), current_ratio],
                    "速动比率": [prior_quick, quick],
                    "现金比率": [ratio(prior_cash, prior_current_liab), cash_ratio],
                },
            },
            "solvency_ratios": {
                "title": "资本结构对比", "type": "line", "unit": "ratio",
                "periods": [ctx.prior_period_label, ctx.period_label],
                "series": {"资产负债率": [ratio(prior_total_liab, prior_total_assets), debt_asset_ratio]},
            },
            "leverage_ratios": {
                "title": "权益乘数对比", "type": "line", "unit": "倍",
                "periods": [ctx.prior_period_label, ctx.period_label],
                "series": {"权益乘数": [ratio(prior_total_assets, prior_equity), equity_multiplier]},
            },
        }, "unavailable": unavailable,
    }


def build_consolidation_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """§5.9 集团合并（公开期降级态）：「主体对比」视角——菜鸟分部序列。"""

    segment_facts: dict[str, int] = {
        "FY2019": 14885, "FY2020": 22233, "FY2021": 37258,
        "FY2022": 46107, "FY2023": 77512, "FY2024": 99020, "FY2025": 101272,
    }
    charts: dict[str, Any] = {
        "cainiao_segment_series": {
            "title": "菜鸟分部收入（阿里年报披露）",
            "type": "line",
            "unit": "百万元",
            "periods": list(segment_facts.keys()),
            "series": {"分部收入": list(segment_facts.values())},
            "note": "FY2026 起菜鸟并入「所有其他」分部，无单独披露",
        },
    }
    return {
        "module": "consolidation",
        "title": "集团合并（降级态）",
        "period": ctx.period_label,
        "prior_period": ctx.prior_period_label,
        "snapshot_id": ctx.snapshot_id,
        "report_ids": [],
        "source_notice": (
            "降级态：公开期单主体，无合并抵销数据。"
            "菜鸟分部序列为阿里年报披露事实（CN-SEG-*）。"
        ),
        "unit": "百万元",
        "kpis": [{"name": "合并抵销", "status": "unavailable",
                   "unavailable_code": "internal_period_feature",
                   "unit": "", "caliber_note": "合并抵销桥属内部期功能"}],
        "charts": charts,
        "unavailable": [{"block": "合并抵销桥", "code": "internal_period_feature",
                          "reason": "公开期单主体（D052）；多法人合并属内部期"}],
    }


def build_expenses_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """费用分析。"""
    def _exp(name: str, item_id: str) -> dict[str, Any]:
        cur = ctx.current.get(f"{item_id}:cur")
        prior = ctx.current.get(f"{item_id}:prior_yoy")
        rev = ctx.current.get("is.revenue:cur")
        rate = _ratio(abs(cur) if cur is not None else None, rev)
        return {"name": name, "status": "available" if cur is not None else "unavailable",
                "value": str(abs(cur)) if cur is not None else None,
                "prior_value": str(abs(prior)) if prior is not None else None,
                "rate": str(rate) if rate is not None else None, "unit": "百万元"}
    selling = ctx.current.get("is.selling_exp:cur")
    admin = ctx.current.get("is.admin_exp:cur")
    rnd = ctx.current.get("is.rnd_exp:cur")
    fin = ctx.current.get("is.fin_exp:cur")
    total = sum((abs(x) for x in (selling, admin, rnd, fin) if x is not None), Decimal("0")) \
        if all(x is not None for x in (selling, admin, rnd, fin)) else None
    rev = ctx.current.get("is.revenue:cur")
    pr = _ratio(total, rev)
    return {"module": "expenses", "title": "费用分析", "period": ctx.period_label,
        "prior_period": ctx.prior_period_label, "snapshot_id": ctx.snapshot_id,
        "report_ids": [str(ctx.current_report_id), str(ctx.prior_report_id)],
        "source_notice": "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用",
        "unit": "百万元",
        "kpis": [_exp("销售及市场推广开支", "is.selling_exp"),
            _exp("一般及行政开支", "is.admin_exp"), _exp("产品开发开支", "is.rnd_exp"),
            _exp("财务成本", "is.fin_exp"),
            {"name": "期间费用合计", "status": "available" if total is not None else "unavailable",
             "value": str(total) if total is not None else None,
             "rate": str(pr) if pr is not None else None, "unit": "百万元"}],
        "charts": {"expense_structure": {"title": "费用结构", "type": "ratio_bar", "unit": "百万元",
            "series": {"销售": abs(selling) if selling is not None else None,
                "管理": abs(admin) if admin is not None else None,
                "研发": abs(rnd) if rnd is not None else None,
                "财务": abs(fin) if fin is not None else None}}},
        "unavailable": [{"block": "预算执行", "code": "budget_not_applicable_public_period",
            "reason": "预算基准属内部期（D054）"}]}


def build_cashflow_module(ctx: ModuleFactContext) -> dict[str, Any]:
    """现金流。"""
    def raw(item: str) -> Decimal | None:
        return ctx.raw_current.get(("合并现金流量表", item, "cur"))
    ocf = ctx.current.get("cf.ocf:cur")
    np = ctx.current.get("is.net_profit:cur")
    return {"module": "cashflow", "title": "现金流", "period": ctx.period_label,
        "prior_period": ctx.prior_period_label, "snapshot_id": ctx.snapshot_id,
        "report_ids": [str(ctx.current_report_id), str(ctx.prior_report_id)],
        "source_notice": "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用",
        "unit": "百万元",
        "kpis": [_kpi("经营活动现金流量净额", ocf,
                 ctx.current.get("cf.ocf:prior_yoy"), unit="百万元"),
            _kpi("投资活动现金流量净额", ctx.current.get("cf.icf:cur"),
                 ctx.current.get("cf.icf:prior_yoy"), unit="百万元"),
            _kpi("筹资活动现金流量净额", ctx.current.get("cf.fin_cf:cur"),
                 ctx.current.get("cf.fin_cf:prior_yoy"), unit="百万元"),
            _kpi("净现比", _ratio(ocf, np), None, unit="ratio", caliber_note="OCF/净利润")],
        "charts": {"cash_bridge": {"title": "现金变动桥", "type": "waterfall", "unit": "百万元",
            "steps": {"年初": raw("年初现金及现金等价物"), "经营": raw("经营活动所得现金净额"),
                "投资": raw("投资活动所用现金净额"), "筹资": raw("融资活动(所用)所得现金净额"),
                "汇率": raw("汇率变动对现金的影响"), "年末": raw("年末现金及现金等价物")},
            "identity": "年末 = 年初 + 净变动 + 汇率"}},
        "unavailable": [{"block": "收现比", "code": "cash_from_sales_not_disclosed",
            "reason": "无「销售收现」行"},
            {"block": "13周预测", "code": "internal_period_feature", "reason": "内部期"}]}


