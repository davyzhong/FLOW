from __future__ import annotations

import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.persistence import read_canonical_package_by_version
from flow_api.data_contract.semantic import compare_semantics
from flow_api.fixtures.known_answers import calculate_known_answers
from flow_api.infrastructure.models.canonical import (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
)
from flow_api.infrastructure.models.intake import (
    ImportVersion,
    MappingVersion,
    QualityIssue,
    SourceRecord,
)
from flow_api.intake.service import IntakeService

from .intake_service_support import (
    STANDARD,
    intake_inputs,
)
from .intake_service_support import (
    intake_session_fixture as _intake_session_fixture,  # noqa: F401
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
KNOWN_ANSWERS = json.loads(
    (REPOSITORY_ROOT / "fixtures/expected/known_answers.json").read_text(encoding="utf-8")
)


def setup_module() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def _acknowledge_warnings(service: IntakeService, session: Session, version: ImportVersion) -> None:
    warnings = session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == version.id,
            QualityIssue.severity == "warning",
        )
    )
    for issue in warnings:
        service.acknowledge_warning(
            issue.id,
            actor="phase-3-acceptance",
            reason="已按验收基线确认非阻断业务预警",
        )


def test_standard_and_external_workbooks_publish_identical_auditable_versions(
    intake_session: Session,
) -> None:
    service = IntakeService(intake_session)
    batch = service.create_batch("FLOW Phase 3 end-to-end acceptance")

    external_stored, external_proposal, external_candidate, external_report = intake_inputs()
    external_source = service.attach_source(batch.id, external_stored)
    external_mapping = service.propose_mapping(
        external_source.id, external_proposal, actor="phase-3-acceptance"
    )
    service.confirm_mapping(external_mapping.id, actor="phase-3-acceptance")
    external_version = service.validate_import(
        external_source.id,
        external_mapping.id,
        external_candidate,
        external_report,
    )
    _acknowledge_warnings(service, intake_session, external_version)
    service.publish_import(external_version.id)

    standard_stored, standard_proposal, standard_candidate, standard_report = intake_inputs(
        STANDARD
    )
    standard_source = service.attach_source(batch.id, standard_stored)
    standard_mapping = service.propose_mapping(
        standard_source.id, standard_proposal, actor="phase-3-acceptance"
    )
    standard_version = service.create_correction(
        standard_source.id,
        standard_mapping.id,
        standard_candidate,
        standard_report,
    )
    _acknowledge_warnings(service, intake_session, standard_version)

    def fail_mid_publication() -> None:
        raise RuntimeError("phase-3 atomicity injection")

    try:
        service.publish_import(standard_version.id, failure_hook=fail_mid_publication)
    except RuntimeError:
        pass
    else:
        raise AssertionError("publication failure injection did not execute")
    intake_session.expire_all()
    assert external_version.is_published
    assert not standard_version.is_published
    assert standard_version.status == "ready"

    service.publish_import(standard_version.id)
    intake_session.commit()

    external_readback = read_canonical_package_by_version(intake_session, external_version.id)
    standard_readback = read_canonical_package_by_version(intake_session, standard_version.id)
    assert compare_semantics(external_candidate.package, external_readback) == ()
    assert compare_semantics(standard_candidate.package, standard_readback) == ()
    assert compare_semantics(external_readback, standard_readback) == ()
    assert calculate_known_answers(external_readback) == KNOWN_ANSWERS
    assert calculate_known_answers(standard_readback) == KNOWN_ANSWERS

    assert external_source.stored_object.sha256 == external_candidate.source_sha256
    assert standard_source.stored_object.sha256 == standard_candidate.source_sha256
    assert external_source.stored_object.sha256 != standard_source.stored_object.sha256
    assert [external_mapping.sequence, standard_mapping.sequence] == [1, 2]
    assert intake_session.scalar(select(func.count()).select_from(MappingVersion)) == 2
    assert external_version.sequence == 1 and standard_version.sequence == 2
    assert not external_version.is_published and standard_version.is_published

    external_lineage_count = intake_session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(SourceRecord.import_version_id == external_version.id)
    )
    assert external_lineage_count == len(external_candidate.lineage)
    transformed_decimal = intake_session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.import_version_id == external_version.id,
            SourceRecord.transform_rule_id == "parse_decimal",
            SourceRecord.raw_value["value"].astext.like("%,%"),
        )
        .limit(1)
    )
    assert transformed_decimal is not None
    assert "," in transformed_decimal.raw_value["value"]
    assert "," not in str(transformed_decimal.transformed_value["value"])
    assert transformed_decimal.transform_rule_version == 1
    assert transformed_decimal.source_row >= 4
    assert transformed_decimal.source_column

    expected_counts = KNOWN_ANSWERS["row_counts"]
    fact_expectations = (
        (FactOperatingActual, expected_counts["operating_actuals"]),
        (FactFinancialActual, expected_counts["financial_actuals"]),
        (FactBudget, expected_counts["monthly_budgets"]),
        (FactArCollection, expected_counts["ar_collections"]),
    )
    for model, expected in fact_expectations:
        assert (
            intake_session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.import_version_id == standard_version.id)
            )
            == expected
        )
