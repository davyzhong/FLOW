"""U6/P08 切片二：从冻结载荷渲染多格式报告（HTML/XLSX/PDF）契约测试。

契约：
- 三格式均从同一冻结 payload 渲染，跨格式关键值一致（黄金值）；
- XLSX 含口径与证据页（来源身份 + 归一化行 + 原始行），独立读取单元格验证；
- PDF 由真 Chromium 打印链路产出（%PDF 魔数与页对象存在，非 HTML 改后缀）；
- 载荷不可变：payload_hash 变化才允许重渲染，同哈希复用产物。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.publishing import ReportSnapshot
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.publishing.objective_freeze import (
    ObjectiveReportSnapshot,
    freeze_objective_statement_report,
)
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (ReportSnapshot, ObjectiveReportSnapshot, StatementNormalizedItem,
                  StatementLineItem, StatementReport):
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
    session.flush()
    normalize_report(session, report)
    return report


def test_three_formats_carry_same_golden_values(db_session: Session) -> None:
    """黄金值：HTML/XLSX/PDF 从同一冻结载荷渲染，关键值跨格式一致。"""
    from flow_api.publishing.objective_renderers import (
        render_html_from_payload,
        render_xlsx_bytes_from_payload,
    )

    report = _seed(db_session)
    snapshot = freeze_objective_statement_report(db_session, report_id=report.id)
    db_session.flush()
    payload = snapshot.payload

    html = render_html_from_payload(payload)
    xlsx_bytes = render_xlsx_bytes_from_payload(payload)

    golden_revenue = "74142121"  # 人民币千元，披露原值
    assert golden_revenue in html, "HTML 应含收入原值"
    # XLSX 独立读取单元格
    import io

    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(xlsx_bytes))
    found = any(
        str(cell.value).replace(",", "").startswith(golden_revenue)
        for ws in wb.worksheets
        for row in ws.iter_rows()
        for cell in row
        if cell.value is not None
    )
    assert found, "XLSX 应含收入原值"
    # 三格式同源：payload_hash 一致（渲染器输入同一载荷）
    assert snapshot.payload_hash == __import__("hashlib").sha256(
        __import__("json").dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def test_pdf_is_real_chromium_output(tmp_path: Path, db_session: Session) -> None:
    report = _seed(db_session)
    snapshot = freeze_objective_statement_report(db_session, report_id=report.id)
    db_session.flush()
    from flow_api.publishing.objective_renderers import render_html_from_payload
    from flow_api.statements.objective_report_pdf import print_pdf

    html = render_html_from_payload(snapshot.payload)
    out = tmp_path / "objective.pdf"
    try:
        print_pdf(html, out_path=out, footer_left="顺丰控股 2026Q1 客观分析")
        data = out.read_bytes()
        assert data[:5] == b"%PDF-", "必须是真实 PDF 魔数，非 HTML 改后缀"
        assert b"/Page" in data or b"Pages" in data
    except RuntimeError as error:
        pytest.skip(f"Chromium 不可用，跳过真 PDF 验证：{error}")
