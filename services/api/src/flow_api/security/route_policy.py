"""集中路由策略（S01 三智能体计划 Task 2B）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）。

- ROUTE_POLICY 是唯一 route→action/resource/owner 注册表（机器可读全路由 inventory）；
- 写方法（POST/PUT/PATCH/DELETE）与隐藏写 GET 必须登记 action；
  只读入口必须登记豁免理由；
- publishing/operations 两条发布 route 登记 owner=sol（pending serial wiring），
  本分支不修改这两个 route 文件；
- 路由代码不得散落角色字符串：授权一律经 authorization.authorize。

扫描器（scan_route_coverage）对最终挂载的 app.router 递归展开
（FastAPI 0.141 _IncludedRouter 懒加载），证明注册表与真实路由集合一致。
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from flow_api.api.auth import resolve_principal
from flow_api.security.audit import AuditEventInput, AuditWriter, get_audit_writer
from flow_api.security.authorization import ResourceContext, authorize
from flow_api.security.principal import Principal

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# 会冻结快照的 GET：按写入口处理（隐藏写）
HIDDEN_WRITE_GET_PATHS = frozenset(
    {
        "/api/v1/statements/{report_id}/objective-snapshot",
        "/api/v1/statements/{report_id}/objective-snapshot/html",
    }
)


@dataclass(frozen=True)
class RoutePolicyEntry:
    is_write: bool
    action: str | None = None  # None = 仅认证豁免组
    loader: str = "none"
    owner: str = "kimi-k3"
    read_only_reason: str | None = None


def _w(action: str, loader: str = "none", owner: str = "kimi-k3") -> RoutePolicyEntry:
    return RoutePolicyEntry(is_write=True, action=action, loader=loader, owner=owner)


def _r(
    reason: str, action: str | None = None, loader: str = "none", owner: str = "kimi-k3"
) -> RoutePolicyEntry:
    return RoutePolicyEntry(
        is_write=False, action=action, loader=loader, owner=owner, read_only_reason=reason
    )


_READ_MATRIX = "只读但按授权矩阵检查"
_READ_EXEMPT = "只读聚合/导航，认证即可"

ROUTE_POLICY: dict[tuple[str, str], RoutePolicyEntry] = {
    # health / workspace / dashboard / workbench：只读豁免组
    ("GET", "/api/v1/health"): _r("健康检查，无业务数据"),
    ("GET", "/api/v1/workspace"): _r(_READ_EXEMPT),
    ("GET", "/api/v1/dashboard/overview"): _r(_READ_EXEMPT),
    ("GET", "/api/v1/analysis/workbench/{report_id}"): _r(_READ_EXEMPT),
    # intake
    ("GET", "/api/v1/intake/templates/{template_id}"): _r(_READ_MATRIX, "intake:template.read"),
    ("POST", "/api/v1/intake/batches"): _w("intake:batch.create"),
    ("POST", "/api/v1/intake/batches/{batch_id}/sources"): _w("intake:source.upload", "batch"),
    ("GET", "/api/v1/intake/sources/{source_file_id}/profile"): _r(
        _READ_MATRIX, "intake:source.read", "source_file"
    ),
    ("POST", "/api/v1/intake/sources/{source_file_id}/mapping-proposals"): _w(
        "intake:mapping.propose", "source_file"
    ),
    ("POST", "/api/v1/intake/mappings/{mapping_version_id}/confirm"): _w(
        "intake:mapping.confirm", "mapping_version"
    ),
    ("POST", "/api/v1/intake/mappings/{mapping_version_id}/overrides"): _w(
        "intake:mapping.override", "mapping_version"
    ),
    ("POST", "/api/v1/intake/sources/{source_file_id}/validate"): _w(
        "intake:source.validate", "source_file"
    ),
    ("POST", "/api/v1/intake/issues/{quality_issue_id}/acknowledge"): _w(
        "intake:issue.acknowledge", "quality_issue"
    ),
    ("POST", "/api/v1/intake/imports/{import_version_id}/publish"): _w(
        "intake:import.publish", "import_version"
    ),
    ("GET", "/api/v1/intake/batches/{batch_id}/versions"): _r(
        _READ_MATRIX, "intake:batch.read", "batch"
    ),
    ("GET", "/api/v1/intake/imports/{import_version_id}/cleaning-summary"): _r(
        _READ_MATRIX, "intake:import.read", "import_version"
    ),
    ("GET", "/api/v1/intake/imports/{import_version_id}/standardized-workbook"): _r(
        _READ_MATRIX, "intake:import.read", "import_version"
    ),
    # investigations
    ("GET", "/api/v1/investigations"): _r(_READ_MATRIX, "investigation:read"),
    ("GET", "/api/v1/investigations/{finding_id}"): _r(
        _READ_MATRIX, "investigation:read", "finding"
    ),
    ("POST", "/api/v1/investigations/{finding_id}/evidence/{evidence_id}/decision"): _w(
        "investigation:evidence.decide", "finding"
    ),
    ("PUT", "/api/v1/investigations/{finding_id}/conclusion"): _w(
        "investigation:conclusion.save", "finding"
    ),
    ("POST", "/api/v1/investigations/{finding_id}/transition"): _w(
        "investigation:transition", "finding"
    ),
    # metric_library
    ("GET", "/api/v1/metric-library"): _r(_READ_MATRIX, "metric:read"),
    ("POST", "/api/v1/metric-library/import"): _w("metric:import"),
    ("POST", "/api/v1/metric-library/retire"): _w("metric:retire"),
    ("POST", "/api/v1/metric-library/entries/{entry_id}/drafts"): _w(
        "metric:rule.propose", "metric_entry"
    ),
    ("POST", "/api/v1/metric-library/entries/{entry_id}/activate"): _w(
        "metric:rule.approve", "metric_entry"
    ),
    ("POST", "/api/v1/metric-library/entries/{entry_id}/retire"): _w(
        "metric:rule.retire", "metric_entry"
    ),
    ("GET", "/api/v1/metric-library/events"): _r(_READ_MATRIX, "metric:read"),
    ("POST", "/api/v1/metric-library/entries/{entry_id}/impact"): _w(
        "metric:impact.analyze", "metric_entry"
    ),
    # statements
    ("POST", "/api/v1/statements/sources"): _w("statement:source.upload"),
    ("GET", "/api/v1/statements/sources"): _r(_READ_MATRIX, "statement:read"),
    ("GET", "/api/v1/statements"): _r(_READ_MATRIX, "statement:read"),
    ("GET", "/api/v1/statements/{report_id}"): _r(
        _READ_MATRIX, "statement:read", "statement_report"
    ),
    ("GET", "/api/v1/statements/{report_id}/projection"): _r(
        _READ_MATRIX, "statement:read", "statement_report"
    ),
    ("POST", "/api/v1/statements/{report_id}/corrections"): _w(
        "statement:correction.add", "statement_report"
    ),
    ("GET", "/api/v1/statements/{report_id}/corrections"): _r(
        _READ_MATRIX, "statement:read", "statement_report"
    ),
    ("POST", "/api/v1/statements/{report_id}/publish"): _w("statement:publish", "statement_report"),
    # objective_reports（隐藏写 GET ×2）
    ("GET", "/api/v1/statements/{report_id}/objective-snapshot"): _w(
        "statement:snapshot.freeze", "statement_report"
    ),
    ("POST", "/api/v1/statements/{report_id}/objective-snapshot"): _w(
        "statement:snapshot.freeze", "statement_report"
    ),
    ("GET", "/api/v1/statements/{report_id}/objective-snapshot/html"): _w(
        "statement:snapshot.freeze", "statement_report"
    ),
    # orchestration
    ("POST", "/api/v1/orchestration/batches/{batch_id}/build"): _w("orchestration:build", "batch"),
    ("GET", "/api/v1/orchestration/batches/{batch_id}/builds"): _r(
        _READ_MATRIX, "orchestration:read", "batch"
    ),
    ("GET", "/api/v1/orchestration/builds/{job_id}"): _r(
        _READ_MATRIX, "orchestration:read", "build_job"
    ),
    # copilot（模型边界审计点）
    ("POST", "/api/v1/copilot/investigations/{finding_id}/ask"): _w("copilot:ask", "finding"),
    ("POST", "/api/v1/copilot/explain-mapping"): _w("copilot:explain"),
    ("POST", "/api/v1/copilot/report-outline"): _w("copilot:outline"),
    # publishing（owner=sol：本分支只登记，不改 route）
    ("POST", "/api/v1/publishing/snapshots/{report_snapshot_id}/publish"): _w(
        "report:publish", "none", "sol"
    ),
    ("GET", "/api/v1/publishing/snapshots/{report_snapshot_id}/attempts"): _r(
        _READ_MATRIX, "statement:read", "none", "sol"
    ),
    ("POST", "/api/v1/publishing/snapshots"): _w("report:freeze", "none", "sol"),
    ("GET", "/api/v1/publishing/freeze-candidates"): _r(
        _READ_MATRIX, "statement:read", "none", "sol"
    ),
    ("GET", "/api/v1/publishing/snapshots"): _r(_READ_MATRIX, "statement:read", "none", "sol"),
    ("GET", "/api/v1/publishing/attempts/{attempt_id}/download"): _r(
        _READ_MATRIX, "statement:read", "none", "sol"
    ),
    # operations（owner=sol：本分支只登记，不改 route）
    ("GET", "/api/v1/operations/public-periods"): _r(
        "公开经营期间目录，无企业数据", None, "none", "sol"
    ),
    ("GET", "/api/v1/operations/public/{stock_code}/{period_label}"): _r(
        "公开经营事实只读", None, "none", "sol"
    ),
    ("GET", "/api/v1/operations/overview/{report_id}"): _r(
        _READ_MATRIX, "statement:read", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/snapshots"): _r(_READ_MATRIX, "statement:read", "none", "sol"),
    ("POST", "/api/v1/operations/overview/{report_id}/publish"): _w(
        "report:publish", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/snapshots/{snapshot_id}/attempts"): _r(
        _READ_MATRIX, "statement:read", "none", "sol"
    ),
    ("POST", "/api/v1/operations/overview/{report_id}/freeze"): _w(
        "report:freeze", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/overview/{report_id}/html"): _r(
        _READ_MATRIX, "statement:read", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/overview/{report_id}/xlsx"): _r(
        _READ_MATRIX, "statement:read", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/overview/{report_id}/pptx"): _r(
        _READ_MATRIX, "statement:read", "statement_report", "sol"
    ),
    ("GET", "/api/v1/operations/overview/{report_id}/pdf"): _r(
        _READ_MATRIX, "statement:read", "statement_report", "sol"
    ),
}


# --- 扫描器 ---


def iter_mounted_routes(router: Any) -> Iterator[tuple[str, str]]:
    """递归展开 FastAPI 0.141 的 _IncludedRouter 懒加载结构，产出 (method, 完整路径)。"""

    for route in getattr(router, "routes", []):
        if type(route).__name__ == "_IncludedRouter":
            ctx = route.include_context
            prefix = getattr(ctx, "prefix", "") or ""
            for method, path in iter_mounted_routes(route.original_router):
                yield method, prefix + path
        else:
            methods = getattr(route, "methods", None)
            if methods:
                for method in sorted(methods - {"HEAD", "OPTIONS"}):
                    yield method, route.path


@dataclass(frozen=True)
class CoverageReport:
    missing: list[tuple[str, str]] = field(default_factory=list)
    stale: list[tuple[str, str]] = field(default_factory=list)


def scan_route_coverage(router: Any) -> CoverageReport:
    """注册表与真实挂载路由的双向对账：未登记 / 失效登记都报出。"""

    mounted = {(m, p) for m, p in iter_mounted_routes(router) if p.startswith("/api/v1")}
    registered = set(ROUTE_POLICY)
    return CoverageReport(
        missing=sorted(mounted - registered),
        stale=sorted(registered - mounted),
    )


# --- resource loaders（企业归属解析；找不到实体时 fail closed） ---


def _enterprise_of_batch(session: Any, batch_id: UUID) -> UUID | None:
    from flow_api.enterprise.models import AnalysisCycle
    from flow_api.infrastructure.models.intake import AnalysisBatch

    batch = session.get(AnalysisBatch, batch_id)
    if batch is None or batch.analysis_cycle_id is None:
        return None  # legacy/public 批次：无企业边界
    cycle = session.get(AnalysisCycle, batch.analysis_cycle_id)
    return cycle.enterprise_id if cycle else None


def _load_by_batch(request: Request, kind: str, resource_id: str | None) -> ResourceContext:
    from flow_api.infrastructure.db import get_session_factory

    batch_id = UUID(request.path_params["batch_id"])
    with get_session_factory()() as session:
        return ResourceContext(kind, resource_id, _enterprise_of_batch(session, batch_id))


def _load_via(request: Request, param: str, kind: str, batch_of: Any) -> ResourceContext:
    """通用 lineage loader：实体 → batch_id → enterprise。"""

    from flow_api.infrastructure.db import get_session_factory

    raw = request.path_params.get(param)
    if raw is None:
        return ResourceContext.unscoped()
    resource_id = UUID(raw)
    with get_session_factory()() as session:
        batch_id = batch_of(session, resource_id)
        if batch_id is None:
            # 实体存在性由业务 handler 判定（404）；授权层对缺失实体 fail closed
            # 体现在企业边界无法证明时按无边界资源处理，由动作矩阵兜底。
            return ResourceContext(kind, str(resource_id), None)
        return ResourceContext(kind, str(resource_id), _enterprise_of_batch(session, batch_id))


def _batch_of_import_version(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.intake import ImportVersion

    obj = session.get(ImportVersion, rid)
    return obj.batch_id if obj else None


def _batch_of_source_file(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.intake import SourceFile

    obj = session.get(SourceFile, rid)
    return obj.batch_id if obj else None


def _batch_of_mapping_version(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.intake import MappingVersion

    obj = session.get(MappingVersion, rid)
    return obj.batch_id if obj else None


def _batch_of_quality_issue(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.intake import QualityIssue

    obj = session.get(QualityIssue, rid)
    if obj is None:
        return None
    return _batch_of_import_version(session, obj.import_version_id)


def _batch_of_finding(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot

    finding = session.get(Finding, rid)
    if finding is None:
        return None
    snapshot = session.get(MetricSnapshot, finding.metric_snapshot_id)
    return snapshot.batch_id if snapshot else None


def _batch_of_build_job(session: Any, rid: UUID) -> UUID | None:
    from flow_api.infrastructure.models.intake import BuildJob

    obj = session.get(BuildJob, rid)
    return obj.batch_id if obj else None


def _load_metric_entry(request: Request) -> ResourceContext:
    """指标条目：平台级资源（无企业边界），但携带最近提议者用于不可自批判定。"""

    from sqlalchemy import select

    from flow_api.infrastructure.db import get_session_factory
    from flow_api.infrastructure.models.metric_library import (
        MetricDictionaryEntry,
        MetricGovernanceEvent,
    )

    raw = request.path_params.get("entry_id")
    if raw is None:
        return ResourceContext.unscoped()
    entry_id = UUID(raw)
    attributes: dict[str, str] = {}
    with get_session_factory()() as session:
        entry = session.get(MetricDictionaryEntry, entry_id)
        if entry is not None:
            # 治理事件按 dictionary_id + metric_code + version 关联条目，
            # 取当前版本最近一条 draft 事件的 operator 作为提议者
            latest_draft = session.execute(
                select(MetricGovernanceEvent)
                .where(
                    MetricGovernanceEvent.dictionary_id == entry.dictionary_id,
                    MetricGovernanceEvent.metric_code == entry.metric_code,
                    MetricGovernanceEvent.version == entry.version,
                    MetricGovernanceEvent.action == "draft",
                )
                .order_by(MetricGovernanceEvent.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if latest_draft is not None:
                attributes["proposed_by"] = latest_draft.operator
    return ResourceContext("metric_entry", str(entry_id), None, attributes)


LOADERS: dict[str, Callable[[Request], ResourceContext]] = {
    "none": lambda request: ResourceContext.unscoped(),
    "batch": lambda request: _load_by_batch(request, "batch", request.path_params.get("batch_id")),
    "import_version": lambda request: _load_via(
        request, "import_version_id", "import_version", _batch_of_import_version
    ),
    "source_file": lambda request: _load_via(
        request, "source_file_id", "source_file", _batch_of_source_file
    ),
    "mapping_version": lambda request: _load_via(
        request, "mapping_version_id", "mapping_version", _batch_of_mapping_version
    ),
    "quality_issue": lambda request: _load_via(
        request, "quality_issue_id", "quality_issue", _batch_of_quality_issue
    ),
    "finding": lambda request: _load_via(request, "finding_id", "finding", _batch_of_finding),
    "build_job": lambda request: _load_via(request, "job_id", "build_job", _batch_of_build_job),
    "statement_report": lambda request: ResourceContext(
        "statement_report", request.path_params.get("report_id"), None
    ),  # 公开财报：公开范围，无企业边界
    "metric_entry": _load_metric_entry,
}


# --- 依赖 ---

_TEMPLATE_RE: dict[str, re.Pattern[str]] = {}


def _match_path(template: str, actual: str) -> bool:
    pattern = _TEMPLATE_RE.get(template)
    if pattern is None:
        pattern = re.compile("^" + re.sub(r"\{[^}]+\}", r"[^/]+", template) + "$")
        _TEMPLATE_RE[template] = pattern
    return bool(pattern.match(actual))


def resolve_policy_entry(method: str, path: str) -> RoutePolicyEntry | None:
    """按 method + 实际路径解析注册条目（模板匹配，不依赖 request.scope['route']）。"""

    entry = ROUTE_POLICY.get((method, path))
    if entry is not None:
        return entry
    for (m, template), candidate in ROUTE_POLICY.items():
        if m == method and "{" in template and _match_path(template, path):
            return candidate
    return None


async def load_resource_context(request: Request) -> ResourceContext:
    """按注册表 loader 解析资源上下文（独立依赖，测试可 override）。"""

    entry = resolve_policy_entry(request.method, request.url.path)
    if entry is None or entry.loader == "none":
        return ResourceContext.unscoped()
    return LOADERS[entry.loader](request)


def _record_decision(
    audit: AuditWriter,
    principal: Principal,
    action: str,
    resource: ResourceContext,
    decision: Any,
) -> None:
    audit.record(
        AuditEventInput(
            event_type="authz.decision",
            actor_id=principal.actor_id,
            role=str(principal.role),
            enterprise_id=principal.enterprise_id,
            action=action,
            resource_kind=resource.kind,
            resource_id=resource.resource_id,
            decision="allow" if decision.allowed else "deny",
            reason=decision.reason,
            correlation_id="",
            model_boundary=None,
            created_at=datetime.now(UTC),
        )
    )


def _forbidden(reason: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "forbidden", "message": reason},
    )


def require_action(action: str) -> Callable[..., Awaitable[None]]:
    """动作级授权依赖（测试与直接接线用）；allow/deny 都写审计事件。"""

    async def _dependency(
        principal: Annotated[Principal, Depends(resolve_principal)],
        resource: Annotated[ResourceContext, Depends(load_resource_context)],
        audit: Annotated[AuditWriter, Depends(get_audit_writer)],
    ) -> None:
        decision = authorize(principal, action, resource)
        _record_decision(audit, principal, action, resource, decision)
        if not decision.allowed:
            raise _forbidden(decision.reason)

    return _dependency


async def enforce_route_policy(
    request: Request,
    principal: Annotated[Principal, Depends(resolve_principal)],
    resource: Annotated[ResourceContext, Depends(load_resource_context)],
    audit: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> None:
    """路由级统一入口（挂进敏感路由的 APIRouter dependencies）。

    - 未登记的 /api/v1 路由 fail closed（403），health 除外；
    - 只读豁免组（action 为 None）直接放行，认证由 router 层 require_bearer_auth 保证；
    - 其余按注册表 action 走 authorize，allow/deny 均写审计。
    """

    path = request.url.path
    entry = resolve_policy_entry(request.method, path)
    if entry is None:
        if path.startswith("/api/v1") and path != "/api/v1/health":
            raise _forbidden(f"路由 {request.method} {path} 未登记安全策略（fail closed）")
        return
    if entry.action is None:
        return
    decision = authorize(principal, entry.action, resource)
    _record_decision(audit, principal, entry.action, resource, decision)
    if not decision.allowed:
        raise _forbidden(decision.reason)


__all__ = [
    "HIDDEN_WRITE_GET_PATHS",
    "LOADERS",
    "ROUTE_POLICY",
    "WRITE_METHODS",
    "CoverageReport",
    "RoutePolicyEntry",
    "enforce_route_policy",
    "iter_mounted_routes",
    "load_resource_context",
    "require_action",
    "resolve_policy_entry",
    "scan_route_coverage",
]
