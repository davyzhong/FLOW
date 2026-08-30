from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from botocore.exceptions import ClientError
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from flow_api.api.routes.intake import get_db_session, get_source_storage
from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.object_store import ObjectStore
from flow_api.intake.source_storage import SourceStorage
from flow_api.main import create_app

from integration.intake_service_support import clean

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        del Bucket
        if Key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadObject",
            )
        content, content_type, metadata = self.objects[Key]
        return {
            "ContentLength": len(content),
            "ContentType": content_type,
            "Metadata": metadata,
        }

    def put_object(
        self,
        *,
        Bucket: str,  # noqa: N803
        Key: str,  # noqa: N803
        Body: bytes,  # noqa: N803
        ContentType: str,  # noqa: N803
        Metadata: dict[str, str],  # noqa: N803
    ) -> None:
        del Bucket
        self.objects[Key] = (Body, ContentType, Metadata)

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        del Bucket
        if Key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "GetObject",
            )
        return {"Body": BytesIO(self.objects[Key][0])}


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def api_context() -> tuple[Any, Session]:
    with Session(get_engine(), expire_on_commit=False) as session:
        clean(session)
        storage = SourceStorage(ObjectStore(client=FakeS3Client(), bucket="flow"))
        app = create_app()

        def session_override() -> Any:
            yield session
            session.flush()

        app.dependency_overrides[get_db_session] = session_override
        app.dependency_overrides[get_source_storage] = lambda: storage
        yield app, session
        session.rollback()
        clean(session)


async def test_typed_intake_api_runs_upload_to_published_version(
    api_context: tuple[Any, Session],
) -> None:
    app, _ = api_context
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        batch_response = await client.post(
            "/api/v1/intake/batches",
            json={"name": "August logistics management report"},
        )
        assert batch_response.status_code == 201
        batch = batch_response.json()
        assert batch["status"] == "draft"

        upload_response = await client.post(
            f"/api/v1/intake/batches/{batch['id']}/sources",
            files={
                "workbook": (
                    NONSTANDARD.name,
                    NONSTANDARD.read_bytes(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert upload_response.status_code == 201
        source = upload_response.json()
        assert source["sha256"] and source["size_bytes"] > 0

        profile_response = await client.get(f"/api/v1/intake/sources/{source['id']}/profile")
        assert profile_response.status_code == 200
        assert profile_response.json()["sheet_count"] == 9

        mapping_response = await client.post(
            f"/api/v1/intake/sources/{source['id']}/mapping-proposals"
        )
        assert mapping_response.status_code == 201
        mapping = mapping_response.json()
        assert len(mapping["mapping_hash"]) == 64
        assert mapping["unresolved_sheet_ids"] == []

        confirmation_response = await client.post(
            f"/api/v1/intake/mappings/{mapping['id']}/confirm",
            json={"actor": "finance.bp@example.com"},
        )
        assert confirmation_response.status_code == 200
        assert confirmation_response.json()["confirmed_by"] == "finance.bp@example.com"

        validation_response = await client.post(
            f"/api/v1/intake/sources/{source['id']}/validate",
            json={"mapping_version_id": mapping["id"]},
        )
        assert validation_response.status_code == 200
        version = validation_response.json()
        assert version["status"] == "ready"
        assert all(item["passed"] for item in version["reconciliations"])
        for issue in version["issues"]:
            if issue["severity"] == "warning":
                acknowledgement = await client.post(
                    f"/api/v1/intake/issues/{issue['id']}/acknowledge",
                    json={
                        "actor": "finance.bp@example.com",
                        "reason": "已与业务负责人核对口径",
                    },
                )
                assert acknowledgement.status_code == 200

        publication_response = await client.post(f"/api/v1/intake/imports/{version['id']}/publish")
        assert publication_response.status_code == 200
        published = publication_response.json()
        assert published["status"] == "published"
        assert published["is_published"] is True
        assert "export" in published["next_allowed_actions"]

        history_response = await client.get(f"/api/v1/intake/batches/{batch['id']}/versions")
        assert history_response.status_code == 200
        assert [item["sequence"] for item in history_response.json()["versions"]] == [1]


async def test_upload_and_transition_errors_are_typed(
    api_context: tuple[Any, Session],
) -> None:
    app, _ = api_context
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        batch = (await client.post("/api/v1/intake/batches", json={"name": "Invalid input"})).json()
        invalid = await client.post(
            f"/api/v1/intake/batches/{batch['id']}/sources",
            files={"workbook": ("source.csv", b"a,b\n1,2", "text/csv")},
        )
        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "invalid_source"

        missing = await client.post(
            "/api/v1/intake/imports/00000000-0000-0000-0000-000000000001/publish"
        )
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "import_not_found"
