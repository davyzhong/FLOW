"""Task 3：大麦合成财务报告生成契约测试（规格 §5.1 恒等清单）。

- FY2025（对比期）/ FY2026（分析期）两份完整报告；
- 收入与 canonical 年度汇总一致；资产 = 负债 + 权益；
- 现金桥闭合且 CF 期末现金 = BS 货币资金；
- 权益 roll-forward 期末权益 = BS 权益；净利润归属拆分合计 = 净利润；
- 金额单位统一人民币千元（canonical 万元 × 10）。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.fixtures.damai.generator import build_damai_package
from flow_api.fixtures.damai.statements import build_damai_statement_payloads

_UNIT = Decimal("10")  # canonical 万元 -> 报告千元


def _annual_revenue_thousands(package: dict, months: tuple[str, ...]) -> Decimal:
    return sum(
        (
            Decimal(str(row["revenue"])) * _UNIT
            for row in package["monthly_facts"]["operating_actual"]
            if row["month"] in months
        ),
        Decimal("0"),
    )


def test_two_annual_reports_generated() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    assert set(payloads) == {"FY2025", "FY2026"}
    for payload in payloads.values():
        assert set(payload["statements"]) >= {
            "合并利润表",
            "合并资产负债表",
            "合并现金流量表",
            "合并所有者权益变动表",
        }
        assert payload["unit"] == "人民币千元"


def test_metric_source_lines_are_explicit_and_reconcile() -> None:
    """覆盖指标所需的子项须进入合成报表，但不得改变已闭合总额。"""
    payloads = build_damai_statement_payloads(build_damai_package())
    for payload in payloads.values():
        statements = payload["statements"]
        income = {row["item"]: row for row in statements["合并利润表"]}
        balance = {row["item"]: row for row in statements["合并资产负债表"]}
        cashflow = {row["item"]: row for row in statements["合并现金流量表"]}

        finance_cost = Decimal(income["财务费用"]["本期发生额"])
        interest = Decimal(income["其中：利息费用"]["本期发生额"])
        assert Decimal("0") < interest < finance_cost

        current_liabilities = Decimal(balance["流动负债合计"]["期末余额"])
        assert sum(
            Decimal(balance[item]["期末余额"])
            for item in ("短期借款", "应付账款", "其他流动负债")
        ) == current_liabilities
        noncurrent_liabilities = Decimal(balance["非流动负债合计"]["期末余额"])
        assert sum(
            Decimal(balance[item]["期末余额"])
            for item in ("长期借款", "其他非流动负债")
        ) == noncurrent_liabilities

        assert Decimal(cashflow["销售商品、提供劳务收到的现金"]["本期发生额"]) == Decimal(
            cashflow["经营活动现金流入小计"]["本期发生额"]
        )
        assert Decimal(cashflow["折旧与摊销"]["本期发生额"]) > 0
        capex = Decimal(
            cashflow["购建固定资产、无形资产和其他长期资产支付的现金"]["本期发生额"]
        )
        assert capex == Decimal(cashflow["投资活动现金流出小计"]["本期发生额"])
        assert Decimal(cashflow["投资活动产生的现金流量净额"]["本期发生额"]) == -capex


def test_revenue_matches_canonical_annual_total() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    all_months = tuple(
        sorted({r["month"] for r in package["monthly_facts"]["operating_actual"]})
    )
    canonical = {
        "FY2025": _annual_revenue_thousands(package, all_months[:12]),
        "FY2026": _annual_revenue_thousands(package, all_months[12:]),
    }
    for fy, payload in payloads.items():
        income = {row["item"]: row for row in payload["statements"]["合并利润表"]}
        reported = Decimal(income["营业收入"]["本期发生额"])
        assert reported == canonical[fy], f"{fy} 收入必须与 canonical 年度汇总一致"


def test_gross_profit_and_net_income_attribution() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    for payload in payloads.values():
        income = {row["item"]: row for row in payload["statements"]["合并利润表"]}
        revenue = Decimal(income["营业收入"]["本期发生额"])
        cost = Decimal(income["营业成本"]["本期发生额"])
        gross = Decimal(income["毛利"]["本期发生额"])
        assert revenue - cost == gross
        net = Decimal(income["五、净利润（净亏损以“－”号填列）"]["本期发生额"])
        attr = Decimal(income["1.归属于母公司所有者的净利润"]["本期发生额"])
        minority = Decimal(income["2.少数股东损益"]["本期发生额"])
        assert attr + minority == net, "净利润归属拆分必须闭合"


def test_balance_sheet_identity_holds() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    for payload in payloads.values():
        bs = {row["item"]: row for row in payload["statements"]["合并资产负债表"]}
        assets = Decimal(bs["资产总计"]["期末余额"])
        liabilities = Decimal(bs["负债合计"]["期末余额"])
        equity = Decimal(bs["所有者权益合计"]["期末余额"])
        assert assets == liabilities + equity, "资产 = 负债 + 权益"


def test_cash_bridge_closes_and_matches_balance_sheet() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    for payload in payloads.values():
        cf = {row["item"]: row for row in payload["statements"]["合并现金流量表"]}
        opening = Decimal(cf["加：期初现金及现金等价物余额"]["本期发生额"])
        operating = Decimal(cf["经营活动产生的现金流量净额"]["本期发生额"])
        investing = Decimal(cf["投资活动产生的现金流量净额"]["本期发生额"])
        financing = Decimal(cf["筹资活动产生的现金流量净额"]["本期发生额"])
        closing = Decimal(cf["六、期末现金及现金等价物余额"]["本期发生额"])
        assert opening + operating + investing + financing == closing, "现金桥必须闭合"
        bs = {row["item"]: row for row in payload["statements"]["合并资产负债表"]}
        assert closing == Decimal(bs["货币资金"]["期末余额"]), (
            "现金流量表期末现金必须等于资产负债表货币资金"
        )


def test_equity_roll_forward_matches_balance_sheet() -> None:
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    for payload in payloads.values():
        eq = {row["item"]: row for row in payload["statements"]["合并所有者权益变动表"]}
        opening = Decimal(eq["期初权益"]["本期发生额"])
        net_income = Decimal(eq["本期净利润"]["本期发生额"])
        other = Decimal(eq["其他权益变动"]["本期发生额"])
        closing = Decimal(eq["期末权益"]["本期发生额"])
        assert opening + net_income + other == closing, "权益 roll-forward 必须闭合"
        bs = {row["item"]: row for row in payload["statements"]["合并资产负债表"]}
        assert closing == Decimal(bs["所有者权益合计"]["期末余额"]), (
            "权益变动表期末权益必须等于资产负债表权益"
        )


# ---------------------------------------------------------------------------
# Task A1 红灯：财报独立身份（规格 §4.3 / 计划 Task A3 前置合同）
# ---------------------------------------------------------------------------


def test_statement_payloads_carry_damai_syn_identity() -> None:
    """财报 payload 必须携带独立 synthetic 身份 DAMAI.SYN，
    不得复用或冒充 9988.HK（阿里巴巴）fixture 身份。"""
    package = build_damai_package()
    payloads = build_damai_statement_payloads(package)
    for fy, payload in payloads.items():
        assert payload.get("stock_code") == "DAMAI.SYN", (
            f"{fy} 必须携带 DAMAI.SYN 独立身份"
        )
        assert payload.get("company") == "大麦物流", f"{fy} 公司名必须为大麦物流"
