"""大麦合成财务报告生成（Task 3 / Task A3 报表范式升级）：从 canonical 年度事实推导闭合四表。

数据边界：利润表收入/成本与经营现金流净额来自 canonical 月度事实（零调整
投影）；费用、投资为确定性合成参数（synthetic，显式常量）。闭合为硬约束：
资产 = 负债 + 权益；现金桥闭合；权益 roll-forward 闭合且与 BS 权益一致。
金额单位统一人民币千元（canonical 万元 × 10）。

A3 起报表范式对齐 A 股合并报表披露：报表类型用「合并*」标准名、列用披露原文
标签（期末余额/期初余额/本期发生额/上期发生额），行项目采用 CAS 规范名，
使 ReviewService.publish 的勾稽门禁（资产=负债+权益、净利润归属、现金桥）
真实生效；FY2026 报告携带 FY2025 比较期列（期初/上期），链式一致。
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
_CF_OUTFLOW_RATE = Decimal("0.80")  # 经营现金流出小计（占收入，流入=流出+净额）
_CURRENT_LIAB_SHARE = Decimal("0.70")  # 流动负债占负债合计比

# 报表类型标准名（与 A 股勾稽门禁的覆盖判定一致）
ST_IS = "合并利润表"
ST_BS = "合并资产负债表"
ST_CF = "合并现金流量表"
ST_EQ = "合并所有者权益变动表"


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


def _income_statement(f: dict[str, Decimal]) -> list[dict[str, Any]]:
    """CAS 合并利润表：利润总额 = 营业利润（无营业外），净利润归属拆分闭合。"""

    revenue = f["revenue"]
    cost = f["cost"]
    gross = revenue - cost
    selling = _d(revenue * _EXPENSE_RATES["销售费用"])
    admin = _d(revenue * _EXPENSE_RATES["管理费用"])
    rnd = _d(revenue * _EXPENSE_RATES["研发费用"])
    fin_exp = _d(revenue * _FIN_EXP_RATE)
    operating = gross - selling - admin - rnd - fin_exp
    pretax = operating  # 无营业外收支：利润总额 = 营业利润
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
        ("财务费用", fin_exp),
        ("三、营业利润（亏损以“－”号填列）", operating),
        ("四、利润总额（亏损总额以“－”号填列）", pretax),
        ("减：所得税费用", tax),
        ("五、净利润（净亏损以“－”号填列）", net),
        ("1.归属于母公司所有者的净利润", attr),
        ("2.少数股东损益", net - attr),
    ]
    return [
        {"item": item, "本期发生额": str(value), "上期发生额": None}
        for item, value in rows
    ]


def _cash_flow_statement(
    f: dict[str, Decimal], opening_cash: Decimal
) -> tuple[list[dict[str, Any]], Decimal]:
    """现金桥硬闭合：净增加 = 经营+投资+筹资；期末 = 期初 + 净增加。"""

    ocf = f["ocf"]
    outflow = _d(f["revenue"] * _CF_OUTFLOW_RATE)
    inflow = outflow + ocf
    investing = _d(-(f["revenue"] * _INVEST_RATE))
    financing = Decimal("0")  # 扩张由经营积累覆盖
    net_increase = ocf + investing + financing
    closing = opening_cash + net_increase
    amounts: list[tuple[str, Decimal]] = [
        ("经营活动现金流入小计", _d(inflow)),
        ("经营活动现金流出小计", _d(outflow)),
        ("经营活动产生的现金流量净额", _d(ocf)),
        ("投资活动产生的现金流量净额", _d(investing)),
        ("筹资活动产生的现金流量净额", _d(financing)),
        ("五、现金及现金等价物净增加额", _d(net_increase)),
        ("加：期初现金及现金等价物余额", _d(opening_cash)),
        ("六、期末现金及现金等价物余额", _d(closing)),
    ]
    rows = [
        {"item": item, "本期发生额": str(value), "上期发生额": None}
        for item, value in amounts
    ]
    return rows, _d(closing)


def _equity_statement(
    opening_equity: Decimal, net_income: Decimal, closing_equity: Decimal
) -> list[dict[str, Any]]:
    other = closing_equity - opening_equity - net_income
    return [
        {"item": "期初权益", "本期发生额": str(_d(opening_equity)), "上期发生额": None},
        {"item": "本期净利润", "本期发生额": str(_d(net_income)), "上期发生额": None},
        {"item": "其他权益变动", "本期发生额": str(_d(other)), "上期发生额": None},
        {"item": "期末权益", "本期发生额": str(_d(closing_equity)), "上期发生额": None},
    ]


def _balance_sheet_rows(
    cash: Decimal, revenue: Decimal, equity_total: Decimal
) -> dict[str, tuple[Decimal, Decimal]]:
    """构造闭合资产负债表（item → (期末, 占位)），恒等式逐条精确成立。

    流动资产合计 = 货币资金+应收账款+存货+其他流动资产；非流动资产合计 = 固定资产；
    资产总计 = 流动+非流动；负债合计 = 资产 − 权益（配平）并拆流动/非流动；
    所有者权益合计 = 归母 + 少数股东；负债和所有者权益总计 = 资产总计。
    """

    ar = _d(revenue * _AR_RATE)
    inventory = _d(revenue * _INVENTORY_RATE)
    ca_other = _d(revenue * _CA_OTHER_RATE)
    fixed = _d(revenue * _FIXED_ASSET_RATE)
    current_assets = cash + ar + inventory + ca_other
    noncurrent_assets = fixed
    total_assets = current_assets + noncurrent_assets
    liabilities = total_assets - equity_total
    current_liab = _d(liabilities * _CURRENT_LIAB_SHARE)
    noncurrent_liab = liabilities - current_liab
    attr_equity = _d(equity_total * _ATTR_SHARE)
    minority_equity = equity_total - attr_equity
    rows: list[tuple[str, Decimal]] = [
        ("货币资金", cash),
        ("应收账款", ar),
        ("存货", inventory),
        ("其他流动资产", ca_other),
        ("流动资产合计", current_assets),
        ("固定资产", fixed),
        ("非流动资产合计", noncurrent_assets),
        ("资产总计", total_assets),
        ("流动负债合计", current_liab),
        ("非流动负债合计", noncurrent_liab),
        ("负债合计", liabilities),
        ("归属于母公司所有者权益合计", attr_equity),
        ("少数股东权益", minority_equity),
        ("所有者权益合计", equity_total),
        ("负债和所有者权益总计", total_assets),
    ]
    return {item: (value, value) for item, value in rows}


def _balance_sheet(
    cash: Decimal,
    revenue: Decimal,
    equity_closing: Decimal,
    *,
    opening: dict[str, Decimal] | None,
) -> tuple[list[dict[str, Any]], dict[str, Decimal]]:
    """期末 BS 闭合；期初列取上年期末（链式一致），首份报告期初由参数构造。"""

    rows = _balance_sheet_rows(cash, revenue, equity_closing)
    end_values = {item: end for item, (end, _begin) in rows.items()}
    if opening is None:
        # 首份报告（FY2025）：以期初现金/期初权益参数构造闭合期初 BS
        opening_cash = _d(revenue * _CASH_RATE)
        opening_equity = _d(revenue * _OPENING_EQUITY_RATE)
        opening_rows = _balance_sheet_rows(opening_cash, revenue, opening_equity)
        opening = {item: end for item, (end, _b) in opening_rows.items()}
    result = [
        {
            "item": item,
            "期末余额": str(_d(end_values[item])),
            "期初余额": str(_d(opening[item])),
        }
        for item in end_values
    ]
    return result, end_values


def build_damai_statement_payloads(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """从 canonical 事实生成 FY2025（对比期）与 FY2026（分析期）闭合报告。

    FY2026 报告携带 FY2025 比较期列（上期发生额/期初余额 = FY2025 期末值），
    保证同比列同样满足全部勾稽恒等式。
    """

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
    opening_equity: Decimal | None = None
    prior_rows: dict[str, dict[str, Any]] = {}
    for fy, months in months_by_fy.items():
        f = _annual_facts(package, months)
        income_rows = _income_statement(f)
        net_income = Decimal(
            next(
                r
                for r in income_rows
                if r["item"] == "五、净利润（净亏损以“－”号填列）"
            )["本期发生额"]
        )
        if opening_equity is None:
            opening_equity = _d(f["revenue"] * _OPENING_EQUITY_RATE)
        cf_rows, closing_cash = _cash_flow_statement(f, opening_cash)
        # 权益 roll-forward：期末权益 = 期末现金（synthetic 简化：扩张由经营积累覆盖）
        closing_equity = closing_cash
        equity_rows = _equity_statement(opening_equity, net_income, closing_equity)
        bs_rows, bs_end = _balance_sheet(
            closing_cash,
            f["revenue"],
            closing_equity,
            opening=None,  # 期初列：FY2025 参数构造；FY2026 由上年期末统一注入
        )

        # 比较期列注入：FY2026 的 上期发生额/期初余额 = FY2025 本期/期末
        if prior_rows:
            for row in income_rows + cf_rows + equity_rows:
                prior = prior_rows["flow"].get(row["item"])
                if prior is not None:
                    row["上期发生额"] = prior
            for row in bs_rows:
                prior = prior_rows["BS"].get(row["item"])
                if prior is not None:
                    row["期初余额"] = prior

        payloads[fy] = {
            "entity": package["enterprise"],
            "stock_code": "DAMAI.SYN",
            "company": "大麦物流",
            "unit": "人民币千元",
            "period": months,
            "statements": {
                ST_IS: income_rows,
                ST_CF: cf_rows,
                ST_EQ: equity_rows,
                ST_BS: bs_rows,
            },
            "notes_index": [
                "附注 1：编制基础（synthetic 演示，CAS 合并报表简化投影）",
                "附注 2：收入按业务族分解见 canonical family_actual",
                "附注 3：应收账款账龄见 canonical ar_aging",
            ],
        }
        prior_rows = {
            "flow": {row["item"]: row["本期发生额"] for row in income_rows + cf_rows + equity_rows},
            "BS": {item: str(_d(value)) for item, value in bs_end.items()},
        }
        opening_cash = closing_cash
        opening_equity = closing_equity
    return payloads


__all__ = ["build_damai_statement_payloads"]
