from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.records import (
    ArCollectionRecord,
    BatchRecord,
    CanonicalPackage,
    CustomerRecord,
    CustomerSegmentRecord,
    FinancialActualRecord,
    LogisticsProductRecord,
    ManagementAccountRecord,
    MonthlyBudgetRecord,
    OperatingActualRecord,
    OrganizationRecord,
    PeriodRecord,
    RegionRecord,
    ScenarioVersionRecord,
)
from flow_api.data_contract.workbook import workbook_rows
from flow_api.infrastructure.models.canonical import (
    Customer,
    CustomerSegment,
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
    LogisticsProduct,
    ManagementAccount,
    Organization,
    Period,
    Region,
    ScenarioVersion,
)
from flow_api.infrastructure.models.intake import ImportVersion, SourceFile, SourceRecord

DATABASE_FIXTURE_NAMESPACE = UUID("23cb1107-9809-59cc-8c5c-690900ce9ef1")


def _stable_id(entity: str, business_key: str) -> UUID:
    return uuid5(DATABASE_FIXTURE_NAMESPACE, f"{entity}:{business_key}")


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, ".4f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(nested) for nested in value]
    return value


def _validate_package(package: CanonicalPackage) -> None:
    organization_codes = {row.code for row in package.organizations}
    customer_codes = {row.code for row in package.customers}
    segment_codes = {row.code for row in package.customer_segments}
    product_codes = {row.code for row in package.logistics_products}
    region_codes = {row.code for row in package.regions}
    account_codes = {row.code for row in package.management_accounts}
    scenario_codes = {row.code for row in package.scenario_versions}
    period_codes = {row.month_key for row in package.periods}
    checks: list[tuple[str, str, set[str]]] = []
    for operating_row in package.operating_actuals:
        checks.extend(
            (
                ("month_key", operating_row.month_key, period_codes),
                ("organization_code", operating_row.organization_code, organization_codes),
                ("customer_code", operating_row.customer_code, customer_codes),
                (
                    "logistics_product_code",
                    operating_row.logistics_product_code,
                    product_codes,
                ),
                ("region_code", operating_row.region_code, region_codes),
            )
        )
    for financial_row in package.financial_actuals:
        checks.extend(
            (
                ("month_key", financial_row.month_key, period_codes),
                ("organization_code", financial_row.organization_code, organization_codes),
                (
                    "management_account_code",
                    financial_row.management_account_code,
                    account_codes,
                ),
            )
        )
    for budget_row in package.monthly_budgets:
        checks.extend(
            (
                ("month_key", budget_row.month_key, period_codes),
                ("organization_code", budget_row.organization_code, organization_codes),
                ("scenario_code", budget_row.scenario_code, scenario_codes),
            )
        )
        if budget_row.customer_segment_code is not None:
            checks.append(
                ("customer_segment_code", budget_row.customer_segment_code, segment_codes)
            )
        if budget_row.logistics_product_code is not None:
            checks.append(
                ("logistics_product_code", budget_row.logistics_product_code, product_codes)
            )
        if budget_row.management_account_code is not None:
            checks.append(
                (
                    "management_account_code",
                    budget_row.management_account_code,
                    account_codes,
                )
            )
    for ar_row in package.ar_collections:
        checks.extend(
            (
                ("month_key", ar_row.month_key, period_codes),
                ("customer_code", ar_row.customer_code, customer_codes),
            )
        )
    for field_id, value, targets in checks:
        if value not in targets:
            raise ValueError(f"{field_id} references unknown business key {value}")

    grains: tuple[tuple[str, list[tuple[Any, ...]]], ...] = (
        (
            "operating_actual",
            [
                (
                    row.month_key,
                    row.organization_code,
                    row.customer_code,
                    row.logistics_product_code,
                    row.region_code,
                )
                for row in package.operating_actuals
            ],
        ),
        (
            "financial_actual",
            [
                (row.month_key, row.organization_code, row.management_account_code)
                for row in package.financial_actuals
            ],
        ),
        (
            "monthly_budget",
            [
                (
                    row.month_key,
                    row.organization_code,
                    row.customer_segment_code,
                    row.logistics_product_code,
                    row.management_account_code,
                    row.scenario_code,
                    row.metric_code,
                )
                for row in package.monthly_budgets
            ],
        ),
        (
            "ar_collection",
            [
                (row.month_key, row.customer_code, row.invoice_number, row.aging_bucket)
                for row in package.ar_collections
            ],
        ),
    )
    for name, values in grains:
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate canonical grain in {name}")


