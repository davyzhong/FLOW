from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.metric_library import (
    AccountingAccount,
    AccountingFoundation,
    EntryLine,
    MetricActionRequest,
    MetricDraftRequest,
    MetricEntry,
    MetricEntryActionResponse,
    MetricGovernanceEventLine,
    MetricGovernanceEventListResponse,
    MetricImpactResponse,
    MetricLibraryResponse,
    ReportItem,
    SandboxDiffLine,
)
from flow_api.api.schemas.metric_library import (
    AccountingStandard as AccountingStandardRow,
)
from flow_api.api.schemas.metric_library import (
    EntryTemplate as EntryTemplateRow,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricDictionaryEntry,
    StatementLineMapping,
)
from flow_api.metric_library_store.binding import build_execution_binding
from flow_api.metric_library_store.governance import GovernanceError, MetricGovernance
from flow_api.metric_library_store.impact import ImpactError, MetricImpactService
from flow_api.metric_library_store.importer import import_all

router = APIRouter(prefix="/metric-library", tags=["metric-library"])

METRIC_LIBRARY_PATHS = (
    Path("config/metrics/metric_dictionary_v1.yaml"),
    Path("config/metrics/accounting_foundation_v1.yaml"),
)
CONFIG_ROOT = METRIC_LIBRARY_PATHS[0].parent


def resolve_metric_library_root(module_path: Path = Path(__file__)) -> Path:
    resolved_module_path = module_path.resolve()
    candidates = (resolved_module_path.parent, *resolved_module_path.parents)
    for candidate in candidates:
        if all((candidate / relative_path).is_file() for relative_path in METRIC_LIBRARY_PATHS):
            return candidate
    raise RuntimeError(f"FLOW metric library datasets not found from {resolved_module_path}")


