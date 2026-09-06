"""四表一注覆盖与质量规则（B04）。

按报告种类评估抽取结果的覆盖度与勾稽质量：
- 覆盖状态四态：passed / failed / missing / not_applicable（不适用）；
- 年报要求四表 + 附注清单；季报要求三表；业绩公告只要求收益简表；
- 缺权益变动表或附注时不得标「四表一注完整」；
- 关键勾稽不平衡（资产负债表恒等式、利润归属、现金桥）构成发布阻断项。

附注本期定位为披露项目清单与取数定位（D041），不做全文重建。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from flow_api.statements.extraction import ExtractionResult

STATEMENT_BS = "合并资产负债表"
STATEMENT_IS = "合并利润表"
STATEMENT_CF = "合并现金流量表"
STATEMENT_EQ = "合并所有者权益变动表"
NOTES = "附注"


class CoverageStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


# 报告种类 → 必需报表（附注以披露清单计）
REQUIRED_BY_KIND: dict[str, tuple[str, ...]] = {
    "年报": (STATEMENT_BS, STATEMENT_IS, STATEMENT_CF, STATEMENT_EQ, NOTES),
    "一季报": (STATEMENT_BS, STATEMENT_IS, STATEMENT_CF),
    "中报": (STATEMENT_BS, STATEMENT_IS, STATEMENT_CF, STATEMENT_EQ, NOTES),
    "三季报": (STATEMENT_BS, STATEMENT_IS, STATEMENT_CF),
    "业绩公告": (STATEMENT_IS,),
}

# 关键勾稽：任一失败即阻断正式发布
CRITICAL_CHECK_PATTERNS = (
    "资产总计=负债合计+所有者权益合计",
    "資產總額=權益及負債總額",
    "资产总计=流动资产合计+非流动资产合计",
    "净利润=归母+少数股东损益",
    "年度利潤=本公司所有者+非控制性權益",
    "毛利=收入+收入成本",
    "毛利=收入-營業成本",
    "期末现金=期初+净增加额",
    "年末現金=年初+淨變動+外匯",
)


@dataclass(frozen=True, slots=True)
class StatementCoverage:
    statement_type: str
    status: CoverageStatus
    item_count: int
    failed_checks: tuple[str, ...] = ()
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReportQuality:
    coverage: tuple[StatementCoverage, ...]
    four_statements_complete: bool
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def publishable(self) -> bool:
        return not self.blockers


def evaluate_report_quality(
    result: ExtractionResult, *, report_kind: str
) -> ReportQuality:
    """评估一份抽取结果的覆盖度与质量；阻断项与缺失如实返回。"""

    required = REQUIRED_BY_KIND.get(report_kind)
    if required is None:
        raise ValueError(f"未知报告种类：{report_kind}（可用：{sorted(REQUIRED_BY_KIND)}）")

    failed_labels = tuple(c.label for c in result.checks if c.status == "不一致")
    coverage: list[StatementCoverage] = []
    for statement in required:
        if statement == NOTES:
            coverage.append(
                StatementCoverage(
                    statement_type=NOTES,
                    status=CoverageStatus.MISSING,
                    item_count=0,
                    note="附注未覆盖：披露清单与取数定位待建设（不阻碍三表勾稽结论）",
                )
            )
            continue
        if statement == STATEMENT_EQ:
            coverage.append(
                StatementCoverage(
                    statement_type=STATEMENT_EQ,
                    status=CoverageStatus.MISSING,
                    item_count=0,
                    note="权益变动表未被当前适配器覆盖（披露可能存在，抽取缺口如实记录）",
                )
            )
            continue
        items = result.statements.get(statement)
        if not items:
            if report_kind == "业绩公告":
                status = CoverageStatus.NOT_APPLICABLE
                note = "业绩公告为简表，该报表不在披露范围内"
            else:
                status = CoverageStatus.MISSING
                note = None
            coverage.append(
                StatementCoverage(
                    statement_type=statement,
                    status=status,
                    item_count=0,
                    note=note,
                )
            )
            continue
        related_failures = tuple(
            label for label in failed_labels if _check_belongs_to(label, statement)
        )
        coverage.append(
            StatementCoverage(
                statement_type=statement,
                status=CoverageStatus.FAILED if related_failures else CoverageStatus.PASSED,
                item_count=len(items),
                failed_checks=related_failures,
            )
        )

    blockers = tuple(
        label for label in failed_labels if _is_critical(label)
    )
    # 「四表一注完整」只适用于年报：权益变动表与附注同备且全部勾稽通过。
    # 季报/业绩公告在本字段上恒为 False（完整性由 coverage 各态表达）。
    complete = (
        report_kind == "年报"
        and all(c.status == CoverageStatus.PASSED for c in coverage)
        and not blockers
    )
    return ReportQuality(
        coverage=tuple(coverage),
        four_statements_complete=complete,
        blockers=blockers,
        warnings=result.warnings,
    )


def _check_belongs_to(label: str, statement: str) -> bool:
    groups = {
        STATEMENT_BS: ("资产", "负债", "权益", "資產", "負債", "權益"),
        STATEMENT_IS: ("利润", "毛利", "收入", "盈利", "利潤", "除稅", "年度"),
        STATEMENT_CF: ("现金", "現金", "经营净额", "财状"),
    }
    return any(token in label for token in groups.get(statement, ()))


def _is_critical(label: str) -> bool:
    return any(pattern in label for pattern in CRITICAL_CHECK_PATTERNS)


__all__ = [
    "CoverageStatus",
    "ReportQuality",
    "StatementCoverage",
    "evaluate_report_quality",
]
