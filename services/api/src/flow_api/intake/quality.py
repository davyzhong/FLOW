from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from flow_api.data_contract.models import WorkbookContract
from flow_api.data_contract.records import CanonicalPackage
from flow_api.intake.mapping import MappingProposal
from flow_api.intake.reconciliation import ReconciliationCheck, reconcile

IssueSeverity = Literal["blocking", "warning"]


@dataclass(frozen=True, slots=True)
class IssueLocation:
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    target_sheet_id: str | None = None
    target_field_id: str | None = None
    record_id: str | None = None


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    severity: IssueSeverity
    message: str
    location: IssueLocation
    evidence: str
    repair_suggestion: str


@dataclass(frozen=True, slots=True)
class QualityReport:
    issues: tuple[Issue, ...]
    reconciliations: tuple[ReconciliationCheck, ...]

    @property
    def blocking_issues(self) -> tuple[Issue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "blocking")

    @property
    def warning_issues(self) -> tuple[Issue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def publishable(self) -> bool:
        return not self.blocking_issues


def _issue(
    code: str,
    severity: IssueSeverity,
    message: str,
    *,
    location: IssueLocation,
    evidence: str,
    repair: str,
) -> Issue:
    return Issue(code, severity, message, location, evidence, repair)


def _mapping_issues(proposal: MappingProposal) -> list[Issue]:
    issues: list[Issue] = []
    for sheet_id in proposal.unresolved_sheet_ids:
        issues.append(
            _issue(
                "missing_required_sheet_mapping",
                "blocking",
                f"必需工作表角色尚未映射：{sheet_id}",
                location=IssueLocation(target_sheet_id=sheet_id),
                evidence="映射方案中不存在对应源工作表。",
                repair="选择正确的源工作表并保存新的映射版本。",
            )
        )
    for sheet in proposal.sheets:
        for field_id in sheet.unresolved_required_fields:
            issues.append(
                _issue(
                    "missing_required_mapping",
                    "blocking",
                    f"必填字段尚未映射：{sheet.target_sheet_id}.{field_id}",
                    location=IssueLocation(
                        source_sheet=sheet.source_sheet,
                        target_sheet_id=sheet.target_sheet_id,
                        target_field_id=field_id,
                    ),
                    evidence="确定性与已确认映射中均不存在该字段。",
                    repair="映射一个类型和业务语义兼容的源字段。",
                )
            )
        for field in sheet.fields:
            if field.requires_confirmation or field.confidence == "low":
                issues.append(
                    _issue(
                        "low_confidence_mapping",
                        "warning",
                        f"字段映射需要确认：{sheet.target_sheet_id}.{field.target_field_id}",
                        location=IssueLocation(
                            source_sheet=sheet.source_sheet,
                            source_column=field.source_column,
                            target_sheet_id=sheet.target_sheet_id,
                            target_field_id=field.target_field_id,
                        ),
                        evidence=f"{field.method} score={field.score:.2f}: {field.rationale}",
                        repair="由 Finance BP 确认字段口径，或选择其他源字段。",
                    )
                )
    return issues


def _fact_rows(package: CanonicalPackage) -> dict[str, tuple[Any, ...]]:
    return {
        "operating_actual": package.operating_actuals,
        "financial_actual": package.financial_actuals,
        "monthly_budget": package.monthly_budgets,
        "ar_collection": package.ar_collections,
    }


def _grain_issues(package: CanonicalPackage, contract: WorkbookContract) -> list[Issue]:
    issues: list[Issue] = []
    for sheet_id, rows in _fact_rows(package).items():
        grain_fields = contract.get_sheet(sheet_id).grain
        seen: dict[tuple[Any, ...], str] = {}
        for row in rows:
            payload = row.model_dump()
            grain = tuple(payload[field_id] for field_id in grain_fields)
            record_id = str(payload["record_id"])
            if grain in seen:
                issues.append(
                    _issue(
                        "duplicate_grain",
                        "blocking",
                        f"{sheet_id} 存在重复业务粒度。",
                        location=IssueLocation(target_sheet_id=sheet_id, record_id=record_id),
                        evidence=f"与记录 {seen[grain]} 使用相同粒度 {grain!r}。",
                        repair="删除重复记录或修正组成业务粒度的字段。",
                    )
                )
            else:
                seen[grain] = record_id
    return issues


def _relationship_issues(package: CanonicalPackage) -> list[Issue]:
    issues: list[Issue] = []
    organizations = {row.code for row in package.organizations}
    regions = {row.code for row in package.regions}
    customers = {row.code for row in package.customers}
    segments = {row.code for row in package.customer_segments}
    products = {row.code for row in package.logistics_products}
    accounts = {row.code for row in package.management_accounts}
    required_checks: tuple[tuple[str, tuple[Any, ...], str, set[str]], ...] = (
        ("operating_actual", package.operating_actuals, "organization_code", organizations),
        ("operating_actual", package.operating_actuals, "customer_code", customers),
        ("operating_actual", package.operating_actuals, "logistics_product_code", products),
        ("operating_actual", package.operating_actuals, "region_code", regions),
        ("financial_actual", package.financial_actuals, "organization_code", organizations),
        (
            "financial_actual",
            package.financial_actuals,
            "management_account_code",
            accounts,
        ),
        ("monthly_budget", package.monthly_budgets, "organization_code", organizations),
        ("ar_collection", package.ar_collections, "customer_code", customers),
    )
    for sheet_id, rows, field_id, allowed in required_checks:
        for row in rows:
            value = getattr(row, field_id)
            if value not in allowed:
                issues.append(
                    _issue(
                        "broken_required_relation",
                        "blocking",
                        f"必需维度关联失败：{sheet_id}.{field_id}",
                        location=IssueLocation(
                            target_sheet_id=sheet_id,
                            target_field_id=field_id,
                            record_id=row.record_id,
                        ),
                        evidence=f"{value!r} 不存在于对应主数据。",
                        repair="补充主数据，或修正事实记录中的业务编码。",
                    )
                )
    optional_checks = (
        ("customer_segment_code", segments),
        ("logistics_product_code", products),
        ("management_account_code", accounts),
    )
    for row in package.monthly_budgets:
        for field_id, allowed in optional_checks:
            value = getattr(row, field_id)
            if value is not None and value not in allowed:
                issues.append(
                    _issue(
                        "unmatched_optional_dimension",
                        "warning",
                        f"可选预算维度无法关联：{field_id}",
                        location=IssueLocation(
                            target_sheet_id="monthly_budget",
                            target_field_id=field_id,
                            record_id=row.record_id,
                        ),
                        evidence=f"{value!r} 不存在于对应主数据。",
                        repair="确认是否保留为未匹配维度，或修正业务编码。",
                    )
                )
    return issues


def _business_warnings(package: CanonicalPackage) -> list[Issue]:
    issues: list[Issue] = []
    amount_fields = (
        "revenue",
        "warehousing_cost",
        "transportation_cost",
        "other_direct_cost",
    )
    for row in package.operating_actuals:
        for field_id in amount_fields:
            value: Decimal = getattr(row, field_id)
            if value < 0:
                issues.append(
                    _issue(
                        "unexpected_negative",
                        "warning",
                        f"经营事实出现异常负值：{field_id}",
                        location=IssueLocation(
                            target_sheet_id="operating_actual",
                            target_field_id=field_id,
                            record_id=row.record_id,
                        ),
                        evidence=f"值为 {value}。",
                        repair="确认是否为冲销/退款，并记录业务原因。",
                    )
                )
        if row.order_count == 0 and row.revenue != 0:
            issues.append(
                _issue(
                    "revenue_without_orders",
                    "warning",
                    "订单量为零但营业收入不为零。",
                    location=IssueLocation(
                        target_sheet_id="operating_actual", record_id=row.record_id
                    ),
                    evidence=f"order_count={row.order_count}, revenue={row.revenue}",
                    repair="确认收入是否跨期、补录订单量，或说明特殊业务口径。",
                )
            )
    return issues


def _reconciliation_issues(checks: tuple[ReconciliationCheck, ...]) -> list[Issue]:
    return [
        _issue(
            "reconciliation_outside_tolerance",
            "blocking",
            f"经营财务对账超出阈值：{check.code}",
            location=IssueLocation(),
            evidence=(
                f"expected={check.expected_value}, actual={check.actual_value}, "
                f"difference={check.difference}, tolerance={check.tolerance}"
            ),
            repair="核对经营与财务来源、映射口径和期间后创建新的导入版本。",
        )
        for check in checks
        if not check.passed
    ]


def _sort_key(issue: Issue) -> tuple[Any, ...]:
    return (
        0 if issue.severity == "blocking" else 1,
        issue.code,
        issue.location.target_sheet_id or "",
        issue.location.target_field_id or "",
        issue.location.record_id or "",
        issue.location.source_sheet or "",
        issue.location.source_column or "",
    )


def evaluate_quality(
    package: CanonicalPackage,
    contract: WorkbookContract,
    proposal: MappingProposal,
    *,
    reconciliation_tolerance: Decimal = Decimal("0.01"),
) -> QualityReport:
    checks = reconcile(package, reconciliation_tolerance)
    issues = (
        _mapping_issues(proposal)
        + _grain_issues(package, contract)
        + _relationship_issues(package)
        + _business_warnings(package)
        + _reconciliation_issues(checks)
    )
    return QualityReport(tuple(sorted(issues, key=_sort_key)), checks)
