from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Column, MetaData, Table, func, insert, select, text
from sqlalchemy.orm import Session

from flow_api.cockpit.modules import build_balance_sheet_module, load_fact_context
from flow_api.enterprise.directory import sync_enterprise_directory
from flow_api.enterprise.models import AnalysisCycle, Enterprise
from flow_api.fixtures.damai.loader import (
    _damai_analysis_cycle_id,
    _upsert_enterprise,
    seed_damai_demo,
)
from flow_api.fixtures.damai.reset import reset_damai_business_data
from flow_api.infrastructure.db import build_engine
from flow_api.infrastructure.local_backup import create_local_backup, restore_local_backup
from flow_api.infrastructure.local_object_store import LocalObjectStore
from flow_api.infrastructure.models import Base
from flow_api.infrastructure.models.analytics import MetricSnapshot, ReviewEvent
from flow_api.infrastructure.models.canonical import FactFinancialActual, Period
from flow_api.infrastructure.models.cockpit import ActionItem
from flow_api.infrastructure.models.enterprise_directory import EnterpriseMember
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    StoredObject,
)
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.intake.service import IntakeService
from flow_api.publishing.objective_freeze import (
    ObjectiveReportSnapshot,
    freeze_objective_statement_report,
)
from flow_api.security.models import AuditEvent
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report
from flow_api.statements.projection import SnapshotIdentity, build_topic_projection


def test_model_registry_contains_tables_used_by_current_migrations() -> None:
    assert len(Base.metadata.tables) == 61
    assert "copilot_interaction" in Base.metadata.tables
    assert "objective_report_snapshot" in Base.metadata.tables


def test_model_registry_can_create_schema_on_sqlite() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        tables = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).scalars()

    assert len(set(tables)) == len(Base.metadata.tables)


def test_sqlite_alembic_initialization_and_repeat_upgrade(tmp_path) -> None:
    database_path = tmp_path / "flow.sqlite3"
    config = Config(Path(__file__).resolve().parents[2] / "alembic-sqlite.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = build_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        version = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
        table_count = connection.exec_driver_sql(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table'"
        ).scalar_one()
    assert version == "sqlite0004"
    assert table_count == len(Base.metadata.tables) + 1


def test_sqlite_engine_enforces_foreign_keys() -> None:
    engine = build_engine("sqlite://")

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_settings_default_to_local_sqlite_paths(tmp_path) -> None:
    from flow_api.settings import Settings

    settings = Settings(_env_file=None, flow_data_dir=tmp_path, database_url="")

    assert settings.database_url == f"sqlite:///{tmp_path.resolve() / 'flow.sqlite3'}"
    assert settings.object_directory == tmp_path.resolve() / "objects"
    assert not hasattr(settings, "redis_url")
    assert not hasattr(settings, "s3_bucket")


def test_sqlite_intake_service_creates_bootstrap_enterprise_and_cycle() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        batch = IntakeService(session).create_batch("SQLite bootstrap")
        cycle = session.get(AnalysisCycle, batch.analysis_cycle_id)

        assert cycle is not None
        assert cycle.period_key == "2026-09"
        enterprise = session.get(Enterprise, cycle.enterprise_id)
        assert enterprise is not None
        assert enterprise.code == "flow-bootstrap"


def test_sqlite_damai_enterprise_and_analysis_cycle_upserts_are_idempotent() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first_enterprise = _upsert_enterprise(session)
        first_cycle_id = _damai_analysis_cycle_id(session)
        session.flush()

        second_enterprise = _upsert_enterprise(session)
        second_cycle_id = _damai_analysis_cycle_id(session)
        cycle = session.get(AnalysisCycle, first_cycle_id)

        assert first_enterprise == second_enterprise
        assert first_cycle_id == second_cycle_id
        assert cycle is not None
        assert cycle.period_key == "2023-03"


def test_sqlite_organization_package_sync_is_idempotent() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)
    enterprise_id = uuid4()
    package = (
        Path(__file__).resolve().parents[4] / "data/enterprise/damai-logistics/v2/organization"
    )

    with Session(engine) as session:
        session.add(
            Enterprise(
                id=enterprise_id,
                code="damai-logistics",
                name="大麦物流测试企业",
            )
        )
        session.flush()
        first = sync_enterprise_directory(session, enterprise_id, package)
        second = sync_enterprise_directory(session, enterprise_id, package)
        session.flush()

        assert first == second == {"org_units": 8, "positions": 8, "members": 8}