def _manifest(package: CanonicalPackage) -> dict[str, Any]:
    return {
        "periods": [row.month_key for row in package.periods],
        "organizations": [row.code for row in package.organizations],
        "customer_segments": [row.code for row in package.customer_segments],
        "customers": [row.code for row in package.customers],
        "logistics_products": [row.code for row in package.logistics_products],
        "regions": [row.code for row in package.regions],
        "management_accounts": [row.code for row in package.management_accounts],
        "scenario_versions": [row.code for row in package.scenario_versions],
    }


def _lineage_records(
    package: CanonicalPackage, version: ImportVersion, source_file: SourceFile
) -> tuple[list[SourceRecord], dict[tuple[str, str], SourceRecord]]:
    records: list[SourceRecord] = []
    fact_sources: dict[tuple[str, str], SourceRecord] = {}
    for sheet_id, rows in workbook_rows(package).items():
        sheet_name = {
            "instructions": "00_填写说明",
            "analysis_batch": "01_分析批次",
            "operating_actual": "02_经营实际",
            "financial_actual": "03_财务实际",
            "monthly_budget": "04_月度预算",
            "ar_collection": "05_应收回款",
            "customer_master": "06_客户主数据",
            "logistics_product": "07_物流产品",
            "organization_region": "08_组织与区域",
            "management_account": "09_管理科目",
        }[sheet_id]
        for row_number, row in enumerate(rows, start=4):
            normalized = _json_value(dict(row))
            source_record = SourceRecord(
                import_version=version,
                source_file=source_file,
                sheet_name=sheet_name,
                source_row=row_number,
                source_column="*",
                canonical_field="__row__",
                raw_value=normalized,
                transformed_value=normalized,
            )
            records.append(source_record)
            record_id = row.get("record_id")
            if isinstance(record_id, str):
                fact_sources[(sheet_id, record_id)] = source_record
    return records, fact_sources


