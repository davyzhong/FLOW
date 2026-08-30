from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import delete
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

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
STANDARD_WORKBOOK = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"
MODELS_IN_DELETE_ORDER = (
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
)


def _clean(session: Session) -> None:
    for model in MODELS_IN_DELETE_ORDER:
        session.execute(delete(model))
    session.commit()


@pytest.fixture(name="data_contract_session")
def data_contract_session_fixture() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        _clean(database_session)
        yield database_session
        database_session.rollback()
        _clean(database_session)


def make_source_file(session: Session) -> SourceFile:
    content = STANDARD_WORKBOOK.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    batch = AnalysisBatch(name="FLOW reference persistence test")
    stored = StoredObject(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=len(content),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    source = SourceFile(
        batch=batch,
        stored_object=stored,
        original_filename=STANDARD_WORKBOOK.name,
        workbook_metadata={"contract_version": "flow.excel.v1"},
    )
    session.add(source)
    session.flush()
    return source
