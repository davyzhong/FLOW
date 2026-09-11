"""O3：经营快照进入统一 append-only 发布与下载登记链。"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import PublicationAttempt
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.operations.freeze import freeze_operations_overview
from flow_api.operations.publication import OperationsPublicationService
from flow_api.publishing.objective_freeze import ObjectiveReportSnapshot
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"


class FakeStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_immutable(self, content: bytes, filename: str) -> StoredObject:
        import hashlib
        import mimetypes

        digest = hashlib.sha256(content).hexdigest()
        self.objects[digest] = content
        return StoredObject(
            sha256=digest,
            object_key=f"raw/{digest[:2]}/{digest}",
            size_bytes=len(content),
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
        )

    def read_by_sha(self, sha256: str) -> bytes:
        return self.objects[sha256]


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        PublicationAttempt,
        ObjectiveReportSnapshot,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _seed(session: Session) -> Any:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )
    normalize_report(session, report)
    report.status = "published"
    session.flush()
    return report


def test_operations_publication_persists_four_formats_append_only(
    db_session: Session,
) -> None:
    report = _seed(db_session)
    snapshot = freeze_operations_overview(db_session, report_id=report.id)
    store = FakeStore()
    service = OperationsPublicationService(
        store=store,
        pdf_printer=lambda _html: b"%PDF-1.4 operations",
    )

    outcomes = service.publish(db_session, snapshot.id)
    assert outcomes == {
        "pptx": "succeeded",
        "xlsx": "succeeded",
        "html": "succeeded",
        "pdf": "succeeded",
    }

    attempts = db_session.scalars(
        select(PublicationAttempt)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot.id)
        .order_by(PublicationAttempt.sequence)
    ).all()
    assert [item.format for item in attempts] == ["pptx", "xlsx", "html", "pdf"]
    assert all(item.report_snapshot_id is None for item in attempts)
    assert all(item.stored_object_id is not None for item in attempts)

    service.publish(db_session, snapshot.id, formats=("xlsx",))
    retry = db_session.scalars(
        select(PublicationAttempt)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot.id)
        .order_by(PublicationAttempt.sequence)
    ).all()
    assert [item.sequence for item in retry] == [1, 2, 3, 4, 5]


def test_operations_publication_rejects_wrong_snapshot_type(db_session: Session) -> None:
    from flow_api.operations.publication import OperationsPublicationError
    from flow_api.publishing.objective_freeze import freeze_objective_statement_report

    report = _seed(db_session)
    financial = freeze_objective_statement_report(db_session, report_id=report.id)
    with pytest.raises(OperationsPublicationError, match="operations_overview"):
        OperationsPublicationService(store=FakeStore()).publish(db_session, financial.id)


def test_operations_attempts_are_listed_and_downloadable(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi.testclient import TestClient

    from flow_api.api.routes import publishing as publishing_routes
    from flow_api.api.routes.investigations import get_investigation_session
    from flow_api.api.routes.operations import get_operations_session
    from flow_api.main import create_app

    report = _seed(db_session)
    snapshot = freeze_operations_overview(db_session, report_id=report.id)
    store = FakeStore()
    OperationsPublicationService(store=store).publish(db_session, snapshot.id, formats=("xlsx",))
    monkeypatch.setattr(publishing_routes, "get_publication_object_store", lambda: store)

    app = create_app()
    app.dependency_overrides[get_operations_session] = lambda: db_session
    app.dependency_overrides[get_investigation_session] = lambda: db_session
    client = TestClient(app)

    listing = client.get("/api/v1/operations/snapshots")
    assert listing.status_code == 200
    assert listing.json()["snapshots"][0]["id"] == str(snapshot.id)

    attempts = client.get(f"/api/v1/operations/snapshots/{snapshot.id}/attempts")
    assert attempts.status_code == 200
    attempt = attempts.json()["attempts"][0]
    assert attempt["format"] == "xlsx" and attempt["download_available"] is True

    download = client.get(f"/api/v1/publishing/attempts/{attempt['attempt_id']}/download")
    assert download.status_code == 200
    assert download.content[:2] == b"PK"
    assert download.headers["content-disposition"].endswith('.xlsx"')


def test_download_reports_missing_immutable_object_as_conflict(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi.testclient import TestClient

    from flow_api.api.routes import publishing as publishing_routes
    from flow_api.api.routes.investigations import get_investigation_session
    from flow_api.api.routes.operations import get_operations_session
    from flow_api.infrastructure.object_store import ImmutableObjectNotFoundError
    from flow_api.main import create_app

    report = _seed(db_session)
    snapshot = freeze_operations_overview(db_session, report_id=report.id)
    store = FakeStore()
    OperationsPublicationService(store=store).publish(db_session, snapshot.id, formats=("xlsx",))
    attempt = db_session.scalar(
        select(PublicationAttempt).where(
            PublicationAttempt.objective_report_snapshot_id == snapshot.id
        )
    )
    assert attempt is not None

    class MissingStore:
        def read_by_sha(self, sha256: str) -> bytes:
            raise ImmutableObjectNotFoundError(sha256)

    monkeypatch.setattr(
        publishing_routes,
        "get_publication_object_store",
        lambda: MissingStore(),
    )
    app = create_app()
    app.dependency_overrides[get_operations_session] = lambda: db_session
    app.dependency_overrides[get_investigation_session] = lambda: db_session

    response = TestClient(app).get(
        f"/api/v1/publishing/attempts/{attempt.id}/download"
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "download_not_available"
