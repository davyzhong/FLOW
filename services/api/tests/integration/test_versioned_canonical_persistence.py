from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.parser import parse_workbook
from flow_api.data_contract.persistence import (
    load_canonical_package,
    read_canonical_package_by_version,
)
from flow_api.data_contract.semantic import compare_semantics
from flow_api.infrastructure.models.canonical import FactOperatingActual
from flow_api.infrastructure.models.intake import SourceFile

from .data_contract_support import (
    data_contract_session_fixture as _data_contract_session_fixture,  # noqa: F401
)
from .data_contract_support import make_source_file

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
STANDARD = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"


def setup_module() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_corrections_create_queryable_versions_without_overwriting_prior_facts(
    data_contract_session: Session,
) -> None:
    session = data_contract_session
    package = parse_workbook(STANDARD, CONTRACT)
    first_source = make_source_file(session)
    first = load_canonical_package(session, package, first_source)
    session.flush()
    second_source = SourceFile(
        batch_id=first_source.batch_id,
        stored_object_id=first_source.stored_object_id,
        original_filename="corrected.xlsx",
        workbook_metadata={"contract_version": "flow.excel.v1"},
    )
    session.add(second_source)
    session.flush()
    second = load_canonical_package(session, package, second_source)
    session.commit()

    first_package = read_canonical_package_by_version(session, first.id)
    second_package = read_canonical_package_by_version(session, second.id)
    assert first.sequence == 1
    assert second.sequence == 2
    assert compare_semantics(package, first_package) == ()
    assert compare_semantics(package, second_package) == ()
    assert (
        session.scalar(select(func.count()).select_from(FactOperatingActual))
        == len(package.operating_actuals) * 2
    )
    first_fact = session.scalar(
        select(FactOperatingActual)
        .where(FactOperatingActual.import_version_id == first.id)
        .limit(1)
    )
    second_fact = session.scalar(
        select(FactOperatingActual)
        .where(FactOperatingActual.import_version_id == second.id)
        .limit(1)
    )
    assert first_fact is not None and second_fact is not None
    assert first_fact.id != second_fact.id
    assert first_fact.business_record_id == second_fact.business_record_id
