"""真实数据导入 API（R2）：模板下载 / 校验并导入 / 数据集列表 / 删除。

单机边界：只操作当前 SQLite，按 dataset_id 与大麦演示数据隔离。
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, UploadFile

from flow_api.importer.service import collect_errors, import_workbook
from flow_api.importer.store import default_store
from flow_api.importer.templates import build_template_xlsx

router = APIRouter(prefix="/importer", tags=["importer"])

_SheetKind = Literal["trial_balance", "income_statement"]

_STORE: Any = None  # 延迟初始化（测试可注入隔离 engine）


def _get_store() -> Any:
    global _STORE
    if _STORE is None:
        from flow_api.infrastructure.db import get_engine

        _STORE = default_store(str(get_engine().url))
    return _STORE


def set_store(store: Any) -> None:
    """测试注入口：替换为隔离 engine 的 store。"""
    global _STORE
    _STORE = store


@router.get("/template/{sheet_kind}")
def download_template(sheet_kind: _SheetKind) -> Any:
    from fastapi.responses import Response

    sheet = {"trial_balance": "科目余额表", "income_statement": "利润表"}[sheet_kind]
    data = build_template_xlsx(sheet)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{sheet_kind}-template.xlsx"'},
    )


@router.post("/dataset")
async def upload_dataset(file: UploadFile, name: str = "") -> Any:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="上传文件为空")
    dataset_name = (name or "").strip() or (file.filename or "导入数据集")
    store = _get_store()
    outcome = import_workbook(store, data, dataset_name, file.filename or "upload.xlsx")
    if not outcome.ok:
        return {
            "ok": False,
            "errors": collect_errors(outcome),
        }
    return {
        "ok": True,
        "dataset_id": outcome.dataset_id,
        "trial_balance_rows": len(outcome.trial_balance.rows),
        "income_statement_rows": (
            len(outcome.income_statement.rows) if outcome.income_statement else 0
        ),
        "balance_summary": outcome.trial_balance.balance_summary,
    }


@router.get("/dataset")
def list_datasets() -> Any:
    return {"datasets": _get_store().list_datasets()}


@router.get("/dataset/{dataset_id}/balances")
def dataset_balances(dataset_id: str) -> Any:
    store = _get_store()
    if not any(d["id"] == dataset_id for d in store.list_datasets()):
        raise HTTPException(status_code=404, detail="dataset not found")
    return {"dataset_id": dataset_id, "rows": store.dataset_balances(dataset_id)}


@router.get("/dataset/{dataset_id}/metrics")
def dataset_metrics(dataset_id: str) -> Any:
    from flow_api.importer.normalization import derive_metrics

    store = _get_store()
    view = derive_metrics(store, dataset_id)
    if view is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return view


@router.get("/dataset/{dataset_id}/cockpit")
def dataset_cockpit(dataset_id: str) -> Any:
    from flow_api.importer.cockpit_view import cockpit_overview

    store = _get_store()
    view = cockpit_overview(store, dataset_id)
    if view is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return view


@router.get("/dataset/{dataset_id}/overview")
def dataset_overview(dataset_id: str) -> Any:
    store = _get_store()
    overview = store.dataset_overview(dataset_id)
    if overview is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return overview


@router.get("/dataset/{dataset_id}/chain")
def dataset_chain(dataset_id: str) -> Any:
    """数据集治理发布链回执（published / is_active_source）。"""
    from flow_api.importer.publish_chain import chain_receipt
    from flow_api.infrastructure.db import get_session_factory

    if not any(d["id"] == dataset_id for d in _get_store().list_datasets()):
        raise HTTPException(status_code=404, detail="dataset not found")
    with get_session_factory()() as session:
        return chain_receipt(session, dataset_id)


@router.post("/dataset/{dataset_id}/publish")
def publish_dataset_route(dataset_id: str) -> Any:
    """把导入账套发布为治理链（CanonicalPackage→发布门禁→快照→AnalysisRun）。

    勾稽不平（资产−负债−权益≠0）会被发布门禁拒绝（422），与上传校验的
    借贷平衡是两道独立的真实门禁：借贷平衡管行间记账，勾稽管类别归属。
    """
    from flow_api.importer.publish_chain import publish_dataset
    from flow_api.infrastructure.db import get_session_factory
    from flow_api.metrics.service import MetricSnapshotBlockedError

    store = _get_store()
    with get_session_factory()() as session:
        try:
            receipt = publish_dataset(session, store, dataset_id)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (ValueError, MetricSnapshotBlockedError) as error:
            session.rollback()
            raise HTTPException(status_code=422, detail=str(error)) from error
        session.commit()
    return receipt


@router.delete("/dataset/{dataset_id}")
def delete_dataset(dataset_id: str) -> Any:
    from flow_api.importer.publish_chain import withdraw_dataset_chain
    from flow_api.infrastructure.db import get_session_factory

    store = _get_store()
    if not store.delete_dataset(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")
    with get_session_factory()() as session:
        withdrawn = withdraw_dataset_chain(session, dataset_id)
        session.commit()
    return {"ok": True, "deleted": dataset_id, "chain_withdrawn": withdrawn}