def load_canonical_package(
    session: Session, package: CanonicalPackage, source_file: SourceFile
) -> ImportVersion:
    _validate_package(package)
    if source_file.batch_id is None:
        session.flush()
    next_sequence = (
        session.scalar(
            select(func.coalesce(func.max(ImportVersion.sequence), 0)).where(
                ImportVersion.batch_id == source_file.batch_id
            )
        )
        or 0
    ) + 1
    version = ImportVersion(
        batch_id=source_file.batch_id,
        sequence=next_sequence,
        is_published=False,
        summary={
            "batch_code": package.batch.batch_code,
            "contract_version": package.batch.contract_version,
            "batch": _json_value(package.batch.model_dump()),
            "manifest": _manifest(package),
        },
    )
    session.add(version)
    session.flush()
    lineage, fact_sources = _lineage_records(package, version, source_file)
    session.add_all(lineage)

    period_by_code = {
        row.month_key: Period(
            id=_stable_id("period", row.month_key),
            month_key=int(row.month_key.replace("-", "")),
            year=row.year,
            quarter=row.quarter,
            month=row.month,
        )
        for row in package.periods
    }
    organization_by_code = {
        row.code: Organization(
            id=_stable_id("organization", row.code),
            code=row.code,
            name=row.name,
            level=row.level,
        )
        for row in package.organizations
    }
    for organization_row in package.organizations:
        if organization_row.parent_code is not None:
            organization_by_code[organization_row.code].parent_id = organization_by_code[
                organization_row.parent_code
            ].id
    segment_by_code = {
        row.code: CustomerSegment(
            id=_stable_id("customer_segment", row.code), code=row.code, name=row.name
        )
        for row in package.customer_segments
    }
    customer_by_code = {
        row.code: Customer(
            id=_stable_id("customer", row.code),
            code=row.code,
            name=row.name,
            industry=row.industry,
            tier=row.tier,
            credit_term_days=row.credit_term_days,
            segment_id=segment_by_code[row.segment_code].id,
        )
        for row in package.customers
    }
    product_by_code = {
        row.code: LogisticsProduct(
            id=_stable_id("logistics_product", row.code),
            code=row.code,
            name=row.name,
            level=row.level,
        )
        for row in package.logistics_products
    }
    for product_row in package.logistics_products:
        if product_row.parent_code is not None:
            product_by_code[product_row.code].parent_id = product_by_code[
                product_row.parent_code
            ].id
    region_by_code = {
        row.code: Region(
            id=_stable_id("region", row.code),
            code=row.code,
            name=row.name,
            province=row.province,
            city=row.city,
        )
        for row in package.regions
    }
    for region_row in package.regions:
        if region_row.parent_code is not None:
            region_by_code[region_row.code].parent_id = region_by_code[region_row.parent_code].id
    account_by_code = {
        row.code: ManagementAccount(
            id=_stable_id("management_account", row.code),
            code=row.code,
            name=row.name,
            category=row.category,
            financial_account_code=row.financial_account_code,
        )
        for row in package.management_accounts
    }
    for account_row in package.management_accounts:
        if account_row.parent_code is not None:
            account_by_code[account_row.code].parent_id = account_by_code[
                account_row.parent_code
            ].id
    scenario_by_code = {
        row.code: ScenarioVersion(
            id=_stable_id("scenario_version", row.code),
            code=row.code,
            name=row.name,
            scenario_type=row.scenario_type,
            version_label=row.version_label,
        )
        for row in package.scenario_versions
    }
    session.add_all(
        [
            *period_by_code.values(),
            *organization_by_code.values(),
            *segment_by_code.values(),
            *customer_by_code.values(),
            *product_by_code.values(),
            *region_by_code.values(),
            *account_by_code.values(),
            *scenario_by_code.values(),
        ]
    )
    session.flush()

    operating_facts = [
        FactOperatingActual(
            id=UUID(row.record_id),
            import_version_id=version.id,
            source_record_id=fact_sources[("operating_actual", row.record_id)].id,
            period_id=period_by_code[row.month_key].id,
            organization_id=organization_by_code[row.organization_code].id,
            customer_id=customer_by_code[row.customer_code].id,
            logistics_product_id=product_by_code[row.logistics_product_code].id,
            region_id=region_by_code[row.region_code].id,
            order_count=row.order_count,
            shipment_count=row.shipment_count,
            revenue=row.revenue,
            warehousing_cost=row.warehousing_cost,
            transportation_cost=row.transportation_cost,
            other_direct_cost=row.other_direct_cost,
        )
        for row in package.operating_actuals
    ]
    financial_facts = [
        FactFinancialActual(
            id=UUID(row.record_id),
            import_version_id=version.id,
            source_record_id=fact_sources[("financial_actual", row.record_id)].id,
            period_id=period_by_code[row.month_key].id,
            organization_id=organization_by_code[row.organization_code].id,
            management_account_id=account_by_code[row.management_account_code].id,
            amount=row.amount,
        )
        for row in package.financial_actuals
    ]
    budget_facts = [
        FactBudget(
            id=UUID(row.record_id),
            import_version_id=version.id,
            source_record_id=fact_sources[("monthly_budget", row.record_id)].id,
            period_id=period_by_code[row.month_key].id,
            organization_id=organization_by_code[row.organization_code].id,
            customer_segment_id=(
                segment_by_code[row.customer_segment_code].id
                if row.customer_segment_code is not None
                else None
            ),
            logistics_product_id=(
                product_by_code[row.logistics_product_code].id
                if row.logistics_product_code is not None
                else None
            ),
            management_account_id=(
                account_by_code[row.management_account_code].id
                if row.management_account_code is not None
                else None
            ),
            scenario_version_id=scenario_by_code[row.scenario_code].id,
            metric_code=row.metric_code,
            amount=row.amount,
        )
        for row in package.monthly_budgets
    ]
    ar_facts = [
        FactArCollection(
            id=UUID(row.record_id),
            import_version_id=version.id,
            source_record_id=fact_sources[("ar_collection", row.record_id)].id,
            period_id=period_by_code[row.month_key].id,
            customer_id=customer_by_code[row.customer_code].id,
            invoice_number=row.invoice_number,
            aging_bucket=row.aging_bucket,
            receivable_balance=row.receivable_balance,
            due_amount=row.due_amount,
            overdue_amount=row.overdue_amount,
            collected_amount=row.collected_amount,
        )
        for row in package.ar_collections
    ]
    session.add_all([*operating_facts, *financial_facts, *budget_facts, *ar_facts])
    session.flush()
    return version


