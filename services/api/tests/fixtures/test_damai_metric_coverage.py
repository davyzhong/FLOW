from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DICTIONARY_PATH = REPOSITORY_ROOT / "config/metrics/metric_dictionary_v1_1.yaml"
COVERAGE_PATH = REPOSITORY_ROOT / "config/metrics/damai_demo_metric_coverage_v1.yaml"
GENERATOR_PATH = REPOSITORY_ROOT / "scripts/build_damai_metric_coverage.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("build_damai_metric_coverage", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_damai_coverage_is_generated_from_current_metric_dictionary() -> None:
    dictionary = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    coverage = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))

    assert coverage["synthetic"] is True
    assert coverage["dictionary_id"] == dictionary["dictionary_id"]
    assert coverage["metrics_source"] == "config/metrics/metric_dictionary_v1_1.yaml"
    assert (
        coverage["metrics_source_sha256"]
        == hashlib.sha256(DICTIONARY_PATH.read_bytes()).hexdigest()
    )
    assert [row["metric_code"] for row in coverage["metrics"]] == [
        row["metric_code"] for row in dictionary["metrics_general"]
    ]
    assert {
        snapshot["period"]: (snapshot["computable"], snapshot["total"])
        for snapshot in coverage["snapshots"]
    } == {
        "FY2022": (32, 50),
        "FY2023": (32, 50),
    }


def test_current_dictionary_formulas_reconcile_on_damai_statements() -> None:
    generator = _load_generator()
    dictionary = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    engine = generator.Engine(
        {"facts": generator.build_damai_facts()},
        dictionary,
    )
    company = "damai_syn"
    period = "FY2023"

    def metric(code: str) -> float:
        return engine.ev_metric(code, company, period)

    # 利息费用在申请稿披露利润表中无独立行（旧合成「其中：利息费用」已移除）
    # →利息保障倍数必须如实缺省，不得用财务费用冒充
    coverage = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))
    interest = next(m for m in coverage["metrics"] if m["metric_code"] == "interest_coverage")
    assert all(cell["missing"] for cell in interest["cells"].values())
    assert (
        abs(metric("ccc_days") - (metric("dso_days") + metric("dio_days") - metric("dpo_days")))
        < 1e-9
    )
    assert (
        abs(
            metric("roe")
            - metric("net_margin") * metric("total_asset_turnover") * metric("equity_multiplier")
        )
        < 1e-9
    )

    facts = {
        (fact["item_id"], fact["role"]): fact["value"]
        for fact in generator.build_damai_facts()
        if fact["company"] == company and fact["period"] == period
    }
    expected_expense_ratio = sum(
        facts[(item_id, "cur")]
        for item_id in ("is.selling_exp", "is.admin_exp", "is.rnd_exp", "is.fin_exp")
    ) / facts[("is.revenue", "cur")]
    assert abs(metric("period_expense_ratio") - expected_expense_ratio) < 1e-9

    # 现金流家族（F3）：申请稿直接法现金流披露 OCF/ICF/FCF 融资净额与资本开支行；
    # capex 以绝对值入映射（披露原值为负、流出），FCF = OCF − Capex 语义成立。
    ocf = facts[("cf.ocf", "cur")]
    capex = facts[("cf.capex", "cur")]
    net_profit = facts[("is.net_profit", "cur")]
    assert capex > 0, "capex 必须以流出绝对值入库"
    assert abs(metric("free_cash_flow") - (ocf - capex)) < 1e-9
    assert metric("free_cash_flow") < 0, "申请稿期资本开支超过经营现金流入，FCF 必须为负"
    assert abs(metric("ocf_net_profit_ratio") - ocf / net_profit) < 1e-9


def test_coverage_honestly_marks_disclosure_absent_inputs() -> None:
    """申请稿未披露的输入对应指标必须整族如实缺省（F3 口径裁决）。

    - 利息费用无独立行（旧合成「其中：利息费用」已移除）→ 利息相关 8 项；
    - 「借款」为长短期混合行，无短借拆分 → 短债相关 4 项；
    - 直接法现金流无「销售收现」行 → 收现比；
    - NOPAT/可持续增长率需要披露外输入；量价拆分属于运营数据集（非财报口径）。
    """

    coverage = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))
    expected_missing = {
        "interest_coverage": "is.interest_exp",
        "ebitda_interest_coverage": "is.interest_exp",
        "total_assets_return": "is.interest_exp",
        "roce": "is.interest_exp",
        "ebitda": "is.interest_exp",
        "adjusted_ebitda": "is.interest_exp",
        "ebitda_margin": "is.interest_exp",
        "ocf_interest_coverage": "is.interest_exp",
        "total_debt_capitalization": "bs.short_debt",
        "cash_short_debt_ratio": "bs.short_debt",
        "debt_ebitda": "bs.short_debt",
        "ocf_total_debt_ratio": "bs.short_debt",
        "roic": "nopat",
        "eva": "nopat",
        "sgr": "identity_1",
        "volume_growth": "volume_current",
        "price_change_rate": "price_current",
    }
    assert len(expected_missing) == 17
    for metric_row in coverage["metrics"]:
        cell = metric_row["cells"]["damai_syn FY2023"]
        code = metric_row["metric_code"]
        if code in expected_missing or code == "cash_revenue_ratio":
            assert cell["display"] is None, f"{code} 应如实缺省"
            assert cell["missing"], f"{code} 缺口必须带原因"
            if code in expected_missing:
                assert cell["missing"].startswith(expected_missing[code]), (
                    f"{code} 缺口输入不符：{cell['missing']}"
                )
    computable = {
        row["metric_code"]
        for row in coverage["metrics"]
        if row["cells"]["damai_syn FY2023"]["display"] is not None
    }
    assert expected_missing.keys() | {"cash_revenue_ratio"} <= (
        {m["metric_code"] for m in coverage["metrics"]} - computable
    )
