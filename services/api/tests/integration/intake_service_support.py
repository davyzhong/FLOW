from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from flow_api.data_contract.contract import load_contract
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
    MappingVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
    SourceRecord,
    StoredObject,
    WarningAcknowledgement,
)
from flow_api.intake.detector import profile_workbook
from flow_api.intake.extractor import ExtractedCandidate, extract_candidate_package
from flow_api.intake.mapping import MappingProposal, load_aliases, propose_mapping
from flow_api.intake.quality import QualityReport, evaluate_quality
from flow_api.intake.source_storage import StoredSource
from flow_api.intake.transforms import load_transform_rules

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
ALIASES = load_aliases(REPOSITORY_ROOT / "config/intake/flow_v1_aliases.yaml")
TRANSFORMS = load_transform_rules(REPOSITORY_ROOT / "config/intake/flow_v1_transforms.yaml")
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"
STANDARD = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"

MODELS_IN_DELETE_ORDER = (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
    WarningAcknowledgement,
    ReconciliationResult,
    QualityIssue,
    SourceRecord,
    ImportVersion,
    MappingVersion,
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


def clean(session: Session) -> None:
    for model in MODELS_IN_DELETE_ORDER:
        session.execute(delete(model))
    session.commit()


@pytest.fixture(name="intake_session")
def intake_session_fixture() -> Session:
    with Session(get_engine(), expire_on_commit=False) as session:
        clean(session)
        yield session
        session.rollback()
        clean(session)


@lru_cache(maxsize=2)
def intake_inputs(
    path: Path = NONSTANDARD,
) -> tuple[StoredSource, MappingProposal, ExtractedCandidate, QualityReport]:
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    profile = profile_workbook(content)
    proposal = propose_mapping(profile, CONTRACT, ALIASES)
    candidate = extract_candidate_package(content, profile, proposal, CONTRACT, TRANSFORMS)
    report = evaluate_quality(candidate.package, CONTRACT, proposal)
    stored = StoredSource(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=len(content),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        original_filename=path.name,
    )
    return stored, proposal, candidate, report
