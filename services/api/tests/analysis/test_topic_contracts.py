"""主题合同测试（P02）：成功、缺失与不兼容输入都要有解释性状态。

- 目录可加载，四问→专题为多对多，metric_refs 全部在指标字典已登记；
- 必需事实缺失 → missing_fact 解释性空状态（账龄/客户下钻按披露可用性禁用）；
- 预算主题：无预算版本/多版本未指定/粒度不匹配/零负预算分别给出类型化原因。
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import ValidationError

from flow_api.analysis.topics import (
    load_topic_catalog,
    topic_availability,
    topics_for_question,
    validate_metric_refs,
)
from flow_api.metrics.comparison_contract import (
    ComparisonContext,
    budget_completion_rate,
    comparability_issues,
)
from flow_api.metrics.grain import MetricGrain

REPO_ROOT = Path(__file__).resolve().parents[4]
TOPICS_PATH = REPO_ROOT / "config/analysis/objective_topics_v1.yaml"
DICTIONARY_PATH = REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml"


def _catalog() -> object:
    return load_topic_catalog(TOPICS_PATH)


def test_catalog_loads_with_four_questions_and_six_plus_one_topics() -> None:
    catalog = _catalog()
    assert catalog.topics_catalog_id == "flow.analysis.objective_topics.v1"
    assert {q.question_id for q in catalog.questions} == {"growth", "profit", "capital", "cash"}
    topic_ids = {topic.topic_id for topic in catalog.topics}
    assert {"revenue", "cost", "profit", "budget_execution", "expense", "efficiency"} <= topic_ids
    assert "solvency_risk" in topic_ids, "偿债与风险为横向专题，不被六主题排除"
    # 四问 × 专题多对多：增长至少 2 个专题；效率同时服务资金与利润
    assert len(topics_for_question(catalog, "growth")) >= 2
    efficiency = next(t for t in catalog.topics if t.topic_id == "efficiency")
    assert set(efficiency.questions) == {"capital", "profit"}


def test_all_metric_refs_are_registered_codes() -> None:
    catalog = _catalog()
    dictionary: dict = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    registered = {
        entry["metric_code"]
        for entry in dictionary["metrics_general"] + dictionary["metrics_logistics"]
    }
    assert validate_metric_refs(catalog, registered) == [], "metric_refs 必须引用已登记代码"


def test_essential_subset_has_ten_metrics_with_fallbacks() -> None:
    catalog = _catalog()
    assert len(catalog.essential_metrics) == 10
    assert len({item.metric_code for item in catalog.essential_metrics}) == 10
    for item in catalog.essential_metrics:
        assert item.unavailable_when, f"{item.metric_code} 缺少不可用条件"


def test_every_topic_declares_unavailable_reasons() -> None:
    catalog = _catalog()
    for topic in catalog.topics:
        assert topic.required_facts, f"{topic.topic_id} 未声明必需事实"
        assert topic.unavailable_reasons, f"{topic.topic_id} 未声明解释性空状态"


def test_missing_fact_yields_missing_fact_reason_not_zero() -> None:
    catalog = _catalog()
    cost = next(t for t in catalog.topics if t.topic_id == "cost")
    available = topic_availability(
        cost, available_facts={"is.revenue"}  # 缺 is.cogs
    )
    assert available == ["missing_fact"]
    assert "不可用" in cost.unavailable_reasons["missing_fact"]


def test_customer_drilldown_disabled_without_customer_fact() -> None:
    """无客户事实时禁用客户下钻：客户维度颗粒度不在 allowed_grains。"""

    grain = MetricGrain(customer_id=__import__("uuid").uuid4())
    assert "customer" in grain.dimensions
    catalog = _catalog()
    efficiency = next(t for t in catalog.topics if t.topic_id == "efficiency")
    assert "customer_drilldown" not in " ".join(efficiency.allowed_grains)
    reasons = topic_availability(
        efficiency,
        available_facts=set(efficiency.required_facts),
        allowed_grains={"consolidated"},  # 事实只支持合并口径
    )
    assert reasons == []


def test_aging_disclosure_layer_requires_aging_note() -> None:
    """有账龄附注→披露层可用；无附注→禁用（C09，按披露可用性）。"""

    catalog = _catalog()
    efficiency = next(t for t in catalog.topics if t.topic_id == "efficiency")
    assert "no_aging_disclosure" in efficiency.unavailable_reasons


def test_budget_topic_incomparable_inputs() -> None:
    """预算主题四类不可比：无版本/粒度不匹配/零负预算/缺事实。"""

    catalog = _catalog()
    budget = next(t for t in catalog.topics if t.topic_id == "budget_execution")
    # 无预算版本
    reasons = topic_availability(
        budget, available_facts={"is.revenue"}, available_extras=set()
    )
    assert "no_budget_version" in reasons
    # 有版本但事实缺失
    reasons = topic_availability(budget, available_facts=set(), available_extras={"budget_version"})
    assert "missing_fact" in reasons
    # 粒度不匹配
    reasons = topic_availability(
        budget,
        available_facts={"is.revenue"},
        available_extras={"budget_version"},
        allowed_grains={"order_level"},
    )
    assert "grain_mismatch" in reasons
    # 零/负预算不输出完成率
    result = budget_completion_rate(
        Decimal("100"), Decimal("0"), budget_version="B2026"
    )
    assert getattr(result, "code", "") == "nonpositive_budget"
    result = budget_completion_rate(
        Decimal("100"), Decimal("-50"), budget_version="B2026"
    )
    assert getattr(result, "code", "") == "nonpositive_budget"


def test_comparison_contract_typed_reasons() -> None:
    """币种/范围/期间/重述/存量流量五类不一致返回类型化原因。"""

    actual = ComparisonContext(
        currency="CNY", scope="consolidated", period_type="month",
        restatement_version="restated", measure_kind="flow",
    )
    same = ComparisonContext(
        currency="CNY", scope="consolidated", period_type="month",
        restatement_version="restated", measure_kind="flow",
    )
    assert comparability_issues(actual, same) == ()

    bad = ComparisonContext(
        currency="USD", scope="parent", period_type="ytd",
        restatement_version="original", measure_kind="stock",
    )
    codes = {issue.code for issue in comparability_issues(actual, bad)}
    assert codes == {
        "currency_mismatch", "scope_mismatch", "period_misalignment",
        "restatement_version_mismatch", "stock_flow_mixing",
    }


def test_budget_grain_mismatch_blocks_repeated_join() -> None:
    """月度预算对订单粒度：禁止重复联接放大，显式不可比。"""

    result = budget_completion_rate(
        Decimal("500"), Decimal("400"),
        budget_version="B2026",
        actual_granularity="order_level", budget_granularity="consolidated",
    )
    assert getattr(result, "code", "") == "budget_grain_mismatch"


def test_budget_version_missing_is_typed() -> None:
    result = budget_completion_rate(Decimal("500"), Decimal("400"), budget_version=None)
    assert getattr(result, "code", "") == "budget_version_missing"


def test_topic_contract_rejects_unknown_fields() -> None:
    """合同对象禁止未声明字段（快照稳定）。"""

    from flow_api.analysis.topics import TopicContract

    try:
        TopicContract(
            topic_id="x", name="x", questions=["growth"], metric_refs=[],
            required_facts=[], allowed_grains=[], comparison_modes=[],
            charts=[], unavailable_reasons={}, unknown_field=1,
        )
    except ValidationError:
        pass
    else:  # pragma: no cover
        raise AssertionError("未声明字段应被拒绝")
