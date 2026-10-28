"""M1 科目级映射单测：前缀优先、方向净额、未命中回落计数、配置校验。"""
from __future__ import annotations

from decimal import Decimal

import pytest

from flow_api.importer.account_mapping import (
    AccountGroup,
    load_account_groups,
    map_balance_rows,
)
from flow_api.importer.publish_chain import _repository_root


def _row(code: str, direction: str, closing: str, period: str = "2025-01") -> dict[str, object]:
    return {
        "period": period,
        "account_code": code,
        "direction": direction,
        "closing_balance": Decimal(closing),
    }


@pytest.fixture()
def groups() -> tuple[AccountGroup, ...]:
    return load_account_groups(
        _repository_root() / "config/importer/account_mapping_v1.yaml"
    )


def test_load_groups_from_config(groups) -> None:
    codes = [group.management_account for group in groups]
    assert codes == ["TB_CASH", "TB_AR", "TB_INVENTORY", "TB_FIXED_ASSET", "TB_AP"]


def test_direction_net_fixed_assets(groups) -> None:
    # 1601 原值（借）50000，1602 累计折旧（贷）12000 → 净额 38000
    result = map_balance_rows(
        [_row("1601", "借", "50000"), _row("1602", "贷", "12000")], groups
    )
    assert result.amounts["2025-01"]["TB_FIXED_ASSET"] == Decimal("38000")


def test_cash_group_sums_debit_direction(groups) -> None:
    result = map_balance_rows(
        [_row("1001", "借", "12000"), _row("1002", "借", "8000"), _row("1012", "贷", "500")],
        groups,
    )
    assert result.amounts["2025-01"]["TB_CASH"] == Decimal("19500")


def test_prefix_priority_and_unmatched(groups) -> None:
    # 1001 归 TB_CASH（先命中先得）；2001/6001 未命中计数回落
    result = map_balance_rows(
        [_row("1001", "借", "100"), _row("2001", "贷", "100"), _row("6001", "贷", "0")],
        groups,
    )
    assert result.matched_rows == {"TB_CASH": 1}
    assert result.unmatched_rows == 2


def test_periods_are_independent(groups) -> None:
    result = map_balance_rows(
        [_row("1001", "借", "100", "2025-01"), _row("1001", "借", "300", "2025-02")], groups
    )
    assert result.amounts["2025-01"]["TB_CASH"] == Decimal("100")
    assert result.amounts["2025-02"]["TB_CASH"] == Decimal("300")


def test_duplicate_management_account_rejected() -> None:
    import tempfile
    from pathlib import Path

    payload = """
version: t
groups:
  - management_account: TB_A
    name: 甲
    direction: 借
    code_prefixes: ["1001"]
  - management_account: TB_A
    name: 乙
    direction: 贷
    code_prefixes: ["2001"]
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
        handle.write(payload)
        path = handle.name
    try:
        with pytest.raises(ValueError, match="duplicate"):
            load_account_groups(path)
    finally:
        Path(path).unlink()