def test_sqlite_damai_business_reset_preserves_organization_and_archives_reviews() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        seed_damai_demo(session)
        session.commit()
        enterprise = session.scalar(
            select(Enterprise).where(Enterprise.code == "damai-logistics")
        )
        assert enterprise is not None
        member_count = session.scalar(
            select(func.count())
            .select_from(EnterpriseMember)
            .where(EnterpriseMember.enterprise_id == enterprise.id)
        )
        review_count = session.scalar(select(func.count()).select_from(ReviewEvent))
        assert member_count and member_count > 0
        assert review_count and review_count > 0

        receipt = reset_damai_business_data(session, enterprise.id)
        assert receipt["batches_deleted"] == 1
        assert receipt["review_events_archived"] == review_count
        assert session.scalar(select(func.count()).select_from(ActionItem)) == 0
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.event_type == "finding.review_history.archived")
            )
            == review_count
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(EnterpriseMember)
                .where(EnterpriseMember.enterprise_id == enterprise.id)
            )
            == member_count
        )
        session.commit()

        seed_damai_demo(session)
        session.commit()
        assert session.scalar(
            select(func.count())
            .select_from(AnalysisBatch)
            .where(AnalysisBatch.name == "damai-demo-v1")
        ) == 1
        assert session.scalar(select(func.count()).select_from(ActionItem)) > 0


def test_sqlite_transaction_rollback_discards_uncommitted_rows() -> None:
    engine = build_engine("sqlite://")
    with engine.connect() as connection:
        connection.execute(text("CREATE TABLE rollback_probe (value TEXT NOT NULL)"))
        connection.commit()
        transaction = connection.begin()
        connection.execute(text("INSERT INTO rollback_probe VALUES ('temporary')"))
        transaction.rollback()
        count = connection.execute(text("SELECT count(*) FROM rollback_probe")).scalar_one()

    assert count == 0


def test_sqlite_preserves_partial_unique_index_for_published_versions() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        index_sql = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'index' "
            "AND name = 'uq_import_version_one_published_per_batch'"
        ).scalar_one()

    assert "WHERE is_published" in index_sql


def test_financial_amount_round_trips_without_precision_loss() -> None:
    engine = build_engine("sqlite://")
    metadata = MetaData()
    amount_table = Table(
        "amount_probe",
        metadata,
        Column("amount", FactFinancialActual.__table__.c.amount.type, primary_key=True),
    )
    metadata.create_all(engine)
    expected = [Decimal("123456789012345.6789"), Decimal("0.0001")]

    with engine.begin() as connection:
        connection.execute(insert(amount_table), [{"amount": value} for value in expected])
        actual = connection.execute(select(amount_table.c.amount).order_by(amount_table.c.amount))
        total = connection.execute(select(func.sum(amount_table.c.amount))).scalar_one()

    assert actual.scalars().all() == sorted(expected)
    assert total == sum(expected, Decimal("0"))


