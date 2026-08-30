from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.parser import parse_workbook
from flow_api.data_contract.persistence import load_canonical_package, read_canonical_package
from flow_api.data_contract.semantic import compare_semantics
from flow_api.infrastructure.models.canonical import (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
)
from flow_api.infrastructure.models.intake import ImportVersion, SourceRecord

from .data_contract_support import (
    data_contract_session_fixture as _data_contract_session_fixture,  # noqa: F401
)
from .data_contract_support import make_source_file

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
STANDARD_WORKBOOK = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_package_loads_atomically_with_row_lineage(
    data_contract_session: Session,
) -> None:
    session = data_contract_session
    source_package = parse_workbook(STANDARD_WORKBOOK, CONTRACT)
    source_file = make_source_file(session)

    import_version = load_canonical_package(session, source_package, source_file)
    session.commit()
    loaded = read_canonical_package(session, source_package.batch.batch_code)

    assert compare_semantics(source_package, loaded) == ()
    assert import_version.summary["batch_code"] == source_package.batch.batch_code
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(SourceRecord.import_version_id == import_version.id)
        )
        == 5592
    )
    assert session.scalar(select(func.count()).select_from(FactOperatingActual)) == 3072
    assert session.scalar(select(func.count()).select_from(FactFinancialActual)) == 432
    assert session.scalar(select(func.count()).select_from(FactBudget)) == 120
    assert session.scalar(select(func.count()).select_from(FactArCollection)) == 1920


def test_invalid_package_does_not_leave_partial_rows(
    data_contract_session: Session,
) -> None:
    session = data_contract_session
    package = parse_workbook(STANDARD_WORKBOOK, CONTRACT)
    invalid_row = package.operating_actuals[0].model_copy(
        update={"customer_code": "MISSING_CUSTOMER"}
    )
    invalid_package = package.model_copy(
        update={"operating_actuals": (invalid_row,) + package.operating_actuals[1:]}
    )
    source_file = make_source_file(session)

    with pytest.raises(ValueError, match="MISSING_CUSTOMER"):
        load_canonical_package(session, invalid_package, source_file)
    session.rollback()

    assert session.scalar(select(func.count()).select_from(ImportVersion)) == 0
    assert session.scalar(select(func.count()).select_from(FactOperatingActual)) == 0
