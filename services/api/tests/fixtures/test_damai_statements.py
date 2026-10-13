"""大麦披露财报契约测试（2026-10-13 时间线迁移后）。

- FY2022（比较期）/ FY2023（分析期）两份披露报告（菜鸟申请稿 IFRS 逐行原值）；
- 关键行值与来源登记披露锚一致（防抽取/重排漂移）；
- 上期列与上年文件本期列跨文件一致；
- IFRS 恒等式：毛利、经营亏损、年度亏损归属、资产=权益及负债、现金桥；
- 合成专用行（利息 65% 拆分、折旧 10% 估算、权益变动表）必须已移除；
- 身份：DAMAI.SYN / 大麦物流，provenance 如实披露菜鸟申请稿来源。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from flow_api.fixtures.damai.statements import build_damai_statement_payloads

# 申请稿披露锚（与来源登记一致；人民币千元）
_ANCHORS = {
    "FY2023": {"revenue": Decimal("77799675"), "assets": Decimal("71850931")},
    "FY2022": {"revenue": Decimal("66866916"), "assets": Decimal("58881087")},
}


@pytest.fixture(scope="module")
def payloads() -> dict:
    return build_damai_statement_payloads()


def _col(rows: list[dict], col: str) -> dict[str, Decimal]:
    """行列表 → {行名: 该列 Decimal}（缺省值 None 记 0，与勾稽口径一致）。"""

    return {
        row["item"]: (Decimal(str(row[col])) if row.get(col) is not None else Decimal("0"))
        for row in rows
    }




def test_two_annual_reports_generated(payloads: dict) -> None:
    assert set(payloads) == {"FY2022", "FY2023"}
    for payload in payloads.values():
        assert set(payload["statements"]) == {
            "合并利润表",
            "合并资产负债表",
            "合并现金流量表",
        }, "只含披露三表；合成权益变动表已移除"
        assert payload["unit"] == "人民币千元"
        assert payload["data_layer"] == "disclosed_fact"
        assert "provenance" in payload and "registry" in payload["provenance"]


def test_disclosed_anchor_values(payloads: dict) -> None:
    for fy, payload in payloads.items():
        income = {row["item"]: row for row in payload["statements"]["合并利润表"]}
        assert Decimal(income["收入"]["本期发生额"]) == _ANCHORS[fy]["revenue"]
        bs = {row["item"]: row for row in payload["statements"]["合并资产负债表"]}
        assert Decimal(bs["资产总计"]["期末余额"]) == _ANCHORS[fy]["assets"]


def test_prior_column_matches_prior_year_file(payloads: dict) -> None:
    cur = {row["item"]: row for row in payloads["FY2023"]["statements"]["合并利润表"]}
    prev = {row["item"]: row for row in payloads["FY2022"]["statements"]["合并利润表"]}
    for item in ("收入", "毛利", "年度亏损/利润"):
        assert Decimal(cur[item]["上期发生额"]) == Decimal(prev[item]["本期发生额"]), (
            f"{item} 上期列必须等于 FY2022 文件本期值"
        )


def test_income_statement_identities(payloads: dict) -> None:
    for payload in payloads.values():
        for col in ("本期发生额", "上期发生额"):
            income = _col(payload["statements"]["合并利润表"], col)
            assert income["毛利"] == income["收入"] + income["营业成本"]
            assert income["经营亏损/利润"] == (
                income["毛利"]
                + income["销售及市场推广开支"]
                + income["一般及行政开支"]
                + income["产品开发开支"]
                + income["金融资产减值(转回)/计提"]
                + income["其他收入"]
                + income["其他收益/(亏损)净额"]
            )
            assert income["年度亏损/利润"] == (
                income["归属公司所有者"] + income["非控制性权益"]
            )


def test_balance_sheet_identity_holds(payloads: dict) -> None:
    for payload in payloads.values():
        for col in ("期末余额", "期初余额"):
            bs = _col(payload["statements"]["合并资产负债表"], col)
            assert bs["资产总计"] == bs["流动资产合计"] + bs["非流动资产合计"]
            assert bs["负债合计"] == bs["流动负债合计"] + bs["非流动负债合计"]
            assert bs["权益总额"] == (
                bs["归属于公司所有者权益"] + bs["非控制性权益(权益)"]
            )
            assert bs["资产总计"] == bs["权益及负债总额"]


def test_cash_bridge_closes(payloads: dict) -> None:
    for payload in payloads.values():
        for col in ("本期发生额", "上期发生额"):
            cf = _col(payload["statements"]["合并现金流量表"], col)
            assert cf["现金及现金等价物(减少)/增加净额"] == (
                cf["经营活动所得现金净额"]
                + cf["投资活动所用现金净额"]
                + cf["融资活动(所用)所得现金净额"]
            )
            assert cf["年末现金及现金等价物"] == (
                cf["年初现金及现金等价物"]
                + cf["现金及现金等价物(减少)/增加净额"]
                + cf["汇率变动对现金的影响"]
            )


def test_no_synthetic_assumption_lines(payloads: dict) -> None:
    """无来源合成行必须全部移除（处置见来源登记 U-DM-*）。"""

    for payload in payloads.values():
        income_names = {
            row["item"] for row in payload["statements"]["合并利润表"]
        }
        cf_names = {
            row["item"] for row in payload["statements"]["合并现金流量表"]
        }
        assert "其中：利息费用" not in income_names
        assert "折旧与摊销" not in cf_names


def test_statement_payloads_carry_damai_syn_identity(payloads: dict) -> None:
    """演示主体身份 DAMAI.SYN / 大麦物流；来源如实标注菜鸟申请稿。"""

    for fy, payload in payloads.items():
        assert payload.get("stock_code") == "DAMAI.SYN", (
            f"{fy} 必须携带 DAMAI.SYN 独立身份"
        )
        assert payload.get("company") == "大麦物流", f"{fy} 公司名必须为大麦物流"
        provenance = payload["provenance"]
        assert "菜鸟" in provenance["original"] and "申请版本" in provenance["original"]
        assert "大麦" in provenance["original"]
