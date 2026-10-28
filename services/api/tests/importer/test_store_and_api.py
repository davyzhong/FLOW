"""R2 存储与 API 单测：隔离 SQLite engine，不触常驻库。"""
from __future__ import annotations

import io
from decimal import Decimal

import pytest
from openpyxl import Workbook
from sqlalchemy import create_engine

from flow_api.importer.service import import_workbook
from flow_api.importer.store import ImportStore
from flow_api.importer.templates import build_template_xlsx


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


def test_import_valid_workbook_creates_dataset(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "测试账套", "t.xlsx")
    assert outcome.ok, _errors(outcome)
    assert outcome.dataset_id is not None
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
    assert any("期末借贷不平衡" in e["message"] for e in _errors(outcome))


def test_missing_sheet_reports_read_error(store: ImportStore) -> None:
    workbook = Workbook()
    ws = workbook.active
    ws.title = "随便"
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
    data = build_template_xlsx()
    assert data[:2] == b"PK"  # xlsx zip 魔数


def _errors(outcome: object) -> list[dict[str, str]]:
    from flow_api.importer.service import collect_errors

    return collect_errors(outcome)  # type: ignore[arg-type]


def test_dataset_overview_aggregates_categories(store: ImportStore) -> None:
    outcome = import_workbook(store, _valid_workbook_bytes(), "概览账套", "o.xlsx")
    overview = store.dataset_overview(outcome.dataset_id)  # type: ignore[arg-type]
    assert overview is not None
    assert overview["total_assets"] == "12000"
    assert overview["total_liabilities"] == "12000"
    assert overview["total_equity"] == "0"
    assert Decimal(overview["identity_check"]) == Decimal("0")
    assert overview["periods"] == ["2025-01"]


def test_dataset_overview_missing_returns_none(store: ImportStore) -> None:
    assert store.dataset_overview("nonexistent") is None


def test_cockpit_overview_kpis(store: ImportStore) -> None:
    from flow_api.importer.cockpit_view import cockpit_overview

    rows = [
        {"会计期间": "2025-01", "科目编码": "1001", "科目名称": "库存现金", "科目类别": "资产",
         "方向": "借", "期初余额": "0", "本期借方发生额": "0", "本期贷方发生额": "0", "期末余额": "50000"},
        {"会计期间": "2025-01", "科目编码": "2001", "科目名称": "短期借款", "科目类别": "负债",
         "方向": "贷", "期初余额": "0", "本期借方发生额": "0", "本期贷方发生额": "0", "期末余额": "30000"},
        {"会计期间": "2025-01", "科目编码": "4001", "科目名称": "实收资本", "科目类别": "权益",
         "方向": "贷", "期初余额": "0", "本期借方发生额": "0", "本期贷方发生额": "0", "期末余额": "20000"},
        {"会计期间": "2025-01", "科目编码": "6001", "科目名称": "主营业务收入", "科目类别": "损益",
         "方向": "贷", "期初余额": "0", "本期借方发生额": "0", "本期贷方发生额": "80000", "期末余额": "0"},
        {"会计期间": "2025-01", "科目编码": "6401", "科目名称": "主营业务成本", "科目类别": "损益",
         "方向": "借", "期初余额": "0", "本期借方发生额": "60000", "本期贷方发生额": "0", "期末余额": "0"},
    ]
    from flow_api.importer.validation import validate_trial_balance
    result = validate_trial_balance(rows)
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
