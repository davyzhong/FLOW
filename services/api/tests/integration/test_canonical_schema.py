from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
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
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    SourceFile,
    SourceRecord,
    StoredObject,
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session
        database_session.rollback()
        for model in (
            FactArCollection,
            FactBudget,
            FactFinancialActual,
            FactOperatingActual,
            SourceRecord,
            ImportVersion,
            SourceFile,
            StoredObject,
            AnalysisBatch,
            ScenarioVersion,
            ManagementAccount,
            Region,
            LogisticsProduct,
            Customer,
            CustomerSegment,
            Organization,
            Period,
        ):
            database_session.execute(delete(model))
        database_session.commit()


def canonical_seed(session: Session) -> dict[str, object]:
    suffix = uuid4().hex[:8]
    period = Period(month_key=202608, year=2026, quarter=3, month=8)
    organization = Organization(code=f"ORG-{suffix}", name="Supply Chain BU", level="business_unit")
    segment = CustomerSegment(code=f"SEG-{suffix}", name="Strategic")
    customer = Customer(
        code=f"CUS-{suffix}",
        name="Key Account",
        segment=segment,
        credit_term_days=60,
    )
    product = LogisticsProduct(code=f"PROD-{suffix}", name="Contract logistics")
    region = Region(code=f"REG-{suffix}", name="East China")
    account = ManagementAccount(code=f"ACC-{suffix}", name="Revenue", category="revenue")
    scenario = ScenarioVersion(code=f"ACT-{suffix}", name="Actual", scenario_type="actual")
    batch = AnalysisBatch(name=f"Canonical seed {suffix}")
    digest = uuid4().hex * 2
    stored = StoredObject(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=10,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    source_file = SourceFile(
        batch=batch,
        stored_object=stored,
        original_filename="canonical.xlsx",
    )
    version = ImportVersion(batch=batch, sequence=1, is_published=True)
    source_record = SourceRecord(
        import_version=version,
        source_file=source_file,
        sheet_name="02_经营实际",
        source_row=2,
        source_column="K",
        canonical_field="revenue",
        raw_value={"value": "100.1234"},
        transformed_value={"value": "100.1234"},
    )
    session.add_all(
        [
            period,
            organization,
            segment,
            customer,
            product,
            region,
            account,
            scenario,
            source_record,
        ]
    )
    session.commit()
    return {
        "period": period,
        "organization": organization,
        "segment": segment,
        "customer": customer,
        "product": product,
        "region": region,
        "account": account,
        "scenario": scenario,
        "version": version,
        "source_record": source_record,
    }


def operating_fact(seed: dict[str, object], revenue: Decimal) -> FactOperatingActual:
    return FactOperatingActual(
        period=seed["period"],
        organization=seed["organization"],
        customer=seed["customer"],
        logistics_product=seed["product"],
        region=seed["region"],
        import_version=seed["version"],
        source_record=seed["source_record"],
        order_count=Decimal("10.0000"),
        shipment_count=Decimal("25.0000"),
        revenue=revenue,
        warehousing_cost=Decimal("20.0100"),
        transportation_cost=Decimal("30.0200"),
        other_direct_cost=Decimal("5.0000"),
    )


def test_operating_fact_grain_and_decimal_precision(session: Session) -> None:
    seed = canonical_seed(session)
    first = operating_fact(seed, Decimal("100.1234"))
    session.add(first)
    session.commit()
    session.refresh(first)
    assert first.revenue == Decimal("100.1234")

    session.add(operating_fact(seed, Decimal("200.0000")))
    with pytest.raises(IntegrityError):
        session.commit()


def test_financial_budget_and_ar_facts_preserve_their_grain(session: Session) -> None:
    seed = canonical_seed(session)
    financial = FactFinancialActual(
        period=seed["period"],
        organization=seed["organization"],
        management_account=seed["account"],
        import_version=seed["version"],
        source_record=seed["source_record"],
        amount=Decimal("987654321.1234"),
    )
    budget = FactBudget(
        period=seed["period"],
        organization=seed["organization"],
        customer_segment=seed["segment"],
        logistics_product=seed["product"],
        management_account=seed["account"],
        scenario_version=seed["scenario"],
        import_version=seed["version"],
        source_record=seed["source_record"],
        metric_code="revenue",
        amount=Decimal("1000.1000"),
    )
    ar = FactArCollection(
        period=seed["period"],
        customer=seed["customer"],
        invoice_number="INV-001",
        aging_bucket=None,
        import_version=seed["version"],
        source_record=seed["source_record"],
        receivable_balance=Decimal("500.0000"),
        due_amount=Decimal("400.0000"),
        overdue_amount=Decimal("100.0000"),
        collected_amount=Decimal("50.0000"),
    )
    session.add_all([financial, budget, ar])
    session.commit()

    assert financial.amount == Decimal("987654321.1234")
    assert budget.amount == Decimal("1000.1000")
    assert ar.overdue_amount == Decimal("100.0000")


def test_ar_requires_invoice_or_aging_bucket(session: Session) -> None:
    seed = canonical_seed(session)
    session.add(
        FactArCollection(
            period=seed["period"],
            customer=seed["customer"],
            import_version=seed["version"],
            source_record=seed["source_record"],
            receivable_balance=Decimal("1.0000"),
            due_amount=Decimal("1.0000"),
            overdue_amount=Decimal("0.0000"),
            collected_amount=Decimal("0.0000"),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_period_month_key_is_validated(session: Session) -> None:
    session.add(Period(month_key=202613, year=2026, quarter=5, month=13))
    with pytest.raises(IntegrityError):
        session.commit()
