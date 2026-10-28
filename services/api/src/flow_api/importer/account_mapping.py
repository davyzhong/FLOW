"""科目级映射（M1）：科目编码前缀 → 明细管理科目组。

规则（与 config/importer/account_mapping_v1.yaml 声明一致）：
- 前缀顺序即优先级，一个科目只归最先命中的组；
- 组内金额 = Σ(方向匹配组的期末余额) − Σ(反向期末余额)（方向净额，
  固定资产净额=借向原值−贷向折旧/减值由此成立）；
- 未命中科目由调用方回落类别聚合，本模块不负责基线五科目。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class AccountGroup:
    management_account: str
    name: str
    direction: str
    code_prefixes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MappingResult:
    """期间 × 明细管理科目 → 方向净额；以及逐组命中的科目行数。

    matched_by_period 只记录该期间确实命中行的组——空组不写 0 金额事实
    （缺席≠零：环比 variance 对 0/0 会硬崩，且 0 会冒充真实余额）。
    """

    amounts: dict[str, dict[str, Decimal]]
    matched_rows: dict[str, int]
    matched_by_period: dict[str, set[str]]
    unmatched_rows: int


def load_account_groups(path: str | Path) -> tuple[AccountGroup, ...]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("groups"), list):
        raise ValueError("account mapping must declare a groups list")
    groups: list[AccountGroup] = []
    seen_accounts: set[str] = set()
    for raw in payload["groups"]:
        group = AccountGroup(
            management_account=str(raw["management_account"]),
            name=str(raw["name"]),
            direction=str(raw["direction"]),
            code_prefixes=tuple(str(code) for code in raw["code_prefixes"]),
        )
        if group.management_account in seen_accounts:
            raise ValueError(f"duplicate management account: {group.management_account}")
        if group.direction not in ("借", "贷"):
            raise ValueError(f"{group.management_account}: direction must be 借/贷")
        seen_accounts.add(group.management_account)
        groups.append(group)
    return tuple(groups)


def _match_prefix(account_code: str, groups: tuple[AccountGroup, ...]) -> AccountGroup | None:
    for group in groups:
        if any(account_code.startswith(prefix) for prefix in group.code_prefixes):
            return group
    return None


def map_balance_rows(
    balances: list[dict[str, object]],
    groups: tuple[AccountGroup, ...],
) -> MappingResult:
    """按期间聚合明细组方向净额；未命中行计数返回（调用方回落类别聚合）。"""
    periods: dict[str, dict[str, Decimal]] = {}
    matched_rows: dict[str, int] = {}
    matched_by_period: dict[str, set[str]] = {}
    unmatched = 0
    for row in balances:
        period = str(row["period"])
        account_code = str(row["account_code"])
        closing = row["closing_balance"]  # type: ignore[union-attr]
        direction = str(row["direction"])
        group = _match_prefix(account_code, groups)
        if group is None:
            unmatched += 1
            continue
        bucket = periods.setdefault(
            period,
            {group.management_account: _ZERO for group in groups},
        )
        signed = closing if direction == group.direction else -closing  # type: ignore[operator]
        bucket[group.management_account] += signed  # type: ignore[operator]
        matched_rows[group.management_account] = matched_rows.get(group.management_account, 0) + 1
        matched_by_period.setdefault(period, set()).add(group.management_account)
    return MappingResult(
        amounts=periods,
        matched_rows=matched_rows,
        matched_by_period=matched_by_period,
        unmatched_rows=unmatched,
    )


__all__ = ["AccountGroup", "MappingResult", "load_account_groups", "map_balance_rows"]
