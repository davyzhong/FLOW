"""利润表项目映射（M2）：自由文本「项目」列 → IS_* 管理科目。

标准化：去首尾空白、去全/半角冒号结尾、去「减：/加：/其中：」前缀后
精确匹配字典；未匹配项忽略并由调用方在回执列出（不虚构归属）。

口径边界（work_item FLOW-WI-IMPORTER-RICH-METRICS-20261028-001 M2）：
损益明细（成本/费用分项）只来自利润表；科目级映射只做资产负债结构，
不双源。收入/费用合计仍以科目余额表类别聚合为准（R5 等价基线零扰动）。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# (标准化项目名, IS_* 管理科目码)；顺序即展示顺序，与一般企业利润表一致
INCOME_ITEM_ACCOUNTS: tuple[tuple[str, str], ...] = (
    ("营业收入", "IS_REVENUE"),
    ("营业成本", "IS_COST"),
    ("税金及附加", "IS_TAX_SURCHARGE"),
    ("销售费用", "IS_SELLING"),
    ("管理费用", "IS_ADMIN"),
    ("研发费用", "IS_RD"),
    ("财务费用", "IS_FINANCE"),
    ("营业利润", "IS_OPERATING_PROFIT"),
    ("营业外收入", "IS_NONOPERATING_INCOME"),
    ("营业外支出", "IS_NONOPERATING_EXPENSE"),
    ("利润总额", "IS_TOTAL_PROFIT"),
    ("所得税费用", "IS_INCOME_TAX"),
    ("净利润", "IS_NET_PROFIT"),
)

_ITEM_TO_ACCOUNT: dict[str, str] = dict(INCOME_ITEM_ACCOUNTS)

_PREFIXES = ("减：", "加：", "其中：", "减:", "加:", "其中:")


def normalize_item(raw: str) -> str:
    text = (raw or "").strip()
    changed = True
    while changed:
        changed = False
        for prefix in _PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
                changed = True
        if text and text[-1] in "：:":
            text = text[:-1].strip()
            changed = True
    return text


@dataclass(frozen=True, slots=True)
class IncomeMapping:
    """期间 × IS_* 科目 → 本期金额；未匹配项目按期间列出。"""

    amounts: dict[str, dict[str, Decimal]]
    unmapped: dict[str, tuple[str, ...]]

    @property
    def periods(self) -> tuple[str, ...]:
        return tuple(sorted(self.amounts))


def map_income_items(rows: list[dict[str, object]]) -> IncomeMapping:
    """把利润表存储行映射为期间 × IS_* 科目金额（本期金额口径）。"""
    amounts: dict[str, dict[str, Decimal]] = {}
    unmapped: dict[str, tuple[str, ...]] = {}
    for row in rows:
        period = str(row["period"])
        item = normalize_item(str(row["item"]))
        account = _ITEM_TO_ACCOUNT.get(item)
        if account is None:
            existing = unmapped.setdefault(period, ())
            if item and item not in existing:
                unmapped[period] = (*existing, item)
            continue
        bucket = amounts.setdefault(period, {})
        bucket[account] = bucket.get(account, Decimal("0")) + Decimal(str(row["current_amount"]))
    return IncomeMapping(amounts=amounts, unmapped=unmapped)


__all__ = [
    "INCOME_ITEM_ACCOUNTS",
    "IncomeMapping",
    "map_income_items",
    "normalize_item",
]
