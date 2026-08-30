from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.parser import parse_workbook
from flow_api.data_contract.persistence import load_canonical_package, read_canonical_package
from flow_api.data_contract.semantic import compare_semantics
from flow_api.data_contract.workbook import render_workbook

from .data_contract_support import (
    data_contract_session_fixture as _data_contract_session_fixture,  # noqa: F401
)
from .data_contract_support import make_source_file

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
STANDARD_WORKBOOK = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"


def test_excel_database_excel_has_zero_semantic_loss(
    data_contract_session: Session, tmp_path: Path
) -> None:
    session = data_contract_session
    source_package = parse_workbook(STANDARD_WORKBOOK, CONTRACT)
    source_file = make_source_file(session)
    load_canonical_package(session, source_package, source_file)
    session.commit()

    database_package = read_canonical_package(session, source_package.batch.batch_code)
    exported_workbook = tmp_path / "database-export.xlsx"
    render_workbook(CONTRACT, database_package, exported_workbook)
    exported_package = parse_workbook(exported_workbook, CONTRACT)

    assert compare_semantics(source_package, database_package) == ()
    assert compare_semantics(source_package, exported_package) == ()
