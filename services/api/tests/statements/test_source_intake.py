"""公开财报上传与来源登记（B01）测试。

- 探针：格式/大小/扫描件拒绝（可解释错误码），文本 PDF 返回哈希与页数；
- 识别候选：A 股/港股公司与期间模式（单元级）；
- API：上传 201、同 sha256 幂等 duplicate、错误格式 422、列表端点；
- 存储：以内存 ObjectStore 替身验证内容寻址读写；真实 S3 链路见验收记录。
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from flow_api.api.routes.statements import get_statement_session, get_statement_source_intake
from flow_api.infrastructure.models.statement import StatementSource
from flow_api.main import create_app
from flow_api.settings import get_settings
from flow_api.statements.intake import (
    MIN_TEXT_CHARS,
    StatementSourceError,
    StatementSourceIntake,
    _identify_candidates,
    probe_statement_pdf,
)


def make_pdf(text: str | None) -> bytes:
    content_stream = b""
    if text:
        content_stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    page_obj = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    stream_obj = (
        b"<< /Length " + str(len(content_stream)).encode()
        + b" >>\nstream\n" + content_stream + b"\nendstream"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        page_obj,
        stream_obj,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for index, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    out += (trailer + f"startxref\n{xref_pos}\n%%EOF").encode()
    return out


SAMPLE_TEXT = "Test Corp 2026 First Quarter Report Revenue disclosure sample " * 6
SAMPLE_PDF = make_pdf(SAMPLE_TEXT)
SCANNED_PDF = make_pdf(None)


class FakeObjectStore:
    """内容寻址内存替身：与 ObjectStore.put_immutable 同接口。"""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_immutable(self, content: bytes, filename: str) -> Any:
        sha = hashlib.sha256(content).hexdigest()
        key = f"raw/{sha[:2]}/{sha}"
        self.objects.setdefault(key, content)
        return SimpleNamespace(
            sha256=sha, object_key=key, size_bytes=len(content), content_type="application/pdf"
        )


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    session.execute(delete(StatementSource))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> Iterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_statement_session] = lambda: db_session
    app.dependency_overrides[get_statement_source_intake] = lambda: StatementSourceIntake(
        FakeObjectStore(), max_bytes=80 * 1024 * 1024  # type: ignore[arg-type]
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def test_probe_rejects_non_pdf_filename() -> None:
    with pytest.raises(StatementSourceError, match="仅支持 PDF") as exc:
        probe_statement_pdf(SAMPLE_PDF, "report.xlsx", max_bytes=1024 * 1024)
    assert exc.value.code == "unsupported_source_format"


def test_probe_rejects_bad_magic() -> None:
    with pytest.raises(StatementSourceError) as exc:
        probe_statement_pdf(b"not a pdf at all", "report.pdf", max_bytes=1024 * 1024)
    assert exc.value.code == "invalid_pdf"


def test_probe_rejects_oversize() -> None:
    with pytest.raises(StatementSourceError) as exc:
        probe_statement_pdf(SAMPLE_PDF, "report.pdf", max_bytes=100)
    assert exc.value.code == "source_too_large"


def test_probe_rejects_scanned_pdf_with_explanation() -> None:
    with pytest.raises(StatementSourceError) as exc:
        probe_statement_pdf(SCANNED_PDF, "scan.pdf", max_bytes=1024 * 1024)
    assert exc.value.code == "scanned_pdf_unsupported"
    assert "OCR" in exc.value.message


def test_probe_returns_hash_pages_and_text() -> None:
    probe = probe_statement_pdf(SAMPLE_PDF, "report.pdf", max_bytes=1024 * 1024)
    assert probe.sha256 == hashlib.sha256(SAMPLE_PDF).hexdigest()
    assert probe.page_count == 1
    assert probe.text_chars >= MIN_TEXT_CHARS


def test_identify_candidates_a_share() -> None:
    candidates = _identify_candidates(
        "圆通速递股份有限公司 2026 年第一季度报告 证券代码：600233 证券简称：圆通速递"
    )
    assert candidates["company_candidate"] == "圆通速递"
    assert candidates["stock_code_candidate"] == "600233"
    assert candidates["period_candidate"] == "2026Q1"
    assert candidates["report_kind_candidate"] == "一季报"


def test_identify_candidates_hk_annual() -> None:
    candidates = _identify_candidates("京东物流股份有限公司 股份代號: 2618 FY2025 Annual Report")
    assert candidates["stock_code_candidate"] == "2618.HK"
    assert candidates["period_candidate"] == "FY2025"
    assert candidates["report_kind_candidate"] == "年报"


async def test_upload_registers_source_and_is_idempotent(
    client: AsyncClient, db_session: Session
) -> None:
    files = {"workbook": ("YTO_2026_Q1.pdf", SAMPLE_PDF, "application/pdf")}
    first = await client.post("/api/v1/statements/sources", files=files)
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["sha256"] == hashlib.sha256(SAMPLE_PDF).hexdigest()
    assert body["duplicate"] is False
    assert body["page_count"] == 1

    second = await client.post("/api/v1/statements/sources", files=files)
    assert second.status_code == 201
    assert second.json()["duplicate"] is True
    assert second.json()["id"] == body["id"]

    rows = db_session.scalar(select(func.count()).select_from(StatementSource))
    assert rows == 1

    listing = await client.get("/api/v1/statements/sources")
    assert listing.status_code == 200
    assert [s["sha256"] for s in listing.json()["sources"]] == [body["sha256"]]


async def test_upload_rejects_invalid_pdf(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/statements/sources",
        files={"workbook": ("fake.pdf", b"definitely not a pdf", "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_pdf"


async def test_upload_rejects_scanned_pdf(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/statements/sources",
        files={"workbook": ("scan.pdf", SCANNED_PDF, "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "scanned_pdf_unsupported"
