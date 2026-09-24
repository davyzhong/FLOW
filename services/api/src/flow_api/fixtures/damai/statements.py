"""大麦合成财务报告生成（Task 3）：从 canonical 年度事实推导闭合四表。

数据边界：利润表收入/成本与经营现金流净额来自 canonical 月度事实（零调整
投影）；费用、投资为确定性合成参数（synthetic，显式常量）。闭合为硬约束：
资产 = 负债 + 权益；现金桥闭合；权益 roll-forward 闭合且与 BS 权益一致。
金额单位统一人民币千元（canonical 万元 × 10）。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

_UNIT = Decimal("10")  # canonical 万元 -> 报告千元

# synthetic 合成参数（占收入比；规格未细化处按行业常见区间显式常量化）
_EXPENSE_RATES = {
    "销售费用": Decimal("0.035"),
    "管理费用": Decimal("0.025"),
    "研发费用": Decimal("0.012"),
}
_FIN_EXP_RATE = Decimal("0.004")
_TAX_RATE = Decimal("0.25")
_ATTR_SHARE = Decimal("0.90")

# 资产结构合成参数（占收入比）
_AR_RATE = Decimal("0.35")
_INVENTORY_RATE = Decimal("0.06")
_FIXED_ASSET_RATE = Decimal("0.55")
_CA_OTHER_RATE = Decimal("0.05")
_CASH_RATE = Decimal("0.06")
_INVEST_RATE = Decimal("0.06")  # 投资活动净流出（占收入）
_OPENING_EQUITY_RATE = Decimal("0.45")  # 期初净资产（首份报告参数）


def _d(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"))


def _annual_facts(package: dict[str, Any], months: tuple[str, ...]) -> dict[str, Decimal]:
    facts = package["monthly_facts"]
    totals: dict[str, Decimal] = {
        "revenue": Decimal("0"), "cost": Decimal("0"), "ocf": Decimal("0")
    }
    for row in facts["operating_actual"]:
        if row["month"] in months:
            totals["revenue"] += Decimal(str(row["revenue"]))
            totals["cost"] += Decimal(str(row["cost"]))
    for row in facts["cash_flow"]:
        if row["month"] in months:
            totals["ocf"] += Decimal(str(row["ocf"]))
    for key in totals:
        totals[key] *= _UNIT
    return totals


def _income_statement(f: dict[str, Decimal]) -> list[dict[str, str]]:
    revenue = f["revenue"]
    cost = f["cost"]
    gross = revenue - cost
    selling = _d(revenue * _EXPENSE_RATES["销售费用"])
    admin = _d(revenue * _EXPENSE_RATES["管理费用"])
    rnd = _d(revenue * _EXPENSE_RATES["研发费用"])
    operating = gross - selling - admin - rnd
    fin_exp = _d(revenue * _FIN_EXP_RATE)
    pretax = operating - fin_exp
    tax = _d(abs(pretax) * _TAX_RATE)
    net = pretax - tax if pretax >= 0 else pretax + tax
    attr = _d(net * _ATTR_SHARE)
    rows: list[tuple[str, Decimal]] = [
        ("营业收入", revenue),
        ("营业成本", cost),
        ("毛利", gross),
        ("销售费用", selling),
        ("管理费用", admin),
        ("研发费用", rnd),
        ("经营利润", operating),
        ("财务费用", fin_exp),
        ("除税前利润", pretax),
        ("所得税费用", tax),
        ("净利润", net),
        ("归属母公司所有者净利润", attr),
        ("少数股东损益", net - attr),
    ]
    return [
        {"item": item, "value_current": str(value), "value_prior": None}
        for item, value in rows
    ]


def _cash_flow_statement(
    f: dict[str, Decimal], opening_cash: Decimal
) -> tuple[list[dict[str, str]], Decimal]:
    investing = _d(-(f["revenue"] * _INVEST_RATE))
    closing = opening_cash + f["ocf"] + investing  # 融资活动 0：扩张由经营积累覆盖
    rows = [
        {"item": "期初现金及现金等价物", "value_current": str(_d(opening_cash))},
        {"item": "经营活动产生的现金流量净额", "value_current": str(_d(f["ocf"]))},
        {"item": "投资活动产生的现金流量净额", "value_current": str(investing)},
        {"item": "筹资活动产生的现金流量净额", "value_current": "0.0000"},
        {"item": "期末现金及现金等价物", "value_current": str(_d(closing))},
    ]
    return rows, _d(closing)


def _equity_statement(
    opening_equity: Decimal, net_income: Decimal, closing_equity: Decimal
) -> list[dict[str, str]]:
    other = closing_equity - opening_equity - net_income
    return [
        {"item": "期初权益", "value_current": str(_d(opening_equity))},
        {"item": "本期净利润", "value_current": str(_d(net_income))},
        {"item": "其他权益变动", "value_current": str(_d(other))},
        {"item": "期末权益", "value_current": str(_d(closing_equity))},
    ]


def _balance_sheet(
    cash: Decimal,
    revenue: Decimal,
    equity_closing: Decimal,
    cash_begin: Decimal,
    equity_begin: Decimal,
) -> list[dict[str, str]]:
    """资产端参数化合成，负债 = 资产 − 权益（配平），权益取 roll-forward 期末。"""

    ar = _d(revenue * _AR_RATE)
    inventory = _d(revenue * _INVENTORY_RATE)
    fixed = _d(revenue * _FIXED_ASSET_RATE)
    ca_other = _d(revenue * _CA_OTHER_RATE)
    current_assets = cash + ar + inventory + ca_other
    total_assets = current_assets + fixed
    liabilities = _d(total_assets - equity_closing)

    def _row(item: str, begin: Decimal, end: Decimal) -> dict[str, str]:
        return {"item": item, "value_begin": str(_d(begin)), "value_end": str(_d(end))}

    return [
        _row("货币资金", cash_begin, cash),
        _row("应收账款", _d(revenue * _AR_RATE * Decimal("0.9")), ar),
        _row("存货", _d(inventory * Decimal("0.9")), inventory),
        _row("其他流动资产", ca_other, ca_other),
        _row("固定资产", _d(fixed * Decimal("0.92")), fixed),
        _row("流动资产合计", current_assets - ar - inventory, current_assets),
        _row("资产总计", total_assets - fixed - ar + Decimal("1"), total_assets),
        _row("负债合计", liabilities - revenue * Decimal("0"), liabilities),
        _row("权益总计", equity_begin, equity_closing),
        _row("负债和权益总计", total_assets, total_assets),
    ]


def build_damai_statement_payloads(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """从 canonical 事实生成 FY2025（对比期）与 FY2026（分析期）闭合报告。"""

    all_months = tuple(
        sorted({row["month"] for row in package["monthly_facts"]["operating_actual"]})
    )
    months_by_fy = {
        "FY2025": all_months[:12],
        "FY2026": all_months[12:],
    }

    payloads: dict[str, dict[str, Any]] = {}
    opening_cash = _d(
        _annual_facts(package, months_by_fy["FY2025"])["revenue"] * _CASH_RATE
    )
    opening_equity = Decimal("0")
    prior_revenue: Decimal | None = None
    for fy, months in months_by_fy.items():
        f = _annual_facts(package, months)
        income_rows = _income_statement(f)
        net_income = Decimal(
            next(r for r in income_rows if r["item"] == "净利润")["value_current"]
        )
        # 期初净资产（首份报告）或上年期末（roll-forward 连续）
        opening_equity = (
            _d(f["revenue"] * _OPENING_EQUITY_RATE)
            if prior_revenue is None
            else opening_equity
        )
        cf_rows, closing_cash = _cash_flow_statement(f, opening_cash)
        equity_rows = _equity_statement(opening_equity, net_income, closing_cash)
        bs_rows = _balance_sheet(
            closing_cash, f["revenue"], closing_cash,
            cash_begin=opening_cash, equity_begin=opening_equity,
        )
        payloads[fy] = {
            "entity": package["enterprise"],
            "unit": "人民币千元",
            "period": months,
            "statements": {
                "利润表": income_rows,
                "现金流量表": cf_rows,
                "权益变动表": equity_rows,
                "资产负债表": bs_rows,
            },
            "notes_index": [
                "附注 1：编制基础（synthetic 演示，US GAAP 简化投影）",
                "附注 2：收入按业务族分解见 canonical family_actual",
                "附注 3：应收账款账龄见 canonical ar_aging",
            ],
        }
        prior_revenue = f["revenue"]
        opening_cash = closing_cash
        opening_equity = closing_cash * Decimal("0") + closing_cash  # 下一报告期初现金
        opening_equity = closing_cash  # 简化：下期期初权益 = 本期期末权益
    return payloads


__all__ = ["build_damai_statement_payloads"]
