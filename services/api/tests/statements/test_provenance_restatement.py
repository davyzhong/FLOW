"""T10-B3/B4 验收：溯源页锚写入 + 重述 supersedes 链与差异清单。"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import StatementReport
from flow_api.statements.importer import (
    StatementImportError,
    import_statement_report,
    load_provenance_index,
)


@pytest.fixture
def db_session():
    from flow_api.infrastructure.db import get_session_factory

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

PAYLOAD = {
    "unit": "人民币千元",
    "statements": {
        "合并资产负债表": [
            {"item": "货币资金", "期末余额": 1000, "期初余额": 900},
            {"item": "借款", "期末余额": 500, "期初余额": 400},
        ],
    },
}


def _provenance_index() -> dict:
    """构造溯源索引：货币资金命中期末页锚；借款两条同名行值各归各页。"""
    from flow_api.statements.importer import COLUMN_ALIASES

    index: dict[tuple[str, str, str, str], set[tuple[Decimal, int, str]]] = {}
    entries = [
        ("合并资产负债表", "货币资金", "期末余额", 1000, 12, "strong"),
        ("合并资产负债表", "货币资金", "期初余额", 900, 12, "strong"),
        ("合并资产负债表", "借款", "期末余额", 500, 13, "strong"),
        ("合并资产负债表", "借款", "期初余额", 400, 13, "weak"),
    ]
    for statement, item, column, value, page, mode in entries:
        normalized = COLUMN_ALIASES.get(column, column)
        index.setdefault((statement, item, normalized, "002352.SZ"), set()).add(
            (Decimal(value), page, mode)
        )
    return index


def test_provenance_pages_written(db_session: Session) -> None:
    report = import_statement_report(
        db_session,
        company_name="溯源测试",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2099Q1",
        payload=PAYLOAD,
        source_ref="test/provenance.pdf",
        provenance_index=_provenance_index(),
    )
    pages = {
        (i.item_name, i.sort_order): (i.page_number, i.page_anchor)
        for i in report.items
    }
    assert pages[("货币资金", 0)] == (12, "strong")
    assert pages[("借款", 1)][0] in (13, None)


def test_provenance_without_index_stays_null(db_session: Session) -> None:
    report = import_statement_report(
        db_session,
        company_name="溯源测试",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2098Q1",
        payload=PAYLOAD,
        source_ref="test/provenance_none.pdf",
    )
    assert all(i.page_number is None for i in report.items)


def test_restatement_creates_supersedes_chain_and_diff(db_session: Session) -> None:
    first = import_statement_report(
        db_session,
        company_name="重述测试",
        stock_code="002353.SZ",
        report_kind="一季报",
        period_label="2099Q1",
        payload=PAYLOAD,
        source_ref="test/restatement_v1.pdf",
    )
    restated_payload = {
        "unit": "人民币千元",
        "statements": {
            "合并资产负债表": [
                {"item": "货币资金", "期末余额": 1200, "期初余额": 900},
                {"item": "借款", "期末余额": 500, "期初余额": 400},
            ],
        },
    }
    second = import_statement_report(
        db_session,
        company_name="重述测试",
        stock_code="002353.SZ",
        report_kind="一季报",
        period_label="2099Q1",
        payload=restated_payload,
        source_ref="test/restatement_v2.pdf",
    )
    assert second.version == first.version + 1
    assert second.supersedes_id == first.id
    # 旧版完整保留
    old = db_session.scalar(
        select(StatementReport).where(StatementReport.id == first.id)
    )
    assert old is not None
    assert sorted(i.value_end for i in old.items if i.item_name == "货币资金") == [
        Decimal("1000")
    ]
    # compute_diff 用独立连接，先提交使重述链可见；用后清理测试行
    db_session.commit()
    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
    try:
        import statement_restatement_diff as diff_mod

        diff = diff_mod.compute_diff("002353.SZ", "2099Q1", "一季报")
        assert diff is not None
        assert diff["supersedes_chain"]["supersedes_id_consistent"] is True
        assert diff["changed_count"] == 1, diff["changed"]
        changed = diff["changed"][0]
        assert changed["key"][1] == "货币资金"
        assert Decimal(changed["old"]) == Decimal("1000")
        assert Decimal(changed["new"]) == Decimal("1200")
        assert Decimal(changed["delta"]) == Decimal("200")
    finally:
        db_session.delete(second)
        old_row = db_session.get(StatementReport, first.id)
        if old_row is not None:
            db_session.delete(old_row)
        db_session.commit()


def test_unknown_column_rejected() -> None:
    import pytest

    from flow_api.infrastructure.db import get_session_factory

    bad = {
        "unit": "人民币千元",
        "statements": {"合并资产负债表": [{"item": "x", "不存在的列": 1}]},
    }
    with (
        get_session_factory()() as session,
        pytest.raises(StatementImportError, match="出现未知列"),
    ):
        import_statement_report(
                session,
                company_name="c",
                stock_code="S",
                report_kind="年报",
                period_label="P",
                payload=bad,
                source_ref="s.pdf",
            )


def test_load_provenance_index_normalizes_columns(tmp_path) -> None:
    import yaml

    answer_set = tmp_path / "answer_set.yaml"
    answer_set.write_text(
        yaml.safe_dump(
            {
                "entries": [
                    {
                        "source_pdf": "a.pdf",
                        "stock_code": "S",
                        "period_label": "P",
                        "report_kind": "年报",
                        "page": 7,
                        "match_mode": "strong",
                        "statement": "合并资产负债表",
                        "item": "货币资金",
                        "column": "期末余额",
                        "value": 1000,
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    index = load_provenance_index(answer_set)
    assert any(key[2] == "value_end" for key in index), index
