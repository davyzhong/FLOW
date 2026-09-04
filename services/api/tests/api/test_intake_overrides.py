"""Task 3 契约测试：映射审阅的 corrective、版本化、可审计 override。

POST /api/v1/intake/mappings/{id}/overrides：
- 请求引用已 profile 的源表头与合法契约目标；stale hash / 跨批次 / 未知目标 /
  未知源列 / 重复源列 一律拒绝；
- 应用 override 产生**新的** MappingVersion（append-only）并记录确认人与时间。
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from botocore.exceptions import ClientError
from httpx import ASGITransport, AsyncClient
from integration.intake_service_support import clean
from sqlalchemy.orm import Session

from flow_api.api.routes.intake import get_db_session, get_source_storage
from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.object_store import ObjectStore
from flow_api.intake.source_storage import SourceStorage
from flow_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"
WORKBOOK_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ACTOR = "finance.bp@example.com"


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
        return {"ContentLength": len(content), "ContentType": content_type, "Metadata": metadata}

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
                "HeadObject",
            )
        return {"Body": BytesIO(self.objects[Key][0])}


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def client() -> Any:
    with Session(get_engine(), expire_on_commit=False) as session:
        clean(session)
        storage = SourceStorage(ObjectStore(client=FakeS3Client(), bucket="flow"))
        app = create_app()

        def session_override() -> Any:
            yield session
            session.flush()

        app.dependency_overrides[get_db_session] = session_override
        app.dependency_overrides[get_source_storage] = lambda: storage
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            async_client.test_session = session  # type: ignore[attr-defined]
            yield async_client
        session.rollback()
        clean(session)


async def _create_mapping_with_source(client: Any, batch_name: str) -> dict[str, Any]:
    batch = (await client.post("/api/v1/intake/batches", json={"name": batch_name})).json()
    upload = await client.post(
        f"/api/v1/intake/batches/{batch['id']}/sources",
        files={"workbook": (NONSTANDARD.name, NONSTANDARD.read_bytes(), WORKBOOK_MIME)},
    )
    source = upload.json()
    mapping = (await client.post(f"/api/v1/intake/sources/{source['id']}/mapping-proposals")).json()
    return {"batch": batch, "source": source, "mapping": mapping}


def _swap_overrides(mapping: dict[str, Any]) -> list[dict[str, str]]:
    sheet = mapping["sheets"][0]
    field_a, field_b = sheet["fields"][0], sheet["fields"][1]
    return [
        {
            "target_sheet_id": sheet["target_sheet_id"],
            "target_field_id": field_a["target_field_id"],
            "source_sheet": sheet["source_sheet"],
            "source_header": field_b["source_header"],
        },
        {
            "target_sheet_id": sheet["target_sheet_id"],
            "target_field_id": field_b["target_field_id"],
            "source_sheet": sheet["source_sheet"],
            "source_header": field_a["source_header"],
        },
    ]


async def test_override_creates_new_confirmed_mapping_version(client: Any) -> None:
    ctx = await _create_mapping_with_source(client, "override happy path")
    mapping = ctx["mapping"]
    overrides = _swap_overrides(mapping)

    response = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx["source"]["id"],
            "source_sha256": ctx["source"]["sha256"],
            "overrides": overrides,
        },
    )
    assert response.status_code == 201, response.text
    new_mapping = response.json()
    assert new_mapping["id"] != mapping["id"]
    assert new_mapping["sequence"] == mapping["sequence"] + 1
    assert new_mapping["confirmed_by"] == ACTOR

    sheet = next(
        s for s in new_mapping["sheets"] if s["target_sheet_id"] == overrides[0]["target_sheet_id"]
    )
    by_field = {f["target_field_id"]: f for f in sheet["fields"]}
    overridden = by_field[overrides[0]["target_field_id"]]
    assert overridden["source_header"] == overrides[0]["source_header"]
    assert overridden["method"] == "manual_override"
    assert overridden["confidence"] == "high"


async def test_override_rejects_unknown_target_and_source(client: Any) -> None:
    ctx = await _create_mapping_with_source(client, "override unknown")
    mapping = ctx["mapping"]
    base = {
        "actor": ACTOR,
        "source_file_id": ctx["source"]["id"],
        "source_sha256": ctx["source"]["sha256"],
    }
    sheet = mapping["sheets"][0]
    field = sheet["fields"][0]

    unknown_target = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            **base,
            "overrides": [
                {
                    "target_sheet_id": sheet["target_sheet_id"],
                    "target_field_id": "nope.field",
                    "source_sheet": sheet["source_sheet"],
                    "source_header": field["source_header"],
                }
            ],
        },
    )
    assert unknown_target.status_code == 422
    assert unknown_target.json()["detail"]["code"] == "unknown_target"

    unknown_source = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            **base,
            "overrides": [
                {
                    "target_sheet_id": sheet["target_sheet_id"],
                    "target_field_id": field["target_field_id"],
                    "source_sheet": sheet["source_sheet"],
                    "source_header": "不存在的源表头",
                }
            ],
        },
    )
    assert unknown_source.status_code == 422
    assert unknown_source.json()["detail"]["code"] == "unknown_source_column"


async def test_override_rejects_duplicate_source_column(client: Any) -> None:
    ctx = await _create_mapping_with_source(client, "override duplicate")
    mapping = ctx["mapping"]
    sheet = mapping["sheets"][0]
    field_a, field_b = sheet["fields"][0], sheet["fields"][1]
    response = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx["source"]["id"],
            "source_sha256": ctx["source"]["sha256"],
            "overrides": [
                {
                    "target_sheet_id": sheet["target_sheet_id"],
                    "target_field_id": field_a["target_field_id"],
                    "source_sheet": sheet["source_sheet"],
                    "source_header": field_b["source_header"],
                }
            ],
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "duplicate_source_column"


async def test_override_rejects_stale_source_hash(client: Any) -> None:
    ctx = await _create_mapping_with_source(client, "override stale")
    mapping = ctx["mapping"]
    response = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx["source"]["id"],
            "source_sha256": "0" * 64,
            "overrides": _swap_overrides(mapping),
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_source"


async def test_override_rejects_cross_batch_source(client: Any) -> None:
    ctx_a = await _create_mapping_with_source(client, "override cross A")
    ctx_b = await _create_mapping_with_source(client, "override cross B")
    response = await client.post(
        f"/api/v1/intake/mappings/{ctx_a['mapping']['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx_b["source"]["id"],
            "source_sha256": ctx_b["source"]["sha256"],
            "overrides": _swap_overrides(ctx_a["mapping"]),
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "cross_batch_source"


@pytest.mark.parametrize("operation", ["confirm", "validate"])
async def test_persisted_override_can_be_confirmed_and_extracted(
    client: Any, operation: str
) -> None:
    from uuid import UUID

    from openpyxl import load_workbook
    from sqlalchemy import select

    from flow_api.infrastructure.models.intake import SourceRecord

    ctx = await _create_mapping_with_source(client, "persisted override")
    overrides = _swap_overrides(ctx["mapping"])
    response = await client.post(
        f"/api/v1/intake/mappings/{ctx['mapping']['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx["source"]["id"],
            "source_sha256": ctx["source"]["sha256"],
            "overrides": overrides,
        },
    )
    assert response.status_code == 201, response.text
    mapping = response.json()
    if operation == "confirm":
        confirmed = await client.post(
            f"/api/v1/intake/mappings/{mapping['id']}/confirm", json={"actor": ACTOR}
        )
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["mapping_hash"] == mapping["mapping_hash"]
        assert confirmed.json()["sheets"] == mapping["sheets"]
    validated = await client.post(
        f"/api/v1/intake/sources/{ctx['source']['id']}/validate",
        json={"mapping_version_id": mapping["id"]},
    )
    assert validated.status_code == 200, validated.text
    records = client.test_session.scalars(
        select(SourceRecord).where(SourceRecord.import_version_id == UUID(validated.json()["id"]))
    ).all()
    sheet = mapping["sheets"][0]
    field = next(
        f for f in sheet["fields"] if f["target_field_id"] == overrides[0]["target_field_id"]
    )
    record = next(
        r
        for r in records
        if r.canonical_field == f"{sheet['target_sheet_id']}.{field['target_field_id']}"
    )
    assert record.source_column == field["source_column"]
    workbook = load_workbook(NONSTANDARD, read_only=True)
    try:
        expected = workbook[sheet["source_sheet"]][
            f"{field['source_column']}{record.source_row}"
        ].value
        assert record.raw_value == {"value": expected}
    finally:
        workbook.close()


async def test_override_rejects_column_from_another_sheet(client: Any) -> None:
    ctx = await _create_mapping_with_source(client, "cross sheet")
    mapping = ctx["mapping"]
    overrides = _swap_overrides(mapping)
    overrides[0]["source_sheet"] = mapping["sheets"][1]["source_sheet"]
    overrides[0]["source_header"] = mapping["sheets"][1]["fields"][0]["source_header"]
    response = await client.post(
        f"/api/v1/intake/mappings/{mapping['id']}/overrides",
        json={
            "actor": ACTOR,
            "source_file_id": ctx["source"]["id"],
            "source_sha256": ctx["source"]["sha256"],
            "overrides": overrides,
        },
    )
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("operation", ["confirm", "validate"])
@pytest.mark.parametrize("corruption", ["hash", "sha", "source_id", "batch"])
async def test_mapping_rejects_corrupted_persisted_identity(
    client: Any,
    operation: str,
    corruption: str,
) -> None:
    from uuid import UUID, uuid4

    from flow_api.infrastructure.models.intake import MappingVersion

    ctx = await _create_mapping_with_source(client, "identity check")
    mapping = client.test_session.get(MappingVersion, UUID(ctx["mapping"]["id"]))
    spec = dict(mapping.mapping_spec)
    if corruption == "hash":
        mapping.mapping_hash = "0" * 64
    elif corruption == "sha":
        spec["source_sha256"] = "0" * 64
    elif corruption == "source_id":
        spec["_source_file_id"] = str(uuid4())
    else:
        other = (await client.post("/api/v1/intake/batches", json={"name": "other batch"})).json()
        mapping.batch_id = UUID(other["id"])
    mapping.mapping_spec = spec
    client.test_session.flush()
    if operation == "confirm":
        response = await client.post(
            f"/api/v1/intake/mappings/{mapping.id}/confirm", json={"actor": ACTOR}
        )
    else:
        response = await client.post(
            f"/api/v1/intake/sources/{ctx['source']['id']}/validate",
            json={"mapping_version_id": str(mapping.id)},
        )
    assert response.status_code == 409, response.text