class MetricLibraryAudit:
    """导入/退役审计的轻量 JSONL 记录器。

    审计行追加到 var/ 下（不进 git），结构化记录动作、操作者、摘要与时间。
    数据库行级审计由导入幂等 + 版本状态承担；本文件满足操作可追溯要求。
    """

    def __init__(self, root: Path) -> None:
        self.path = root / "var" / "metric_library_audit.jsonl"

    def append(self, action: str, actor: str, summary: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "id": str(uuid4()),
            "action": action,
            "actor": actor,
            "summary": summary,
            "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


@lru_cache
def _yaml_payload() -> MetricLibraryResponse:
    root = resolve_metric_library_root()
    dictionary: dict[str, Any] = yaml.safe_load((root / METRIC_LIBRARY_PATHS[0]).read_text())
    foundation: dict[str, Any] = yaml.safe_load((root / METRIC_LIBRARY_PATHS[1]).read_text())
    metrics = [
        MetricEntry(collection="general", **entry) for entry in dictionary["metrics_general"]
    ] + [
        MetricEntry(collection="logistics", **entry) for entry in dictionary["metrics_logistics"]
    ]
    return MetricLibraryResponse(
        dictionary_id=dictionary["dictionary_id"],
        status=dictionary["status"],
        decision_ref=dictionary["decision_ref"],
        created=str(dictionary["created"]),
        standards_scope=list(dictionary["standards_scope"]),
        domains=dict(dictionary["domains"]),
        report_items=[
            ReportItem(item_id=item_id, **names)
            for item_id, names in dictionary["report_items"].items()
        ],
        metrics=metrics,
        relations=dictionary["relations"],
        accounting=AccountingFoundation(**foundation),
    )


def _db_payload(session: Session) -> MetricLibraryResponse | None:
    entries = session.scalars(
        select(MetricDictionaryEntry)
        .where(MetricDictionaryEntry.status == "effective")
        .order_by(MetricDictionaryEntry.collection, MetricDictionaryEntry.metric_code)
    ).all()
    if not entries:
        return None
    fallback = _yaml_payload()
    by_code = {(e.collection, e.metric_code): e for e in entries}
    metrics = [
        MetricEntry(
            collection=m.collection,
            metric_code=m.metric_code,
            name=by_code[(m.collection, m.metric_code)].name,
            domain=m.domain,
            definition=m.definition,
            formula_text=m.formula_text,
            formula=m.formula,
            unit=m.unit,
            time_behavior=m.time_behavior,
            caliber=m.caliber,
            default_caliber=m.default_caliber,
            default_basis=m.default_basis,
            alternative_calibers=m.alternative_calibers or [],
            source_cas=m.source_cas or [],
            source_ifrs=m.source_ifrs,
            depends_on=m.depends_on or [],
            decompositions=m.decompositions or [],
            aliases=m.aliases or [],
            benchmark=m.benchmark,
            mpm=m.mpm,
            mpm_review=by_code[(m.collection, m.metric_code)].mpm_review or m.mpm_review,
            reconciliation=m.reconciliation,
            migrates_from=m.migrates_from,
            provenance=m.provenance,
            entry_id=str(by_code[(m.collection, m.metric_code)].id),
            status=by_code[(m.collection, m.metric_code)].status,
        )
        for m in fallback.metrics
        if (m.collection, m.metric_code) in by_code
    ]
    mappings = session.scalars(select(StatementLineMapping)).all()
    report_items = (
        [
            ReportItem(item_id=mm.item_id, cas=mm.cas_label, ifrs=mm.ifrs_label or "")
            for mm in mappings
        ]
        if mappings
        else fallback.report_items
    )
    subjects = session.scalars(select(AccountingSubject)).all()
    standards = session.scalars(select(AccountingStandard)).all()
    templates = session.scalars(select(EntryTemplate)).all()
    if not subjects:
        return fallback.model_copy(update={"metrics": metrics})
    first = entries[0]
    return MetricLibraryResponse(
        dictionary_id=first.dictionary_id,
        status="effective",
        decision_ref="D047",
        created=str(first.created_at),
        standards_scope=["CAS", "IFRS"],
        domains=fallback.domains,
        report_items=report_items,
        metrics=metrics,
        relations=fallback.relations,
        accounting=AccountingFoundation(
            dataset_id="flow.accounting_foundation.v1",
            status="effective",
            # 元数据（已知缺口/类别/取代说明）库内无列，取 YAML 权威值，不伪造为空
            known_gaps=fallback.accounting.known_gaps,
            categories=fallback.accounting.categories,
            accounts=[
                AccountingAccount(
                    code=s.code,
                    name=s.name,
                    category=s.category,
                    balance_side=s.balance_side,
                    status=s.status,
                    standard_ref=s.standard_ref,
                    code_note=s.code_note,
                    source_note=s.source_note,
                )
                for s in subjects
            ],
            superseded_notes=fallback.accounting.superseded_notes,
            standards=[
                AccountingStandardRow(
                    id=s.standard_id, name=s.name, issuer=s.issuer, note=s.note
                )
                for s in standards
            ],
            entry_templates=[
                EntryTemplateRow(
                    template_id=t.template_id,
                    scenario=t.scenario,
                    business_context=t.business_context,
                    lines=[EntryLine(**line) for line in t.lines],
                    standard_ref=t.standard_ref,
                    related_metrics=t.related_metrics or [],
                    note=t.note,
                )
                for t in templates
            ],
        ),
    )


def get_metric_library_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_metric_library_session)]


@router.get("", response_model=MetricLibraryResponse)
def get_metric_library(session: SessionDependency) -> MetricLibraryResponse:
    """只读返回指标库（数据库优先，空库回退 v1 YAML；D047 定稿）。

    每个指标附带执行绑定（C02：engine/facts/narrative 与执行器或缺失原因）。
    """
    payload = _db_payload(session) or _yaml_payload()
    bindings = {b.metric_code: b for b in build_execution_binding()}
    metrics = []
    for metric in payload.metrics:
        binding = bindings.get(metric.metric_code)
        metrics.append(
            metric.model_copy(
                update={
                    "execution_kind": binding.kind if binding else None,
                    "execution_detail": (
                        (binding.executor or binding.reason) if binding else None
                    ),
                }
            )
        )
    return payload.model_copy(update={"metrics": metrics})


class ImportRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=128)


class RetireRequest(BaseModel):
    dictionary_id: str = Field(min_length=1, max_length=64)
    actor: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=512)


@router.post("/import", response_model=dict[str, int])
def import_metric_library(
    request: ImportRequest, session: SessionDependency
) -> dict[str, int]:
    """整版幂等导入 v1 配置到数据库（受保护操作，审计留痕）。"""
    root = resolve_metric_library_root()
    summary = import_all(session, root / CONFIG_ROOT)
    session.commit()
    MetricLibraryAudit(root).append("import", request.actor, summary)
    return summary


