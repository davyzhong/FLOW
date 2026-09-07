"""四层覆盖率（P02，订正 C11）：登记 / 可执行 / 源数据覆盖 / 展示启用 分开计数。

禁止把"登记 55 条"表述为"55 条可算/可展示"；输出逐指标覆盖行，
避免只报告总数（总数会掩盖层层折损）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoverageRow:
    metric_code: str
    registered: bool
    executable: bool
    source_covered: bool
    display_enabled: bool


@dataclass(frozen=True, slots=True)
class CoverageReport:
    rows: tuple[CoverageRow, ...]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "registered": sum(r.registered for r in self.rows),
            "executable": sum(r.executable for r in self.rows),
            "source_covered": sum(r.source_covered for r in self.rows),
            "display_enabled": sum(r.display_enabled for r in self.rows),
            "total": len(self.rows),
        }


def four_layer_coverage(
    registered_codes: set[str],
    executable_codes: set[str],
    source_covered_codes: set[str],
    display_enabled_codes: set[str],
) -> CoverageReport:
    """逐指标四层覆盖行。

    高层蕴含低层：可执行必然已登记；源数据覆盖必然可执行；展示启用必然源数据覆盖。
    输入之间不一致（如展示启用但未登记）按低层截断，不虚报。
    """

    def _and(value: bool, *required: bool) -> bool:
        return value and all(required)

    rows = []
    all_codes = (
        registered_codes | executable_codes | source_covered_codes | display_enabled_codes
    )
    for code in sorted(all_codes):
        registered = code in registered_codes
        executable = _and(code in executable_codes, registered)
        source_covered = _and(code in source_covered_codes, executable)
        display_enabled = _and(code in display_enabled_codes, source_covered)
        rows.append(
            CoverageRow(
                metric_code=code,
                registered=registered,
                executable=executable,
                source_covered=source_covered,
                display_enabled=display_enabled,
            )
        )
    return CoverageReport(rows=tuple(rows))


__all__ = ["CoverageReport", "CoverageRow", "four_layer_coverage"]
