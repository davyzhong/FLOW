"""P01 指标语义订正测试（C02–C05 订正的先导契约）。

- MPM 分类不变量：任何指标不得仅因"管理常用"获得 IFRS 18 MPM 监管标签；
  mpm=true 必须携带已核验的结构化判定（mpm_review），否则数据无效；
- FCF/EBITDA 是管理口径指标：mpm 必须为 false，且口径说明不得与经营现金流混称；
- 负净利润时净现比不得以正常数值展示（渲染层降级）；
- 别名搜索与主名/代码解析到同一指标身份。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import yaml

from flow_api.metric_library_store.search import resolve_metric_identity
from flow_api.metrics.mpm_semantics import assert_mpm_labels_valid
from flow_api.statements.objective_report_html import render_objective_report_v3

REPO_ROOT = Path(__file__).resolve().parents[4]
DICTIONARY_PATH = REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml"


def _load_entries() -> list[dict]:
    data: dict = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    return data["metrics_general"] + data["metrics_logistics"]


def _by_code(entries: list[dict], code: str) -> dict:
    return next(entry for entry in entries if entry["metric_code"] == code)


def test_no_metric_gets_mpm_label_without_verified_review() -> None:
    """mpm=true 是监管级断言，必须携带已核验的结构化判定，裸布尔无效。"""

    for entry in _load_entries():
        if not entry.get("mpm"):
            continue
        review = entry.get("mpm_review")
        assert isinstance(review, dict), (
            f"{entry['metric_code']}: mpm=true 缺少结构化判定 mpm_review"
        )
        assert review.get("determination") == "verified_applicable"
        assert review.get("verified") is True


def test_free_cash_flow_is_not_labeled_mpm() -> None:
    """FCF 管理常用 ≠ 监管 MPM：静态字典不得打 IFRS 18 标签。"""

    entry = _by_code(_load_entries(), "free_cash_flow")
    assert entry.get("mpm") is False
    review = entry.get("mpm_review") or {}
    assert review.get("determination") in ("candidate", "management_caliber")
    assert "2027" in json_str(entry) or "IFRS 18" in str(entry.get("caliber", ""))


def json_str(entry: dict) -> str:
    return str(entry.get("mpm_review", {}))


def test_ebitda_family_is_conditional_candidate_with_cash_terms_fix() -> None:
    """EBITDA 家族：候选而非已认定；且不得与经营现金流混称'现金'（C03）。"""

    entries = _load_entries()
    for code in ("ebitda", "adjusted_ebitda", "ebitda_margin"):
        entry = _by_code(entries, code)
        assert entry.get("mpm") is False, f"{code} 不得静态携带监管 MPM 标签"
        review = entry.get("mpm_review") or {}
        assert review.get("determination") == "candidate"
    for code in ("ebitda", "free_cash_flow"):
        entry = _by_code(entries, code)
        caliber = str(entry.get("caliber", ""))
        assert "现金" in caliber and "不" in caliber, (
            f"{code} 口径说明须声明非现金流量表定义的现金（C03）"
        )


def test_clearly_misabeled_entries_flipped_to_false() -> None:
    """准则定义小计/成本口径/内部经营指标不是管理定义业绩指标（C02）。"""

    entries = _load_entries()
    for code in ("operating_profit", "direct_cost", "collection_rate"):
        entry = _by_code(entries, code)
        assert entry.get("mpm") is False, f"{code} 属明确误标，必须改为 false"


def test_assert_mpm_labels_valid_accepts_corrected_and_rejects_bare_true() -> None:
    """语义校验函数：裸 mpm=true 拒绝；false + candidate 放行。"""

    corrected = SimpleNamespace(
        metric_code="free_cash_flow", mpm=False,
        mpm_review={"determination": "candidate", "verified": False},
    )
    assert_mpm_labels_valid([corrected])  # 不抛

    bad = SimpleNamespace(metric_code="x_ratio", mpm=True, mpm_review=None)
    try:
        assert_mpm_labels_valid([corrected, bad])
    except ValueError as error:
        assert "x_ratio" in str(error)
    else:  # pragma: no cover
        raise AssertionError("裸 mpm=true 未被拒绝")


def test_negative_net_profit_degrades_ocf_ratio_display() -> None:
    """净净利润为负时净现比失真：KPI 不得显示正常数值，须显式降级说明。"""

    report = SimpleNamespace(
        company_name="测试公司", stock_code="000000.SZ", report_kind="一季报",
        period_label="2026Q1", unit_note="人民币千元",
    )
    normalized = [
        SimpleNamespace(
            report_id="r1", mapping_version="v1", statement_type="合并利润表",
            item_name="净利润", item_id="is.net_profit",
            value_current=-500_000, value_prior=None,
            value_begin=None, value_end=None,
        ),
        SimpleNamespace(
            report_id="r1", mapping_version="v1", statement_type="合并现金流量表",
            item_name="经营活动产生的现金流量净额", item_id="cf.ocf",
            value_current=300_000, value_prior=None,
            value_begin=None, value_end=None,
        ),
    ]
    result = SimpleNamespace(
        catalog_id="flow.analysis.objective_finance.v1", entries=(),
    )
    html = render_objective_report_v3(
        report, result, normalized,
        generated_at=__import__("datetime").datetime(2026, 9, 7, 0, 0),
    )
    assert "净现比" in html
    assert "0.60" not in html, "负净利润下不得显示正常净现比数值"
    assert "净利润为负" in html, "须显式标注降级原因"


def test_alias_resolves_to_same_identity() -> None:
    """别名（FCF）与主名/代码解析到同一指标身份。"""

    entries = [
        SimpleNamespace(
            metric_code="free_cash_flow", name="自由现金流",
            aliases=["FCF", "自由现金流FCF"],
        ),
        SimpleNamespace(metric_code="ocf_net_profit_ratio", name="盈利现金比率",
                        aliases=["净利润现金含量"]),
    ]
    by_code = resolve_metric_identity(entries, "free_cash_flow")
    by_name = resolve_metric_identity(entries, "自由现金流")
    by_alias = resolve_metric_identity(entries, "FCF")
    assert by_code is not None and by_name is not None and by_alias is not None
    assert by_code.metric_code == by_name.metric_code == by_alias.metric_code
    assert resolve_metric_identity(entries, "不存在") is None