@router.post("/retire")
def retire_metric_library(request: RetireRequest, session: SessionDependency) -> dict[str, Any]:
    """版本化退役：将指定字典全部条目置 retired（不可逆操作走新版本导入恢复）。"""
    entries = session.scalars(
        select(MetricDictionaryEntry).where(
            MetricDictionaryEntry.dictionary_id == request.dictionary_id
        )
    ).all()
    for entry in entries:
        entry.status = "retired"
    session.commit()
    summary = {"dictionary_id": request.dictionary_id, "retired": len(entries)}
    MetricLibraryAudit(resolve_metric_library_root()).append(
        "retire", request.actor, {**summary, "reason": request.reason}
    )
    return summary


__all__ = ["get_metric_library_session", "router"]


def _entry_action_response(entry: MetricDictionaryEntry) -> MetricEntryActionResponse:
    return MetricEntryActionResponse(
        id=str(entry.id),
        metric_code=entry.metric_code,
        version=entry.version,
        status=entry.status,
    )


@router.post(
    "/entries/{entry_id}/drafts",
    response_model=MetricEntryActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def draft_metric_change(
    entry_id: UUID, request: MetricDraftRequest, session: SessionDependency
) -> MetricEntryActionResponse:
    try:
        draft = MetricGovernance(session).draft_change(
            entry_id,
            changes=request.changes,
            operator=request.operator,
            reason=request.reason,
        )
    except GovernanceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorDetail(code=error.code, message=error.message).model_dump(mode="json"),
        ) from error
    session.commit()
    return _entry_action_response(draft)


@router.post("/entries/{entry_id}/activate", response_model=MetricEntryActionResponse)
def activate_metric_change(
    entry_id: UUID, request: MetricActionRequest, session: SessionDependency
) -> MetricEntryActionResponse:
    try:
        entry = MetricGovernance(session).activate(
            entry_id, operator=request.operator, reason=request.reason
        )
    except GovernanceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorDetail(code=error.code, message=error.message).model_dump(mode="json"),
        ) from error
    session.commit()
    return _entry_action_response(entry)


@router.post("/entries/{entry_id}/retire", response_model=MetricEntryActionResponse)
def retire_metric_change(
    entry_id: UUID, request: MetricActionRequest, session: SessionDependency
) -> MetricEntryActionResponse:
    try:
        entry = MetricGovernance(session).retire(
            entry_id, operator=request.operator, reason=request.reason
        )
    except GovernanceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorDetail(code=error.code, message=error.message).model_dump(mode="json"),
        ) from error
    session.commit()
    return _entry_action_response(entry)


@router.get("/events", response_model=MetricGovernanceEventListResponse)
def list_metric_governance_events(
    session: SessionDependency, metric_code: str | None = None
) -> MetricGovernanceEventListResponse:
    events = MetricGovernance(session).events(metric_code)
    return MetricGovernanceEventListResponse(
        events=[
            MetricGovernanceEventLine(
                id=str(event.id),
                metric_code=event.metric_code,
                version=event.version,
                action=event.action,
                operator=event.operator,
                reason=event.reason,
                diff=event.diff,
                created_at=(
                    event.created_at.isoformat(timespec="seconds") if event.created_at else None
                ),
            )
            for event in events
        ]
    )


@router.post(
    "/entries/{entry_id}/impact",
    response_model=MetricImpactResponse,
)
def analyze_metric_impact(
    entry_id: UUID, session: SessionDependency
) -> MetricImpactResponse:
    """草稿影响分析：下游依赖 + 取数映射 + 沙盒新旧试算（只读，不写入）。"""
    try:
        report = MetricImpactService(session).analyze(entry_id)
    except ImpactError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorDetail(code=error.code, message=error.message).model_dump(mode="json"),
        ) from error
    return MetricImpactResponse(
        metric_code=report.metric_code,
        draft_version=report.draft_version,
        downstream_metrics=list(report.downstream_metrics),
        referenced_items=list(report.referenced_items),
        frozen_snapshots_untouched=report.frozen_snapshots_untouched,
        sandbox=[
            SandboxDiffLine(
                company=diff.company,
                period=diff.period,
                current_value=diff.current_value,
                draft_value=diff.draft_value,
                delta=diff.delta,
                error=diff.error,
            )
            for diff in report.sandbox
        ],
    )
