"""R2 存储与 API 单测：隔离 SQLite engine，不触常驻库。"""
from __future__ import annotations

import io
from decimal import Decimal

import pytest
from openpyxl import Workbook
from sqlalchemy import create_engine

from flow_api.importer.cockpit_view import cockpit_overview
from flow_api.importer.service import collect_errors, import_workbook
from flow_api.importer.store import ImportStore
from flow_api.importer.templates import build_template_xlsx
from flow_api.importer.validation import validate_trial_balance


@pytest.fixture()
def store() -> ImportStore:
    return ImportStore(create_engine("sqlite:///:memory:"))


def _valid_workbook_bytes() -> bytes:
    workbook = Workbook()
    ws = workbook.active
    ws.title = "科目余额表"
    ws.append(["会计期间", "科目编码", "科目名称", "科目类别", "方向",
               "期初余额", "本期借方发生额", "本期贷方发生额", "期末余额"])
    ws.append(["2025-01", "1001", "库存现金", "资产", "借", "10000", "0", "0", "12000"])
    ws.append(["2025-01", "2001", "短期借款", "负债", "贷", "10000", "0", "0", "12000"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _kpi_rows() -> list[dict[str, str]]:
    def row(code: str, name: str, category: str, direction: str, closing: str,
            debit: str = "0", credit: str = "0") -> dict[str, str]:
        return {
            "会计期间": "2025-01", "科目编码": code, "科目名称": name,
            "科目类别": category, "方向": direction, "期初余额": "0",
            "本期借方发生额": debit, "本期贷方发生额": credit, "期末余额": closing,
        }

    return [
        row("1001", "库存现金", "资产", "借", "50000"),
        row("2001", "短期借款", "负债", "贷", "30000"),
        row("4001", "实收资本", "权益", "贷", "20000"),
        row("6001", "主营业务收入", "损益", "贷", "0", credit="80000"),
        row("6401", "主营业务成本", "损益", "借", "0", debit="60000"),
    ]


def test_import_valid_workbook_creates_dataset(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "测试账套", "t.xlsx")
    assert outcome.ok, collect_errors(outcome)
    datasets = store.list_datasets()
    assert len(datasets) == 1
    assert datasets[0]["name"] == "测试账套"


def test_balances_roundtrip_as_decimal(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "账套", "t.xlsx")
    rows = store.dataset_balances(outcome.dataset_id)  # type: ignore[arg-type]
    assert len(rows) == 2
    assert rows[0]["closing_balance"] == Decimal("12000")


def test_unbalanced_workbook_rejected_without_dataset(store: ImportStore) -> None:
    workbook = Workbook()
    ws = workbook.active
    ws.title = "科目余额表"
    ws.append(["会计期间", "科目编码", "科目名称", "科目类别", "方向",
               "期初余额", "本期借方发生额", "本期贷方发生额", "期末余额"])
    ws.append(["2025-01", "1001", "库存现金", "资产", "借", "10000", "0", "0", "12000"])
    ws.append(["2025-01", "2001", "短期借款", "负债", "贷", "10000", "0", "0", "55555"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    outcome = import_workbook(store, buffer.getvalue(), "坏账套", "bad.xlsx")
    assert not outcome.ok
    assert store.list_datasets() == []
    assert any("期末借贷不平衡" in e["message"] for e in collect_errors(outcome))


def test_missing_sheet_reports_read_error(store: ImportStore) -> None:
    workbook = Workbook()
    workbook.active.title = "随便"
    buffer = io.BytesIO()
    workbook.save(buffer)
    outcome = import_workbook(store, buffer.getvalue(), "x", "x.xlsx")
    assert not outcome.ok
    assert outcome.read_error is not None
    assert "缺少工作表" in outcome.read_error


def test_delete_dataset_removes_rows(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "x", "x.xlsx")
    assert store.delete_dataset(outcome.dataset_id)  # type: ignore[arg-type]
    assert store.list_datasets() == []
    assert store.dataset_balances(outcome.dataset_id) == []  # type: ignore[arg-type]


def test_template_download_bytes() -> None:
    assert build_template_bytes()[:2] == b"PK"


def build_template_bytes() -> bytes:
    return build_template_xlsx()


def test_dataset_overview_missing_returns_none(store: ImportStore) -> None:
    assert store.dataset_overview("nonexistent") is None


def test_dataset_overview_aggregates_categories(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "概览账套", "o.xlsx")
    overview = store.dataset_overview(outcome.dataset_id)  # type: ignore[arg-type]
    assert overview is not None
    assert overview["total_assets"] == "12000"
    assert overview["total_liabilities"] == "12000"
    assert overview["total_equity"] == "0"
    assert Decimal(overview["identity_check"]) == Decimal("0")
    assert overview["periods"] == ["2025-01"]


def test_cockpit_overview_kpis(store: ImportStore) -> None:
    result = validate_trial_balance(_kpi_rows())
    assert result.ok, result.errors
    dataset_id = store.save_dataset("KPI 账套", "k.xlsx", result, None)
    view = cockpit_overview(store, dataset_id)
    assert view is not None
    kpis = {k["code"]: k["value"] for k in view["kpi"]}
    assert kpis["total_assets"] == "50000"
    assert kpis["total_liabilities"] == "30000"
    assert kpis["total_equity"] == "20000"
    assert kpis["net_profit"] == "20000"
    assert kpis["debt_ratio"] == "0.6000"
    assert view["identity_check"]["passed"] is True