def _select_by_codes(session: Session, model: Any, codes: list[str]) -> list[Any]:
    return list(session.scalars(select(model).where(model.code.in_(codes)).order_by(model.code)))


def read_canonical_package(session: Session, batch_code: str) -> CanonicalPackage:
    version = session.scalar(
        select(ImportVersion)
        .where(ImportVersion.summary["batch_code"].astext == batch_code)
        .order_by(ImportVersion.sequence.desc())
        .limit(1)
    )
    if version is None:
        raise LookupError(f"canonical package not found: {batch_code}")
    summary = version.summary
    manifest = summary["manifest"]
    batch = BatchRecord.model_validate(summary["batch"])

    periods_db = list(
        session.scalars(
            select(Period)
            .where(Period.month_key.in_(int(code.replace("-", "")) for code in manifest["periods"]))
            .order_by(Period.month_key)
        )
    )
    organizations_db = _select_by_codes(session, Organization, manifest["organizations"])
    segments_db = _select_by_codes(session, CustomerSegment, manifest["customer_segments"])
    customers_db = _select_by_codes(session, Customer, manifest["customers"])
    products_db = _select_by_codes(session, LogisticsProduct, manifest["logistics_products"])
    regions_db = _select_by_codes(session, Region, manifest["regions"])
    accounts_db = _select_by_codes(session, ManagementAccount, manifest["management_accounts"])
    scenarios_db = _select_by_codes(session, ScenarioVersion, manifest["scenario_versions"])
    organization_code_by_id = {row.id: row.code for row in organizations_db}
    segment_code_by_id = {row.id: row.code for row in segments_db}
    product_code_by_id = {row.id: row.code for row in products_db}
    region_code_by_id = {row.id: row.code for row in regions_db}
    account_code_by_id = {row.id: row.code for row in accounts_db}
    scenario_code_by_id = {row.id: row.code for row in scenarios_db}
    customer_code_by_id = {row.id: row.code for row in customers_db}
    month_code_by_id = {row.id: f"{row.year:04d}-{row.month:02d}" for row in periods_db}

    periods = tuple(
        PeriodRecord(
            month_key=month_code_by_id[row.id],
            year=row.year,
            quarter=row.quarter,
            month=row.month,
            window=(
                "comparison"
                if batch.comparison_start_month
                <= month_code_by_id[row.id]
                <= batch.comparison_end_month
                else "analysis"
            ),
        )
        for row in periods_db
    )
    organizations = tuple(
        OrganizationRecord(
            code=row.code,
            name=row.name,
            level=row.level,
            parent_code=(
                organization_code_by_id[row.parent_id] if row.parent_id is not None else None
            ),
        )
        for row in organizations_db
    )
    segments = tuple(CustomerSegmentRecord(code=row.code, name=row.name) for row in segments_db)
    customers = tuple(
        CustomerRecord(
            code=row.code,
            name=row.name,
            industry=row.industry,
            tier=row.tier,
            credit_term_days=row.credit_term_days,
            segment_code=segment_code_by_id[row.segment_id],
        )
        for row in customers_db
    )
    products = tuple(
        LogisticsProductRecord(
            code=row.code,
            name=row.name,
            level=row.level or "service",
            parent_code=(product_code_by_id[row.parent_id] if row.parent_id is not None else None),
        )
        for row in products_db
    )
    regions = tuple(
        RegionRecord(
            code=row.code,
            name=row.name,
            province=row.province,
            city=row.city,
            parent_code=(region_code_by_id[row.parent_id] if row.parent_id is not None else None),
        )
        for row in regions_db
    )
    accounts = tuple(
        ManagementAccountRecord(
            code=row.code,
            name=row.name,
            category=row.category,
            financial_account_code=row.financial_account_code,
            parent_code=(account_code_by_id[row.parent_id] if row.parent_id is not None else None),
        )
        for row in accounts_db
    )
    scenarios = tuple(
        ScenarioVersionRecord(
            code=row.code,
            name=row.name,
            scenario_type=row.scenario_type,
            version_label=row.version_label,
        )
        for row in scenarios_db
    )
    operating_db = list(
        session.scalars(
            select(FactOperatingActual).where(FactOperatingActual.import_version_id == version.id)
        )
    )
    financial_db = list(
        session.scalars(
            select(FactFinancialActual).where(FactFinancialActual.import_version_id == version.id)
        )
    )
    budgets_db = list(
        session.scalars(select(FactBudget).where(FactBudget.import_version_id == version.id))
    )
    ar_db = list(
        session.scalars(
            select(FactArCollection).where(FactArCollection.import_version_id == version.id)
        )
    )
    operating = tuple(
        OperatingActualRecord(
            record_id=str(row.id),
            month_key=month_code_by_id[row.period_id],
            organization_code=organization_code_by_id[row.organization_id],
            customer_code=customer_code_by_id[row.customer_id],
            logistics_product_code=product_code_by_id[row.logistics_product_id],
            region_code=region_code_by_id[row.region_id],
            order_count=row.order_count,
            shipment_count=row.shipment_count,
            revenue=row.revenue,
            warehousing_cost=row.warehousing_cost,
            transportation_cost=row.transportation_cost,
            other_direct_cost=row.other_direct_cost,
        )
        for row in operating_db
    )
    financial = tuple(
        FinancialActualRecord(
            record_id=str(row.id),
            month_key=month_code_by_id[row.period_id],
            organization_code=organization_code_by_id[row.organization_id],
            management_account_code=account_code_by_id[row.management_account_id],
            amount=row.amount,
        )
        for row in financial_db
    )
    budgets = tuple(
        MonthlyBudgetRecord(
            record_id=str(row.id),
            month_key=month_code_by_id[row.period_id],
            organization_code=organization_code_by_id[row.organization_id],
            customer_segment_code=(
                segment_code_by_id[row.customer_segment_id]
                if row.customer_segment_id is not None
                else None
            ),
            logistics_product_code=(
                product_code_by_id[row.logistics_product_id]
                if row.logistics_product_id is not None
                else None
            ),
            management_account_code=(
                account_code_by_id[row.management_account_id]
                if row.management_account_id is not None
                else None
            ),
            scenario_code=scenario_code_by_id[row.scenario_version_id],
            metric_code=row.metric_code,
            amount=row.amount,
        )
        for row in budgets_db
    )
    ar_rows = tuple(
        ArCollectionRecord(
            record_id=str(row.id),
            month_key=month_code_by_id[row.period_id],
            customer_code=customer_code_by_id[row.customer_id],
            invoice_number=row.invoice_number,
            aging_bucket=row.aging_bucket,
            receivable_balance=row.receivable_balance,
            due_amount=row.due_amount,
            overdue_amount=row.overdue_amount,
            collected_amount=row.collected_amount,
        )
        for row in ar_db
    )
    return CanonicalPackage(
        batch=batch,
        periods=periods,
        organizations=organizations,
        customer_segments=segments,
        customers=customers,
        logistics_products=products,
        regions=regions,
        management_accounts=accounts,
        scenario_versions=scenarios,
        operating_actuals=operating,
        financial_actuals=financial,
        monthly_budgets=budgets,
        ar_collections=ar_rows,
    )
