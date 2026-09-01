from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from flow_api.dashboard.formatting import (
    available_value,
    comparison_value,
    unavailable_value,
)
from flow_api.dashboard.models import (
    ActiveFilters,
    BridgeDriver,
    DashboardContext,
    DashboardDegradation,
    DashboardOverview,
    DashboardValue,
    DataStatus,
    DimensionName,
    DimensionOption,
    FilterDimension,
    FilterOptions,
    FindingItem,
    Highlight,
    MarginMatrix,
    MatrixCell,
    MetricCard,
    ProductPerformance,
    ProductRow,
    ProfitBridge,
    TrendPanel,
    TrendPoint,
)
from flow_api.dashboard.repositories import (
    DashboardSourceBundle,
    DashboardSourceRepository,
    PublishedMetricValue,
)

DashboardFilterErrorCode = Literal[
    "unsupported_filter_combination", "unknown_filter_value"
]


class DashboardFilterError(ValueError):
    def __init__(self, code: DashboardFilterErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class DashboardCoreProjection:
    context: DashboardContext
    filter_options: FilterOptions
    active_filters: ActiveFilters
    data_status: DataStatus
    metric_cards: tuple[MetricCard, ...]


@dataclass(frozen=True, slots=True)
class DashboardAnalysisProjection:
    profit_bridge: ProfitBridge
    findings: tuple[FindingItem, ...]
    highlights: tuple[Highlight, ...]


@dataclass(frozen=True, slots=True)
class DashboardDimensionViews:
    product_table: ProductPerformance
    margin_matrix: MarginMatrix


CARD_DEFINITIONS = (
    ("orders", "履约订单量", "规模", "order", False),
    ("revenue", "营业收入", "增长", "CNY", False),
    ("revenue_per_order", "单均收入", "价格/结构", "CNY/order", False),
    ("gross_margin", "毛利率", "盈利", "ratio", False),
    ("fulfillment_cost_rate", "履约成本率", "成本", "ratio", True),
    ("operating_profit", "经营利润", "利润", "CNY", False),
    ("ar_balance", "应收账款", "营运资本", "CNY", True),
    ("operating_cash_flow", "经营现金流", "现金", "CNY", False),
)
RATIO_METRICS = frozenset({"gross_margin", "fulfillment_cost_rate"})
SUPPORTED_DIMENSION_COMBINATIONS: tuple[tuple[DimensionName, ...], ...] = (
    (),
    ("organization",),
    ("customer_segment",),
    ("logistics_product",),
    ("region",),
    ("customer_segment", "logistics_product"),
)
DIMENSION_ORDER = {
    "organization": {"FLOW_GROUP": 0, "ORG_NORTH": 1, "ORG_SOUTH": 2},
    "customer_segment": {"KEY_ACCOUNT": 0, "DOMESTIC": 1},
    "logistics_product": {
        "B2C": 0,
        "B2B": 1,
        "WAREHOUSE": 2,
        "CROSS_BORDER": 3,
        "COLD_CHAIN": 4,
        "REVERSE": 5,
        "M2C": 6,
        "SAME_DAY": 7,
    },
    "region": {
        "REGION_NORTH": 0,
        "REGION_EAST": 1,
        "REGION_SOUTH": 2,
        "REGION_WEST": 3,
    },
}
BRIDGE_DRIVER_LABELS = {
    "revenue_volume": "收入业务量",
    "revenue_mix": "收入结构",
    "revenue_price": "收入单价",
    "warehousing_cost": "仓储成本",
    "transportation_cost": "运输成本",
    "other_direct_cost": "其他直接成本",
    "operating_expense": "期间费用",
}
INVERSE_FINDING_TYPES = frozenset(
    {
        "fulfillment_cost_increase",
        "ar_cash_deterioration",
        "operating_profit_deterioration",
    }
)
UNAVAILABLE_MESSAGE = "当前口径未发布该比较值"


def _month(value: int) -> str:
    return f"{value // 100:04d}-{value % 100:02d}"


def _month_distance(later: datetime, month_key: int) -> int:
    return (later.year * 12 + later.month) - (
        (month_key // 100) * 12 + month_key % 100
    )


def _selected_dimensions(filters: ActiveFilters) -> tuple[DimensionName, ...]:
    selected: list[DimensionName] = []
    if filters.organization_id is not None:
        selected.append("organization")
    if filters.customer_segment_id is not None:
        selected.append("customer_segment")
    if filters.logistics_product_id is not None:
        selected.append("logistics_product")
    if filters.region_id is not None:
        selected.append("region")
    return tuple(selected)


def _matches_filters(item: PublishedMetricValue, filters: ActiveFilters) -> bool:
    value = item.value
    return (
        value.organization_id == filters.organization_id
        and value.customer_id is None
        and value.customer_segment_id == filters.customer_segment_id
        and value.logistics_product_id == filters.logistics_product_id
        and value.region_id == filters.region_id
    )


def _trend_value(values: dict[str, str], code: str) -> DashboardValue:
    value = values.get(code)
    if value is None:
        return unavailable_value(
            "trend_metric_not_published",
            "该月快照未发布趋势指标",
        )
    return available_value(value)


class DashboardService:
    def __init__(self, repository: DashboardSourceRepository | None = None) -> None:
        self.repository = repository or DashboardSourceRepository()

    def get_core(
        self,
        session: Session,
        *,
        filters: ActiveFilters,
        now: datetime | None = None,
    ) -> DashboardCoreProjection:
        bundle = self.repository.get_latest(session)
        generated_at = now or datetime.now(UTC)
        options = self._filter_options(bundle)
        self._validate_filters(filters, options)
        return DashboardCoreProjection(
            context=self._context(bundle, generated_at),
            filter_options=options,
            active_filters=filters,
            data_status=self._data_status(bundle, generated_at),
            metric_cards=self._metric_cards(bundle, filters),
        )

    def get_overview(
        self,
        session: Session,
        *,
        filters: ActiveFilters,
        now: datetime | None = None,
    ) -> DashboardOverview:
        bundle = self.repository.get_latest(session)
        generated_at = now or datetime.now(UTC)
        options = self._filter_options(bundle)
        self._validate_filters(filters, options)
        data_status = self._data_status(bundle, generated_at)
        trends = self.get_trends(session)
        bridge = self._profit_bridge(bundle)
        findings = self._finding_items(bundle)
        products = options.dimensions[2].options
        segments = options.dimensions[1].options
        product_table = self._product_table(bundle, products)
        margin_matrix = self._margin_matrix(bundle, segments, products)
        highlights = tuple(
            Highlight(
                finding_id=item.finding_id,
                title=item.title,
                impact_display=item.impact.display_value,
            )
            for item in findings[:3]
        )
        degradations: list[DashboardDegradation] = []
        if trends.status != "complete":
            degradations.append(
                DashboardDegradation(
                    panel="trends",
                    code=trends.status,
                    message=trends.degradation_message or "趋势序列不完整",
                )
            )
        if bridge.status != "complete":
            degradations.append(
                DashboardDegradation(
                    panel="profit_bridge",
                    code=bridge.status,
                    message=bridge.degradation_message or "经营利润桥不完整",
                )
            )
        if not findings:
            degradations.append(
                DashboardDegradation(
                    panel="findings",
                    code="findings_not_published",
                    message="经营发现尚未发布",
                )
            )
        if product_table.status != "complete":
            degradations.append(
                DashboardDegradation(
                    panel="product_table",
                    code=product_table.status,
                    message=product_table.degradation_message or "产品经营视图不完整",
                )
            )
        if margin_matrix.status != "complete":
            degradations.append(
                DashboardDegradation(
                    panel="margin_matrix",
                    code=margin_matrix.status,
                    message=margin_matrix.degradation_message or "毛利矩阵不完整",
                )
            )
        if data_status.freshness_status == "stale":
            state: Literal["ready", "empty", "error", "degraded", "stale"] = (
                "stale"
            )
        elif degradations or data_status.quality_status != "passed":
            state = "degraded"
        else:
            state = "ready"
        return DashboardOverview(
            state=state,
            context=self._context(bundle, generated_at),
            filter_options=options,
            active_filters=filters,
            data_status=data_status,
            metric_cards=self._metric_cards(bundle, filters),
            trends=trends,
            profit_bridge=bridge,
            findings=findings,
            product_table=product_table,
            margin_matrix=margin_matrix,
            highlights=highlights,
            degradations=tuple(degradations),
        )

    def get_trends(self, session: Session) -> TrendPanel:
        bundle = self.repository.get_latest(session)
        source_points = self.repository.get_snapshot_series(session, bundle)
        expected = tuple(
            self.repository._shift_month(bundle.as_of_period.month_key, offset)
            for offset in range(-11, 1)
        )
        available_months = {point.month_key for point in source_points}
        missing = tuple(
            _month(month_key)
            for month_key in expected
            if month_key not in available_months
        )
        required = {
            "revenue",
            "operating_profit",
            "gross_margin",
            "operating_cash_flow",
        }
        degraded = any(
            {metric.metric_code for metric in point.metrics} != required
            for point in source_points
        )
        points: list[TrendPoint] = []
        for point in source_points:
            values = {item.metric_code: item.exact_value for item in point.metrics}
            points.append(
                TrendPoint(
                    month=_month(point.month_key),
                    metric_snapshot_id=point.snapshot_id,
                    revenue=_trend_value(values, "revenue"),
                    operating_profit=_trend_value(values, "operating_profit"),
                    gross_margin=_trend_value(values, "gross_margin"),
                    operating_cash_flow=_trend_value(values, "operating_cash_flow"),
                )
            )
        if degraded:
            status: Literal["complete", "partial_series", "degraded"] = "degraded"
            message = "部分月度快照缺少趋势指标"
        elif missing:
            status = "partial_series"
            message = "部分月份尚未发布指标快照"
        else:
            status = "complete"
            message = None
        return TrendPanel(
            status=status,
            coverage_count=len(points),
            expected_count=12,
            missing_months=missing,
            points=tuple(points),
            degradation_message=message,
        )

    def get_analysis_projection(
        self, session: Session, *, filters: ActiveFilters
    ) -> DashboardAnalysisProjection:
        bundle = self.repository.get_latest(session)
        self._validate_filters(filters, self._filter_options(bundle))
        bridge = self._profit_bridge(bundle)
        findings = self._finding_items(bundle)
        highlights = tuple(
            Highlight(
                finding_id=item.finding_id,
                title=item.title,
                impact_display=item.impact.display_value,
            )
            for item in findings[:3]
        )
        return DashboardAnalysisProjection(
            profit_bridge=bridge,
            findings=findings,
            highlights=highlights,
        )

    def get_dimension_views(self, session: Session) -> DashboardDimensionViews:
        bundle = self.repository.get_latest(session)
        options = self._filter_options(bundle)
        products = options.dimensions[2].options
        segments = options.dimensions[1].options
        return DashboardDimensionViews(
            product_table=self._product_table(bundle, products),
            margin_matrix=self._margin_matrix(bundle, segments, products),
        )

    def _product_table(
        self,
        bundle: DashboardSourceBundle,
        products: tuple[DimensionOption, ...],
    ) -> ProductPerformance:
        filters_by_product = {
            product.id: ActiveFilters(
                period_view="month",
                logistics_product_id=product.id,
                is_total_scope=False,
            )
            for product in products
        }

        def has_all(comparison_types: dict[str, str]) -> bool:
            return all(
                self._find_value(
                    bundle,
                    metric_code,
                    comparison_type,
                    filters_by_product[product.id],
                )
                is not None
                for product in products
                for metric_code, comparison_type in comparison_types.items()
            )

        budget_types = {
            "revenue": "budget_variance_month_pct",
            "orders": "budget_variance_month_pct",
            "gross_margin": "budget_variance_month",
        }
        yoy_types = {
            "revenue": "yoy_variance_month_pct",
            "orders": "yoy_variance_month_pct",
            "gross_margin": "yoy_variance_month",
        }
        comparison_label: Literal["预算", "同比", "不可用"]
        if has_all(budget_types):
            comparison_label = "预算"
            comparison_types = budget_types
        elif has_all(yoy_types):
            comparison_label = "同比"
            comparison_types = yoy_types
        else:
            comparison_label = "不可用"
            comparison_types = yoy_types

        rows: list[ProductRow] = []
        for product in products:
            filters = filters_by_product[product.id]
            rows.append(
                ProductRow(
                    logistics_product_id=product.id,
                    code=product.code,
                    name=product.name,
                    revenue=self._project_value(
                        bundle, "revenue", "actual_month", filters, primary=True
                    ),
                    orders=self._project_value(
                        bundle, "orders", "actual_month", filters, primary=True
                    ),
                    gross_margin=self._project_value(
                        bundle,
                        "gross_margin",
                        "actual_month",
                        filters,
                        primary=True,
                    ),
                    fulfillment_cost_rate=self._project_value(
                        bundle,
                        "fulfillment_cost_rate",
                        "actual_month",
                        filters,
                        primary=True,
                    ),
                    revenue_comparison=self._project_value(
                        bundle,
                        "revenue",
                        comparison_types["revenue"],
                        filters,
                        comparison=True,
                    ),
                    orders_comparison=self._project_value(
                        bundle,
                        "orders",
                        comparison_types["orders"],
                        filters,
                        comparison=True,
                    ),
                    gross_margin_comparison=self._project_value(
                        bundle,
                        "gross_margin",
                        comparison_types["gross_margin"],
                        filters,
                        comparison=True,
                    ),
                )
            )
        rows.sort(
            key=lambda row: (
                row.revenue.exact_value is not None,
                row.revenue.exact_value or Decimal("0"),
                row.code,
            ),
            reverse=True,
        )
        complete = comparison_label != "不可用" and all(
            all(
                value.status == "available"
                for value in (
                    row.revenue,
                    row.orders,
                    row.gross_margin,
                    row.fulfillment_cost_rate,
                    row.revenue_comparison,
                    row.orders_comparison,
                    row.gross_margin_comparison,
                )
            )
            for row in rows
        )
        return ProductPerformance(
            status="complete" if complete else "degraded",
            comparison_label=comparison_label,
            rows=tuple(rows),
            degradation_message=None if complete else "部分产品指标或比较值未发布",
        )

    def _margin_matrix(
        self,
        bundle: DashboardSourceBundle,
        segments: tuple[DimensionOption, ...],
        products: tuple[DimensionOption, ...],
    ) -> MarginMatrix:
        filters_by_cell = {
            (segment.id, product.id): ActiveFilters(
                period_view="month",
                customer_segment_id=segment.id,
                logistics_product_id=product.id,
                is_total_scope=False,
            )
            for segment in segments
            for product in products
        }

        def comparison_available(comparison_type: str) -> bool:
            return all(
                self._find_value(bundle, "gross_margin", comparison_type, filters)
                is not None
                for filters in filters_by_cell.values()
            )

        comparison_label: Literal["预算", "同比", "不可用"]
        if comparison_available("budget_variance_month"):
            comparison_label = "预算"
            comparison_type = "budget_variance_month"
        elif comparison_available("yoy_variance_month"):
            comparison_label = "同比"
            comparison_type = "yoy_variance_month"
        else:
            comparison_label = "不可用"
            comparison_type = "yoy_variance_month"
        cells = tuple(
            MatrixCell(
                customer_segment_id=segment.id,
                logistics_product_id=product.id,
                actual_margin=self._project_value(
                    bundle,
                    "gross_margin",
                    "actual_month",
                    filters_by_cell[(segment.id, product.id)],
                    primary=True,
                ),
                comparison=self._project_value(
                    bundle,
                    "gross_margin",
                    comparison_type,
                    filters_by_cell[(segment.id, product.id)],
                    comparison=True,
                ),
            )
            for segment in segments
            for product in products
        )
        complete = comparison_label != "不可用" and all(
            cell.actual_margin.status == "available"
            and cell.comparison.status == "available"
            for cell in cells
        )
        return MarginMatrix(
            status="complete" if complete else "degraded",
            comparison_label=comparison_label,
            rows=segments,
            columns=products,
            cells=cells,
            degradation_message=None if complete else "部分矩阵指标或比较值未发布",
        )

    @staticmethod
    def _profit_bridge(bundle: DashboardSourceBundle) -> ProfitBridge:
        published = next(
            (
                item
                for item in bundle.analysis_results
                if item.playbook_code == "operating_profit_bridge"
            ),
            None,
        )
        if published is None:
            return ProfitBridge(
                status="degraded",
                comparison_basis="prior_year",
                impact=unavailable_value(
                    "analysis_result_not_published",
                    "经营利润桥尚未发布",
                ),
                reconciliation_status="not_applicable",
                reconciliation_difference=Decimal("0.0000"),
                drivers=(),
                degradation_message="经营利润桥尚未发布",
            )
        result = published.result
        drivers = tuple(
            BridgeDriver(
                driver_code=driver.driver_code,
                label=BRIDGE_DRIVER_LABELS.get(
                    driver.driver_code, driver.driver_code
                ),
                contribution=comparison_value(driver.contribution_amount),
            )
            for driver in published.drivers
        )
        if result.status == "not_applicable":
            reconciliation_status: Literal["passed", "failed", "not_applicable"] = (
                "not_applicable"
            )
        elif abs(result.reconciliation_difference) <= result.reconciliation_tolerance:
            reconciliation_status = "passed"
        else:
            reconciliation_status = "failed"
        return ProfitBridge(
            status=result.status,  # type: ignore[arg-type]
            comparison_basis=result.comparison_basis,  # type: ignore[arg-type]
            impact=comparison_value(result.impact_amount),
            reconciliation_status=reconciliation_status,
            reconciliation_difference=result.reconciliation_difference,
            drivers=drivers,
            degradation_message=result.degradation_message,
        )

    @staticmethod
    def _finding_items(bundle: DashboardSourceBundle) -> tuple[FindingItem, ...]:
        items: list[FindingItem] = []
        for published in bundle.findings:
            finding = published.finding
            if (
                finding.finding_type is None
                or finding.total_score is None
                or finding.comparison_basis not in {"prior_year", "budget"}
            ):
                continue
            verified = sum(
                evidence.status == "verified" for evidence in published.evidence
            )
            path = (
                f"/investigations/{finding.id}"
                f"?batch_id={bundle.batch.id}"
                f"&metric_snapshot_id={bundle.snapshot.id}"
                f"&analysis_run_id={bundle.run.id}"
            )
            items.append(
                FindingItem(
                    finding_id=finding.id,
                    finding_type=finding.finding_type,
                    title=finding.title,
                    impact=available_value(
                        finding.impact_amount,
                        direction=(
                            "negative"
                            if finding.finding_type in INVERSE_FINDING_TYPES
                            else "positive"
                        ),
                    ),
                    total_score=finding.total_score,
                    comparison_basis=finding.comparison_basis,  # type: ignore[arg-type]
                    evidence_verified=verified,
                    evidence_total=len(published.evidence),
                    scope="global",
                    investigation_path=path,
                )
            )
        return tuple(items)

    @staticmethod
    def _context(bundle: DashboardSourceBundle, now: datetime) -> DashboardContext:
        return DashboardContext(
            batch_id=bundle.batch.id,
            import_version_id=bundle.import_version.id,
            metric_snapshot_id=bundle.snapshot.id,
            analysis_run_id=bundle.run.id,
            as_of_month=_month(bundle.as_of_period.month_key),
            metric_definition_set_id=bundle.snapshot.definition_set_id,
            metric_definition_set_hash=bundle.snapshot.definition_set_hash,
            metric_engine_version=bundle.snapshot.engine_version,
            analysis_policy_id=bundle.run.policy_id,
            analysis_policy_hash=bundle.run.policy_set_hash,
            analysis_engine_version=bundle.run.engine_version,
            generated_at=now,
        )

    @staticmethod
    def _data_status(bundle: DashboardSourceBundle, now: datetime) -> DataStatus:
        quality = bundle.quality
        if quality.blocking_issue_count:
            quality_status: Literal["passed", "warning", "blocked"] = "blocked"
        elif quality.warning_issue_count:
            quality_status = "warning"
        else:
            quality_status = "passed"
        return DataStatus(
            batch_status=bundle.batch.status,  # type: ignore[arg-type]
            import_status=bundle.import_version.status,  # type: ignore[arg-type]
            quality_status=quality_status,
            blocking_issue_count=quality.blocking_issue_count,
            warning_issue_count=quality.warning_issue_count,
            acknowledged_warning_count=quality.acknowledged_warning_count,
            reconciliation_status=quality.reconciliation_status,
            metric_snapshot_status="published",
            analysis_run_status="published",
            freshness_status=(
                "fresh"
                if _month_distance(now, bundle.as_of_period.month_key) <= 1
                else "stale"
            ),
        )

    @staticmethod
    def _ordered_options(
        dimension: DimensionName, entities: tuple[object, ...]
    ) -> tuple[DimensionOption, ...]:
        options = tuple(
            DimensionOption(id=entity.id, code=entity.code, name=entity.name)  # type: ignore[attr-defined]
            for entity in entities
        )
        rank = DIMENSION_ORDER[dimension]
        return tuple(sorted(options, key=lambda item: (rank.get(item.code, 999), item.code)))

    def _filter_options(self, bundle: DashboardSourceBundle) -> FilterOptions:
        dimensions = bundle.dimension_options
        revenue_definition = next(
            item.definition
            for item in bundle.metric_values
            if item.definition.metric_code == "revenue"
        )
        persisted = {
            tuple(item)
            for item in revenue_definition.definition_config.get(
                "allowed_dimension_sets", []
            )
            if "customer" not in item
        }
        combinations = tuple(
            item for item in SUPPORTED_DIMENSION_COMBINATIONS if item in persisted
        )
        return FilterOptions(
            dimensions=(
                FilterDimension(
                    dimension="organization",
                    label="组织",
                    options=self._ordered_options(
                        "organization", dimensions.organizations
                    ),
                ),
                FilterDimension(
                    dimension="customer_segment",
                    label="客户群",
                    options=self._ordered_options(
                        "customer_segment", dimensions.customer_segments
                    ),
                ),
                FilterDimension(
                    dimension="logistics_product",
                    label="物流产品",
                    options=self._ordered_options(
                        "logistics_product", dimensions.logistics_products
                    ),
                ),
                FilterDimension(
                    dimension="region",
                    label="区域",
                    options=self._ordered_options("region", dimensions.regions),
                ),
            ),
            supported_combinations=combinations,
        )

    @staticmethod
    def _validate_filters(filters: ActiveFilters, options: FilterOptions) -> None:
        selected = _selected_dimensions(filters)
        if selected not in options.supported_combinations:
            raise DashboardFilterError(
                "unsupported_filter_combination",
                f"unsupported dashboard filter combination: {selected}",
            )
        chosen = {
            "organization": filters.organization_id,
            "customer_segment": filters.customer_segment_id,
            "logistics_product": filters.logistics_product_id,
            "region": filters.region_id,
        }
        for dimension in options.dimensions:
            selected_id = chosen[dimension.dimension]
            if selected_id is not None and selected_id not in {
                item.id for item in dimension.options
            }:
                raise DashboardFilterError(
                    "unknown_filter_value",
                    f"unknown {dimension.dimension} filter: {selected_id}",
                )

    @staticmethod
    def _find_value(
        bundle: DashboardSourceBundle,
        metric_code: str,
        comparison_type: str,
        filters: ActiveFilters,
    ) -> PublishedMetricValue | None:
        return next(
            (
                item
                for item in bundle.metric_values
                if item.definition.metric_code == metric_code
                and item.value.comparison_type == comparison_type
                and _matches_filters(item, filters)
            ),
            None,
        )

    @staticmethod
    def _unavailable(*, primary: bool = False) -> DashboardValue:
        code = "metric_grain_not_published" if primary else "comparison_not_published"
        return unavailable_value(code, UNAVAILABLE_MESSAGE)

    def _project_value(
        self,
        bundle: DashboardSourceBundle,
        metric_code: str,
        comparison_type: str,
        filters: ActiveFilters,
        *,
        comparison: bool = False,
        inverse: bool = False,
        primary: bool = False,
    ) -> DashboardValue:
        item = self._find_value(bundle, metric_code, comparison_type, filters)
        if item is None:
            return self._unavailable(primary=primary)
        if comparison:
            return comparison_value(item.value.exact_value, inverse=inverse)
        return available_value(item.value.exact_value)

    def _metric_cards(
        self, bundle: DashboardSourceBundle, filters: ActiveFilters
    ) -> tuple[MetricCard, ...]:
        primary_type = "actual_month" if filters.period_view == "month" else "actual_ytd"
        yoy_suffix = "month" if filters.period_view == "month" else "ytd"
        cards: list[MetricCard] = []
        for metric_code, title, category, unit, inverse in CARD_DEFINITIONS:
            ratio = metric_code in RATIO_METRICS
            budget_type = (
                "budget_variance_month"
                if ratio
                else "budget_variance_month_pct"
            )
            yoy_type = (
                f"yoy_variance_{yoy_suffix}"
                if ratio
                else f"yoy_variance_{yoy_suffix}_pct"
            )
            ytd_budget_type = (
                "budget_variance_ytd" if ratio else "budget_variance_ytd_pct"
            )
            companion_code = None
            if metric_code == "ar_balance":
                companion_code = "dso"
            elif metric_code == "operating_cash_flow":
                companion_code = "cash_conversion"
            cards.append(
                MetricCard(
                    metric_code=metric_code,  # type: ignore[arg-type]
                    title=title,
                    category=category,
                    unit=unit,  # type: ignore[arg-type]
                    primary=self._project_value(
                        bundle,
                        metric_code,
                        primary_type,
                        filters,
                        primary=True,
                    ),
                    budget=self._project_value(
                        bundle,
                        metric_code,
                        budget_type,
                        filters,
                        comparison=True,
                        inverse=inverse,
                    ),
                    yoy=self._project_value(
                        bundle,
                        metric_code,
                        yoy_type,
                        filters,
                        comparison=True,
                        inverse=inverse,
                    ),
                    ytd_budget=self._project_value(
                        bundle,
                        metric_code,
                        ytd_budget_type,
                        filters,
                        comparison=True,
                        inverse=inverse,
                    ),
                    companion=(
                        self._project_value(
                            bundle,
                            companion_code,
                            primary_type,
                            filters,
                        )
                        if companion_code is not None
                        else None
                    ),
                )
            )
        return tuple(cards)


__all__ = [
    "DashboardCoreProjection",
    "DashboardAnalysisProjection",
    "DashboardDimensionViews",
    "DashboardFilterError",
    "DashboardService",
]