def test_statement_import_normalize_and_freeze_work_on_sqlite(tmp_path) -> None:
    database_path = tmp_path / "flow.sqlite3"
    object_root = tmp_path / "objects"
    engine = build_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    fixture_root = Path(__file__).resolve().parents[4] / "fixtures/damai/statements"
    reports: dict[str, StatementReport] = {}
    stored_objects: dict[str, StoredObject] = {}

    with Session(engine, expire_on_commit=False) as session:
        for period in ("FY2022", "FY2023"):
            fixture = fixture_root / f"damai_{period.lower()}.yaml"
            source_bytes = fixture.read_bytes()
            stored_object = LocalObjectStore(object_root).put_immutable(source_bytes, fixture.name)
            stored_objects[period] = stored_object
            session.add(stored_object)
            payload = yaml.safe_load(source_bytes)
            report = import_statement_report(
                session,
                company_name="大麦物流",
                stock_code="DAMAI.SYN",
                report_kind="年报",
                period_label=period,
                payload=payload,
                source_ref=str(fixture),
                source_sha256=stored_object.sha256,
            )
            session.flush()
            normalize_report(session, report)
            report.status = "published"
            reports[period] = report
        freeze_objective_statement_report(session, report_id=reports["FY2022"].id)
        report = reports["FY2023"]
        stored_object = stored_objects["FY2023"]
        first = freeze_objective_statement_report(session, report_id=report.id)
        second = freeze_objective_statement_report(session, report_id=report.id)
        batch = AnalysisBatch(
            name="隔离 SQLite 指标快照批次",
            module_kind="public",
            fact_context_version=1,
        )
        period = Period(month_key=202303, year=2023, quarter=1, month=3)
        session.add_all((batch, period))
        session.flush()
        import_version = ImportVersion(batch_id=batch.id, sequence=1)
        session.add(import_version)
        session.flush()
        metric_snapshot = MetricSnapshot(
            batch_id=batch.id,
            import_version_id=import_version.id,
            as_of_period_id=period.id,
            version=1,
            status="published",
            engine_version="sqlite-test",
            definition_set_id="sqlite-test",
            definition_set_hash="c" * 64,
            fingerprint="d" * 64,
        )
        session.add(metric_snapshot)
        session.commit()

        restored = session.get(ObjectiveReportSnapshot, first.id)
        assert restored is not None
        assert second.id == first.id
        assert restored.payload_hash == first.payload_hash
        assert restored.payload["report_type"] == "objective_statement"
        assert session.get(StatementReport, report.id) is not None

    backup = create_local_backup(
        database_path=database_path,
        object_root=object_root,
        backup_path=tmp_path / "damai-backup.zip",
    )
    restored_db_path, restored_object_root = restore_local_backup(
        backup_path=backup,
        destination=tmp_path / "restored",
    )
    restored_engine = build_engine(f"sqlite:///{restored_db_path}")
    with Session(restored_engine) as restored_session:
        restored_snapshot = restored_session.get(ObjectiveReportSnapshot, first.id)
        restored_report = restored_session.get(StatementReport, report.id)
        restored_source = restored_session.scalar(
            select(StoredObject).where(StoredObject.sha256 == stored_object.sha256)
        )
        assert restored_snapshot is not None
        assert restored_snapshot.payload_hash == first.payload_hash
        assert restored_report is not None
        assert restored_session.get(MetricSnapshot, metric_snapshot.id) is not None
        assert restored_source is not None
        assert LocalObjectStore(restored_object_root).read_by_sha(restored_source.sha256) == (
            fixture_root.joinpath("damai_fy2023.yaml").read_bytes()
        )
        cockpit = build_balance_sheet_module(load_fact_context(restored_session, "DAMAI.SYN"))
        assert cockpit["module"] == "balance-sheet"
        assert cockpit["period"] == "FY2023"
        assert cockpit["kpis"][0]["value"] == "71850.9310"
        projection = build_topic_projection(
            restored_session,
            SnapshotIdentity(report_id=str(restored_report.id), mapping_version="v1"),
        )
        traced = [entry for entry in projection.entries if entry.provenance]
        assert traced
        assert any(
            point.source_sha256 == restored_report.source_sha256
            for entry in traced
            for point in entry.provenance
        )


def test_sqlite_financial_facts_feed_cockpit_aggregation() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)
    fixture_root = Path(__file__).resolve().parents[4] / "fixtures/damai/statements"

    with Session(engine, expire_on_commit=False) as session:
        for period in ("FY2022", "FY2023"):
            fixture = fixture_root / f"damai_{period.lower()}.yaml"
            payload = yaml.safe_load(fixture.read_text(encoding="utf-8"))
            report = import_statement_report(
                session,
                company_name="大麦物流",
                stock_code="DAMAI.SYN",
                report_kind="年报",
                period_label=period,
                payload=payload,
                source_ref=str(fixture),
                source_sha256="a" * 64 if period == "FY2023" else "b" * 64,
            )
            session.flush()
            normalize_report(session, report)
            report.status = "published"
            freeze_objective_statement_report(session, report_id=report.id)
        session.commit()

        result = build_balance_sheet_module(load_fact_context(session, "DAMAI.SYN"))

    assert result["module"] == "balance-sheet"
    assert result["period"] == "FY2023"
    assert result["kpis"][0]["name"] == "总资产"
    assert result["kpis"][0]["value"] == "71850.9310"
