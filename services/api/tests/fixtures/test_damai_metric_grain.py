"""Task A2 顺延项（B3 验收）：大麦指标快照五粒度与 canonical 发行包对账。

- revenue / direct_cost：total、organization、customer_segment、logistics_product、
  segment×product 五种粒度逐一与 canonical operating_actuals 聚合对账；
  direct_cost = 仓储+运输+其他直接成本，三成本不漏算/重算；
- operating_profit / operating_cash_flow：合同仅支持 total/organization 两种粒度，
  与 canonical financial_actuals 对账；
- 期望值直接从发行包 canonical jsonl 独立聚合（不经过 MetricCalculator），
  与 manifest 行数/汇总一致。
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from integration.intake_service_support import clean
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai import loader as damai_loader
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL = REPO_ROOT / "fixtures/damai/canonical"
MONTH_KEY = "2026-08"  # 分析期最后一个月（快照 as_of_month=202608）
TOLERANCE = Decimal("0.01")


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(scope="module")
def seeded() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    clean(session)
    for table in (
        MetricValue,
        AnalysisRun,
        MetricSnapshot,
        AnalysisBatch,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    for table in (
        "finding",
        "evidence",
        "conclusion",
        "review_event",
        "report_snapshot",
        "report_snapshot_item",
        "objective_report_snapshot",
    ):
        session.execute(text(f"DELETE FROM {table}"))
    session.commit()
    damai_loader.seed_damai_demo(session)
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _load_jsonl(name: str) -> list[dict[str, str]]:
    return [
        json.loads(line)
        for line in (CANONICAL / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _expected_operating() -> dict[str, dict[tuple[str | None, ...], Decimal]]:
    """canonical operating_actuals 独立聚合：五粒度期望值。"""

    customers = {row["code"]: row for row in _load_jsonl("customers.jsonl")}
    rows = [row for row in _load_jsonl("operating_actuals.jsonl") if row["month_key"] == MONTH_KEY]
    assert rows, f"canonical 缺少 {MONTH_KEY} 经营明细"

    expected: dict[str, dict[tuple[str | None, ...], Decimal]] = {
        "revenue": {},
        "direct_cost": {},
    }
    grains: tuple[tuple[str, ...], ...] = (
        (),  # total
        ("organization",),
        ("customer_segment",),
        ("logistics_product",),
        ("customer_segment", "logistics_product"),
    )

    def grain_key(row: dict[str, str], grain: tuple[str, ...]) -> tuple[str | None, ...]:
        values: dict[str, str] = {
            "organization": row["organization_code"],
            "customer_segment": customers[row["customer_code"]]["segment_code"],
            "logistics_product": row["logistics_product_code"],
        }
        return tuple(values[name] for name in grain)

    for grain in grains:
        for row in rows:
            key = grain_key(row, grain)
            revenue = Decimal(row["revenue"])
            direct_cost = (
                Decimal(row["warehousing_cost"])
                + Decimal(row["transportation_cost"])
                + Decimal(row["other_direct_cost"])
            )
            expected["revenue"][key] = expected["revenue"].get(key, Decimal("0")) + revenue
            expected["direct_cost"][key] = (
                expected["direct_cost"].get(key, Decimal("0")) + direct_cost
            )
    return expected


def _expected_financial() -> dict[str, dict[tuple[str | None, ...], Decimal]]:
    """canonical financial_actuals 独立聚合：total/organization 两粒度。"""

    rows = [row for row in _load_jsonl("financial_actuals.jsonl") if row["month_key"] == MONTH_KEY]
    assert rows, f"canonical 缺少 {MONTH_KEY} 财务实际"
    return _aggregate_financial(rows, "management_account_code", "OPERATING_PROFIT")


def _expected_financial_ocf() -> dict[tuple[str | None, ...], Decimal]:
    """canonical financial_actuals 的 OCF actual 聚合：total/organization。"""

    rows = [row for row in _load_jsonl("financial_actuals.jsonl") if row["month_key"] == MONTH_KEY]
    return _aggregate_financial(rows, "management_account_code", "OPERATING_CASH_FLOW")


def _expected_budget_ocf() -> dict[tuple[str | None, ...], Decimal]:
    """canonical monthly_budgets 的 OPERATING_CASH_FLOW 预算聚合（total/org）。"""

    rows = [row for row in _load_jsonl("monthly_budgets.jsonl") if row["month_key"] == MONTH_KEY]
    assert rows, f"canonical 缺少 {MONTH_KEY} 预算"
    return _aggregate_financial(rows, "metric_code", "OPERATING_CASH_FLOW")


def _aggregate_financial(
    rows: list[dict[str, str]], code_field: str, wanted: str
) -> dict[tuple[str | None, ...], Decimal]:
    by_org: dict[str, Decimal] = {}
    total = Decimal("0")
    for row in rows:
        if row[code_field] != wanted:
            continue
        amount = Decimal(row["amount"])
        org = row["organization_code"]
        by_org[org] = by_org.get(org, Decimal("0")) + amount
        total += amount
    cells: dict[tuple[str | None, ...], Decimal] = {(): total}
    cells.update({(org,): value for org, value in by_org.items()})
    return cells


def _actual_grains(
    session: Session, comparison_type: str = "actual_month"
) -> dict[str, dict[tuple[str | None, ...], Decimal]]:
    """指标快照实际值：按粒度空值模式分组聚合。"""

    snapshot_id = session.execute(
        text(
            "SELECT ms.id FROM metric_snapshot ms"
            " JOIN dim_period p ON p.id = ms.as_of_period_id"
            " WHERE p.month_key = :month AND ms.status = 'published'"
        ),
        {"month": int(MONTH_KEY.replace("-", ""))},
    ).scalar_one()
    rows = session.execute(
        text(
            "SELECT md.metric_code, o.code AS org, cs.code AS segment, lp.code AS product,"
            " mv.customer_id, mv.region_id, sum(mv.value) AS total"
            " FROM metric_value mv"
            " JOIN metric_definition md ON md.id = mv.metric_definition_id"
            " LEFT JOIN dim_organization o ON o.id = mv.organization_id"
            " LEFT JOIN dim_customer_segment cs ON cs.id = mv.customer_segment_id"
            " LEFT JOIN dim_logistics_product lp ON lp.id = mv.logistics_product_id"
            " WHERE mv.metric_snapshot_id = :sid AND mv.comparison_type = :ctype"
            " AND md.metric_code IN"
            " ('revenue', 'direct_cost', 'operating_profit', 'operating_cash_flow')"
            " GROUP BY 1, 2, 3, 4, 5, 6"
        ),
        {"sid": str(snapshot_id), "ctype": comparison_type},
    ).fetchall()
    actual: dict[str, dict[tuple[str | None, ...], Decimal]] = {}
    for metric_code, org, segment, product, customer_id, region_id, total in rows:
        if customer_id is not None or region_id is not None:
            continue  # customer/region 粒度不在本合同断言范围
        key = tuple(
            value for value in (org, segment, product) if value is not None
        )
        actual.setdefault(metric_code, {})[key] = (
            actual.setdefault(metric_code, {}).get(key, Decimal("0")) + Decimal(str(total))
        )
    return actual


def test_revenue_and_direct_cost_match_canonical_at_five_grains(
    seeded: Session,
) -> None:
    expected = _expected_operating()
    actual = _actual_grains(seeded)
    for metric_code in ("revenue", "direct_cost"):
        assert metric_code in actual, f"{metric_code} 快照无任何粒度值"
        for key, expected_value in expected[metric_code].items():
            actual_value = actual[metric_code].get(key)
            assert actual_value is not None, f"{metric_code} 缺粒度 {key} 的快照值"
            assert abs(actual_value - expected_value) <= TOLERANCE, (
                f"{metric_code} 粒度 {key} 不一致："
                f"快照 {actual_value} vs canonical {expected_value}"
            )


def test_direct_cost_is_full_three_cost_sum(seeded: Session) -> None:
    """direct_cost total = 仓储+运输+其他三成本合计（不漏算/重算）。"""

    expected = _expected_operating()["direct_cost"][()]
    actual = _actual_grains(seeded)["direct_cost"][()]
    assert abs(actual - expected) <= TOLERANCE


def test_financial_metrics_match_canonical_at_supported_grains(
    seeded: Session,
) -> None:
    """operating_profit 和 operating_cash_flow actual 与 canonical 对账。"""

    actual = _actual_grains(seeded)
    expected_profit = _expected_financial()

    cells = actual.get("operating_profit", {})
    assert cells, "operating_profit 快照无任何粒度值"
    for key in cells:
        assert len(key) <= 1, f"operating_profit 出现合同外粒度 {key}"
    for key, expected_value in expected_profit.items():
        actual_value = cells.get(key)
        assert actual_value is not None, f"operating_profit 缺粒度 {key} 的快照值"
        assert abs(actual_value - expected_value) <= TOLERANCE, (
            f"operating_profit 粒度 {key} 不一致：快照 {actual_value} vs canonical {expected_value}"
        )

    ocf_actual = actual.get("operating_cash_flow", {})
    assert ocf_actual, "operating_cash_flow 实际快照缺失"
    for key, expected_value in _expected_financial_ocf().items():
        actual_value = ocf_actual.get(key)
        assert actual_value is not None, f"operating_cash_flow 实际缺粒度 {key}"
        assert abs(actual_value - expected_value) <= TOLERANCE, (
            f"operating_cash_flow 粒度 {key} 不一致："
            f"快照 {actual_value} vs canonical {expected_value}"
        )

    budget = _actual_grains(seeded, comparison_type="budget_month")
    ocf_budget = budget.get("operating_cash_flow", {})
    assert ocf_budget, "operating_cash_flow 预算快照无任何粒度值"
    for key in ocf_budget:
        assert len(key) <= 1, f"operating_cash_flow 预算出现合同外粒度 {key}"
    for key, expected_value in _expected_budget_ocf().items():
        actual_value = ocf_budget.get(key)
        assert actual_value is not None, f"operating_cash_flow 预算缺粒度 {key}"
        assert abs(actual_value - expected_value) <= TOLERANCE, (
            f"operating_cash_flow 预算粒度 {key} 不一致："
                f"快照 {actual_value} vs canonical {expected_value}"
        )
