"""Route policy：路由策略注册表、加载器与授权依赖（S01 Task 2B 重做）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）§4/§5/§6/§9。
权威清单：docs/40_specs/security/route-inventory-v1.tsv（64 条，最终 api_router 挂载）。

纪律：
- TSV 是唯一 route→action/loader/owner 真相；加载即校验（§5 合并阻断项全部在此 fail-fast）；
- 双向一致性用 `app.openapi()` 强制展开探针核验（`_IncludedRouter` 懒挂载是
  `app.routes` 迭代盲区，GLM 独立复审 P3-② 已收编为红灯测试）；
- loader 只允许 SELECT（autoflush 关闭），不得 commit/写审计/调用模型/访问对象存储；
- `blocked:*` 条目无条件 deny ROUTE_BLOCKED，永不进入 handler；
- loader 无法解析 lineage（legacy/断裂）→ deny RESOURCE_SCOPE_UNRESOLVED（§4.1）；
- 授权/审计 actor 只来自 Principal；body 身份字段一律不得进入（§3.3）。

集成边界（Task 2A 后半段落地前）：
- Principal 解析由 `flow_api.api.auth.resolve_principal` 提供（0026/RoleBinding 车道），
  本模块经 `PRINCIPAL_DEP` 单符号引用，集成时替换实现，测试用 dependency_overrides；
- durable AuditWriter 由 0026 车道注册（`register_audit_writer`）；未注册时
  默认 writer 抛 AuditUnavailable → 503（§6 fail closed，不静默放行）；
- correlation_id 从 request.state 读取（§9 middleware 车道落地前缺省 ""，
  集成后由 middleware 保证存在且五处一致）。
"""

from __future__ import annotations

import csv
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from flow_api.api.auth import require_bearer_auth
from flow_api.security.audit import (
    AuditContext,
    AuditUnavailable,
    AuditWriter,
    get_audit_writer,
    register_audit_writer,
)
from flow_api.security.authorization import Action, Decision, ReasonCode, ResourceRef, authorize
from flow_api.security.principal import Principal

# ---------------------------------------------------------------------------
# §5 policy 注册表（TSV 权威）
# ---------------------------------------------------------------------------

# 容器/仓库双布局：镜像内 TSV 烤在 /app/config/security/，仓库内按相对路径。
# 禁止模块级 parents[N]——容器内层级变短会 IndexError（R1 smoke 教训）。
_CONTAINER_TSV = Path("/app/config/security/route-inventory-v1.tsv")


def _find_tsv() -> Path:
    override = os.environ.get("FLOW_ROUTE_INVENTORY_TSV")
    if override:
        return Path(override)
    probe = Path(__file__).resolve()
    for candidate in probe.parents:
        hit = candidate / "docs" / "40_specs" / "security" / "route-inventory-v1.tsv"
        if hit.is_file():
            return hit
    if _CONTAINER_TSV.is_file():
        return _CONTAINER_TSV
    return Path("docs/40_specs/security/route-inventory-v1.tsv")


TSV_PATH = _find_tsv()

_TSV_COLUMNS = (
    "method",
    "path",
    "actual_side_effect",
    "action",
    "resource_loader",
    "owner",
    "exemption_reason",
)

# actual_side_effect 中的写语义前缀；带这些前缀的条目必须有 action 且不得有豁免理由
_WRITE_SIDE_EFFECT_PREFIXES = ("database_write", "object_store_write", "model_call")

# exemption_reason 中构成「只读豁免」的前缀家族——写在写副作用条目上即合并阻断（§5）。
# 其余豁免值（request_*_untrusted、hard_coded_*、four_stage_serial_wiring_required、
# hidden_write_get_*）是偏差注记，允许出现在写入口。
_READ_ONLY_EXEMPTION_PREFIXES = (
    "read_only_",
    "anonymous_public_",
)

# loader -> ResourceRef.resource_type（loader 输出契约；step3 精确组合的另一半）
LOADER_RESOURCE_TYPE: dict[str, str] = {
    "load_blocked_entry": "route",
    "load_public_metric_library": "metric_library",
    "load_single_enterprise": "enterprise_scope",
    "load_default_cycle_create": "enterprise_scope",
    "load_public_health": "health",
    "load_public_workspace_metadata": "workspace_metadata",
    "load_public_module_catalog": "module_catalog",
    "load_public_metric_coverage": "metric_coverage",
    "load_public_intake_template": "intake_template",
    "load_batch_scope_or_deny_legacy": "analysis_batch",
    "load_batch_scope_owner_or_deny_legacy": "analysis_batch",
    "load_body_batch_scope_or_deny_legacy": "analysis_batch",
    "load_source_batch_scope_or_deny_legacy": "source_file",
    "load_source_batch_scope_owner_or_deny_legacy": "source_file",
    "load_mapping_batch_scope_owner_or_deny_legacy": "mapping_version",
    "load_import_batch_scope_or_deny_legacy": "import_version",
    "load_import_batch_scope_owner_or_deny_legacy": "import_version",
    "load_body_import_batch_scope_or_deny_legacy": "import_version",
    "load_issue_batch_scope_owner_or_deny_legacy": "quality_issue",
    "load_finding_batch_scope_or_deny_legacy": "finding",
    "load_finding_batch_scope_owner_or_deny_legacy": "finding",
    "load_finding_evidence_batch_scope_or_deny_legacy": "finding",
    "load_body_metric_snapshot_batch_scope_or_deny_legacy": "metric_snapshot",
    "load_build_job_batch_scope_or_deny_legacy": "build_job",
    "load_public_statement_report": "statement_report",
    "load_public_statement_report_collection": "statement_report_collection",
    "load_public_statement_source_collection": "statement_source_collection",
    "load_report_snapshot_batch_scope_or_deny_legacy": "report_snapshot",
    "load_attempt_parent_scope_or_deny_legacy": "publication_attempt",
    "load_public_operations_catalog": "operations_catalog",
    "load_public_operations_disclosure": "operations_disclosure",
    "load_public_operations_snapshot": "operations_snapshot",
    "load_public_operations_snapshot_collection": "operations_snapshot_collection",
}


@dataclass(frozen=True)
class PolicyEntry:
    method: str
    path: str
    actual_side_effect: str
    action: Action | None  # None = 只读豁免组（ exemption_reason 必有值）
    resource_loader: str  # load_* 或 blocked:<原因>
    owner: str
    exemption_reason: str | None

    @property
    def is_blocked(self) -> bool:
        return self.resource_loader.startswith("blocked:")

    @property
    def is_write(self) -> bool:
        return self.actual_side_effect.startswith(_WRITE_SIDE_EFFECT_PREFIXES)


class PolicyValidationError(RuntimeError):
    """policy 装载校验失败（§5 合并阻断项）——启动 fail-fast。"""


def load_policy(path: Path = TSV_PATH) -> tuple[PolicyEntry, ...]:
    """从 TSV 权威清单装载 policy；任何不一致 fail-fast（§5）。条目按 (path, method) 排序。"""

    if not path.is_file():
        raise PolicyValidationError(f"route inventory 缺失：{path}")
    entries: list[PolicyEntry] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if tuple(reader.fieldnames or ()) != _TSV_COLUMNS:
            raise PolicyValidationError(f"TSV 列头必须为 {_TSV_COLUMNS}，实际 {reader.fieldnames}")
        for row in reader:
            entries.append(_parse_row(row))
    return tuple(sorted(_validate(entries), key=lambda e: (e.path, e.method)))


def _parse_row(row: dict[str, str]) -> PolicyEntry:
    raw_action = (row["action"] or "").strip()
    action: Action | None = None
    if raw_action and raw_action != "-":
        try:
            action = Action(raw_action)
        except ValueError as exc:
            raise PolicyValidationError(
                f"未知 Action：{raw_action!r}（{row['method']} {row['path']}）"
            ) from exc
    exemption = (row["exemption_reason"] or "").strip() or None
    if exemption == "-":
        exemption = None
    return PolicyEntry(
        method=row["method"].strip().upper(),
        path=row["path"].strip(),
        actual_side_effect=row["actual_side_effect"].strip(),
        action=action,
        resource_loader=row["resource_loader"].strip(),
        owner=row["owner"].strip(),
        exemption_reason=exemption,
    )


def _validate(entries: list[PolicyEntry]) -> list[PolicyEntry]:
    seen: set[tuple[str, str]] = set()
    for e in entries:
        key = (e.method, e.path)
        if key in seen:
            raise PolicyValidationError(f"重复 method/path：{e.method} {e.path}")
        seen.add(key)
        if not e.is_blocked and e.resource_loader not in LOADER_RESOURCE_TYPE:
            raise PolicyValidationError(
                f"未知 loader：{e.resource_loader!r}（{e.method} {e.path}）"
            )
        if e.is_blocked and e.action is None:
            raise PolicyValidationError(f"blocked 入口缺少 action：{e.method} {e.path}")
        if e.is_write:
            # 写副作用必须登记 action，且不得被标为只读豁免（规格合并阻断条件）。
            # 注意 exemption_reason 是双义的：写入口上允许携带偏差注记
            # （request_*_untrusted、hard_coded_*、four_stage_serial_wiring_required 等），
            # 只有「只读豁免」家族的注解才构成阻断。
            if e.action is None:
                raise PolicyValidationError(f"写入口缺少 action：{e.method} {e.path}")
            if e.exemption_reason and e.exemption_reason.startswith(_READ_ONLY_EXEMPTION_PREFIXES):
                raise PolicyValidationError(
                    f"写副作用被标只读豁免：{e.method} {e.path}（{e.exemption_reason}）"
                )
        else:
            # 纯只读副作用：要么有 action（仍需角色检查），要么有豁免理由
            if e.action is None and not e.exemption_reason:
                raise PolicyValidationError(f"只读入口缺少豁免理由：{e.method} {e.path}")
    return entries


# ---------------------------------------------------------------------------
# 双向一致性扫描（GLM 探针：app.openapi() 强制展开懒挂载）
# ---------------------------------------------------------------------------


def iter_openapi_routes(app: Any) -> Iterator[tuple[str, str]]:
    """经 `app.openapi()` 展开最终挂载路由，产出 (method, path)。

    `app.routes` 迭代在 FastAPI 0.141 `_IncludedRouter` 懒挂载下只能看到占位，
    openapi() 生成时会强制物化全部 APIRoute——这是 GLM 复审确认的可靠探针。
    """

    schema = app.openapi()
    for path, methods in sorted(schema.get("paths", {}).items()):
        for method in sorted(methods):
            yield method.upper(), path


@dataclass(frozen=True)
class CoverageReport:
    missing: tuple[tuple[str, str], ...]  # 已挂载但 TSV 未登记
    stale: tuple[tuple[str, str], ...]  # TSV 登记但未挂载（扣除 PENDING_MOUNT）


# 已批准但尚未合并挂载的路由——登记先行，挂载随对应车道分支合并落地。
# 移除条件：codex/s01-module-boundaries 合并进集成分支后，把对应条目从这里删掉；
# 若届时路由仍未挂载，双向核验会重新变红（这正是设计意图）。
PENDING_MOUNT_ROUTES: frozenset[tuple[str, str]] = frozenset()


def scan_two_way(app: Any, entries: tuple[PolicyEntry, ...]) -> CoverageReport:
    mounted = {(m, p) for m, p in iter_openapi_routes(app) if p.startswith("/api/v1")}
    registered = {(e.method, e.path) for e in entries}
    return CoverageReport(
        missing=tuple(sorted(mounted - registered)),
        stale=tuple(sorted((registered - mounted) - PENDING_MOUNT_ROUTES)),
    )


# ---------------------------------------------------------------------------
# loader 基础件（SELECT-only；lineage 断裂 → ResourceScopeUnresolved）
# ---------------------------------------------------------------------------


class ResourceScopeUnresolved(RuntimeError):
    """loader 无法解析 scope/enterprise（legacy 或断裂 lineage）→ deny（§4.1）。"""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(f"{resource_type}/{resource_id} lineage 无法解析")
        self.resource_type = resource_type
        self.resource_id = resource_id


def _enterprise_of_batch(session: Session, batch_id: UUID) -> UUID:
    from flow_api.infrastructure.models.intake import AnalysisBatch

    batch = session.get(AnalysisBatch, batch_id)
    if batch is None:
        raise ResourceScopeUnresolved("analysis_batch", str(batch_id))
    if batch.analysis_cycle_id is None:
        # legacy/public 批次：无企业链（§4.1 不得借 Principal 猜测）
        raise ResourceScopeUnresolved("analysis_batch", str(batch_id))
    from flow_api.enterprise.models import AnalysisCycle

    cycle = session.get(AnalysisCycle, batch.analysis_cycle_id)
    if cycle is None:
        raise ResourceScopeUnresolved("analysis_batch", str(batch_id))
    return cycle.enterprise_id


def _batch_scope_ref(
    session: Session,
    resource_type: str,
    resource_id: str,
    batch_id: UUID,
    owner_actor_id: str | None = None,
) -> ResourceRef:
    from flow_api.infrastructure.models.intake import AnalysisBatch

    batch = session.get(AnalysisBatch, batch_id)
    owner = owner_actor_id or (batch.created_by if batch is not None else None)
    return ResourceRef(
        scope="enterprise",
        resource_type=resource_type,
        resource_id=resource_id,
        enterprise_id=_enterprise_of_batch(session, batch_id),
        owner_actor_id=owner,
        proposed_by_actor_id=None,
    )


def _public_ref(resource_type: str, resource_id: str) -> ResourceRef:
    return ResourceRef(
        scope="public",
        resource_type=resource_type,
        resource_id=resource_id,
        enterprise_id=None,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )


def _load_single_enterprise(request: Request, session: Session) -> ResourceRef:
    """bootstrap 单租户语义：库内 analysis_cycle 企业唯一 → 该企业；多企业/无企业 → deny。"""

    from sqlalchemy import text

    enterprises = [
        r[0]
        for r in session.execute(
            text("SELECT DISTINCT enterprise_id FROM analysis_cycle")
        ).all()
    ]
    if len(enterprises) != 1 or enterprises[0] is None:
        raise ResourceScopeUnresolved("enterprise_scope", "ambiguous_or_missing")
    return ResourceRef(
        scope="enterprise",
        resource_type="enterprise_scope",
        resource_id=str(enterprises[0]),
        enterprise_id=enterprises[0],
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )


def _load_default_cycle_create(request: Request, session: Session) -> ResourceRef:
    """create 类动作：owner 由服务层落列（created_by），此处只锚定企业。"""

    return _load_single_enterprise(request, session)


def _load_public_metric_library(request: Request, session: Session) -> ResourceRef:
    """全局参考字典（准则/科目/分录模板）只读：public 参考数据（§4.1）。"""

    return _public_ref("metric_library", "dictionary")


def _load_blocked_entry(request: Request, session: Session) -> ResourceRef:
    """blocked 条目的占位 loader：require_action 在 entry 解析阶段即 deny，永不调用。"""

    return _public_ref("route", f"{request.method} {request.url.path}")


def _path_uuid(request: Request, name: str) -> UUID:
    raw = request.path_params.get(name)
    if raw is None:
        raise ResourceScopeUnresolved("unknown", f"missing path param {name}")
    return UUID(str(raw))


def _body_uuid(request: Request, name: str) -> UUID:
    """body loader 的输入由 require_action 预读进 request.state.policy_body（§5 loader 同步签名）。"""  # noqa: E501

    body = getattr(request.state, "policy_body", None)
    if not isinstance(body, dict) or name not in body:
        raise ResourceScopeUnresolved("request_body", f"missing body field {name}")
    return UUID(str(body[name]))


# --- 通用 lineage 解析（实体 → batch_id） ---


def _batch_of(session: Session, model: Any, rid: UUID, resource_type: str) -> UUID:
    obj = session.get(model, rid)
    if obj is None or getattr(obj, "batch_id", None) is None:
        raise ResourceScopeUnresolved(resource_type, str(rid))
    return cast(UUID, obj.batch_id)


def _load_by_batch_param(resource_type: str) -> ResourceLoader:
    def load(request: Request, session: Session) -> ResourceRef:
        batch_id = _path_uuid(request, "batch_id")
        return _batch_scope_ref(session, resource_type, str(batch_id), batch_id)

    return load


def _load_via_model(
    param: str, resource_type: str, model: Any
) -> ResourceLoader:
    def load(request: Request, session: Session) -> ResourceRef:
        rid = _path_uuid(request, param)
        batch_id = _batch_of(session, model, rid, resource_type)
        return _batch_scope_ref(session, resource_type, str(rid), batch_id)

    return load


def _load_source_file(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import SourceFile

    rid = _path_uuid(request, "source_file_id")
    batch_id = _batch_of(session, SourceFile, rid, "source_file")
    return _batch_scope_ref(session, "source_file", str(rid), batch_id)


def _load_mapping_version(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import MappingVersion

    rid = _path_uuid(request, "mapping_version_id")
    batch_id = _batch_of(session, MappingVersion, rid, "mapping_version")
    return _batch_scope_ref(session, "mapping_version", str(rid), batch_id)


def _load_import_version(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import ImportVersion

    rid = _path_uuid(request, "import_version_id")
    batch_id = _batch_of(session, ImportVersion, rid, "import_version")
    return _batch_scope_ref(session, "import_version", str(rid), batch_id)


def _load_quality_issue(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import ImportVersion, QualityIssue

    rid = _path_uuid(request, "quality_issue_id")
    issue = session.get(QualityIssue, rid)
    if issue is None:
        raise ResourceScopeUnresolved("quality_issue", str(rid))
    batch_id = _batch_of(session, ImportVersion, issue.import_version_id, "quality_issue")
    return _batch_scope_ref(session, "quality_issue", str(rid), batch_id)


def _load_finding(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot

    rid = _path_uuid(request, "finding_id")
    finding = session.get(Finding, rid)
    if finding is None:
        raise ResourceScopeUnresolved("finding", str(rid))
    snapshot = session.get(MetricSnapshot, finding.metric_snapshot_id)
    if snapshot is None or snapshot.batch_id is None:
        raise ResourceScopeUnresolved("finding", str(rid))
    return _batch_scope_ref(session, "finding", str(rid), snapshot.batch_id)


def _load_build_job(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import BuildJob

    rid = _path_uuid(request, "job_id")
    batch_id = _batch_of(session, BuildJob, rid, "build_job")
    return _batch_scope_ref(session, "build_job", str(rid), batch_id)


def _load_report_snapshot(request: Request, session: Session) -> ResourceRef:
    # lineage：report_snapshot → metric_snapshot → batch → cycle → enterprise
    from flow_api.infrastructure.models.analytics import MetricSnapshot
    from flow_api.infrastructure.models.publishing import ReportSnapshot

    rid = _path_uuid(request, "report_snapshot_id")
    obj = session.get(ReportSnapshot, rid)
    if obj is None:
        raise ResourceScopeUnresolved("report_snapshot", str(rid))
    snapshot = session.get(MetricSnapshot, obj.metric_snapshot_id)
    if snapshot is None or snapshot.batch_id is None:
        raise ResourceScopeUnresolved("report_snapshot", str(rid))
    return _batch_scope_ref(session, "report_snapshot", str(rid), snapshot.batch_id)


def _load_attempt(request: Request, session: Session) -> ResourceRef:
    # lineage 二选一（CHECK num_nonnulls=1）：
    #   report_snapshot → metric_snapshot → batch（enterprise）
    #   objective_report_snapshot → statement_report（public 公开财报）
    from flow_api.infrastructure.models.analytics import MetricSnapshot
    from flow_api.infrastructure.models.publishing import PublicationAttempt, ReportSnapshot
    from flow_api.publishing.objective_freeze import ObjectiveReportSnapshot

    rid = _path_uuid(request, "attempt_id")
    obj = session.get(PublicationAttempt, rid)
    if obj is None:
        raise ResourceScopeUnresolved("publication_attempt", str(rid))
    if obj.report_snapshot_id is not None:
        snap = session.get(ReportSnapshot, obj.report_snapshot_id)
        if snap is None:
            raise ResourceScopeUnresolved("publication_attempt", str(rid))
        metric_snapshot = session.get(MetricSnapshot, snap.metric_snapshot_id)
        if metric_snapshot is None or metric_snapshot.batch_id is None:
            raise ResourceScopeUnresolved("publication_attempt", str(rid))
        return _batch_scope_ref(session, "publication_attempt", str(rid), metric_snapshot.batch_id)
    objective = session.get(ObjectiveReportSnapshot, obj.objective_report_snapshot_id)
    if objective is None:
        raise ResourceScopeUnresolved("publication_attempt", str(rid))
    # 公开财报快照的发布产物：跟随 statement_report 的 public scope
    return _public_ref("publication_attempt", str(rid))


# --- body loaders（copilot / publishing freeze） ---


def _load_body_batch(request: Request, session: Session) -> ResourceRef:
    batch_id = _body_uuid(request, "batch_id")
    return _batch_scope_ref(session, "analysis_batch", str(batch_id), batch_id)


def _load_body_import(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.intake import ImportVersion

    rid = _body_uuid(request, "import_version_id")
    batch_id = _batch_of(session, ImportVersion, rid, "import_version")
    return _batch_scope_ref(session, "import_version", str(rid), batch_id)


def _load_body_metric_snapshot(request: Request, session: Session) -> ResourceRef:
    from flow_api.infrastructure.models.analytics import MetricSnapshot

    rid = _body_uuid(request, "metric_snapshot_id")
    snapshot = session.get(MetricSnapshot, rid)
    if snapshot is None or snapshot.batch_id is None:
        raise ResourceScopeUnresolved("metric_snapshot", str(rid))
    return _batch_scope_ref(session, "metric_snapshot", str(rid), snapshot.batch_id)


# --- public loaders（公开财报/目录；无企业边界） ---


def _public_path(resource_type: str, param: str) -> ResourceLoader:
    def load(request: Request, session: Session) -> ResourceRef:
        raw = request.path_params.get(param)
        return _public_ref(resource_type, str(raw) if raw is not None else "collection")

    return load


LOADERS: dict[str, ResourceLoader] = {
    "load_public_health": lambda request, session: _public_ref("health", "live"),
    "load_public_workspace_metadata": lambda request, session: _public_ref(
        "workspace_metadata", "static"
    ),
    "load_public_module_catalog": lambda request, session: _public_ref(
        "module_catalog", "catalog"
    ),
    "load_public_metric_coverage": lambda request, session: _public_ref(
        "metric_coverage", "static"
    ),
    "load_public_intake_template": _public_path("intake_template", "template_id"),
    "load_batch_scope_or_deny_legacy": _load_by_batch_param("analysis_batch"),
    "load_batch_scope_owner_or_deny_legacy": _load_by_batch_param("analysis_batch"),
    "load_source_batch_scope_or_deny_legacy": _load_source_file,
    "load_source_batch_scope_owner_or_deny_legacy": _load_source_file,
    "load_mapping_batch_scope_owner_or_deny_legacy": _load_mapping_version,
    "load_import_batch_scope_or_deny_legacy": _load_import_version,
    "load_import_batch_scope_owner_or_deny_legacy": _load_import_version,
    "load_issue_batch_scope_owner_or_deny_legacy": _load_quality_issue,
    "load_finding_batch_scope_or_deny_legacy": _load_finding,
    "load_finding_batch_scope_owner_or_deny_legacy": _load_finding,
    "load_finding_evidence_batch_scope_or_deny_legacy": _load_finding,
    "load_build_job_batch_scope_or_deny_legacy": _load_build_job,
    "load_body_batch_scope_or_deny_legacy": _load_body_batch,
    "load_body_import_batch_scope_or_deny_legacy": _load_body_import,
    "load_body_metric_snapshot_batch_scope_or_deny_legacy": _load_body_metric_snapshot,
    "load_report_snapshot_batch_scope_or_deny_legacy": _load_report_snapshot,
    "load_attempt_parent_scope_or_deny_legacy": _load_attempt,
    "load_public_statement_report": _public_path("statement_report", "report_id"),
    "load_public_statement_report_collection": lambda request, session: _public_ref(
        "statement_report_collection", "collection"
    ),
    "load_public_statement_source_collection": lambda request, session: _public_ref(
        "statement_source_collection", "collection"
    ),
    "load_public_operations_catalog": lambda request, session: _public_ref(
        "operations_catalog", "collection"
    ),
    "load_public_operations_disclosure": lambda request, session: _public_ref(
        "operations_disclosure",
        f"{request.path_params.get('stock_code', '')}/"
        f"{request.path_params.get('period_label', '')}",
    ),
    "load_public_operations_snapshot": _public_path("operations_snapshot", "snapshot_id"),
    "load_public_operations_snapshot_collection": lambda request, session: _public_ref(
        "operations_snapshot_collection", "collection"
    ),
    "load_public_metric_library": _load_public_metric_library,
    "load_blocked_entry": _load_blocked_entry,
    "load_single_enterprise": _load_single_enterprise,
    "load_default_cycle_create": _load_default_cycle_create,
}


def _validate_loaders_registered(entries: tuple[PolicyEntry, ...]) -> None:
    for e in entries:
        if e.is_blocked:
            continue
        if e.resource_loader not in LOADERS:
            raise PolicyValidationError(
                f"loader 未实现：{e.resource_loader}（{e.method} {e.path}）"
            )


# ---------------------------------------------------------------------------
# §5 require_action 与依赖注入点
# ---------------------------------------------------------------------------

ResourceLoader = Callable[[Request, Session], ResourceRef]


def get_readonly_session() -> Iterator[Session]:
    """授权 loader 专用只读 Session：禁用 autoflush，绝不 commit（§5）。"""

    from flow_api.infrastructure.db import get_session_factory

    factory = get_session_factory()
    session = factory()
    session.autoflush = False
    try:
        yield session
    finally:
        session.close()


# FastAPI Depends 单符号引用点（§3 credential → Principal）。
# Task 2A 后半段已交付 flow_api.api.auth.require_bearer_auth
# （resolve_principal + RoleBinding + legacy bearer 截止），本符号即真实接线；
# 测试经 dependency_overrides 注入假 Principal，不触碰全局状态。
PRINCIPAL_DEP: Callable[..., Any] = require_bearer_auth

_POLICY: tuple[PolicyEntry, ...] | None = None
_TEMPLATE_RE: dict[str, Any] = {}


def get_policy() -> tuple[PolicyEntry, ...]:
    """延迟装载 + 缓存；装载失败即启动失败（§10 inventory 装载 fail-fast）。"""

    global _POLICY
    if _POLICY is None:
        entries = load_policy()
        _validate_loaders_registered(entries)
        _POLICY = entries
    return _POLICY


def _match_path(template: str, actual: str) -> bool:
    import re

    pattern = _TEMPLATE_RE.get(template)
    if pattern is None:
        pattern = re.compile("^" + re.sub(r"\{[^}]+\}", r"[^/]+", template) + "$")
        _TEMPLATE_RE[template] = pattern
    return bool(pattern.match(actual))


def resolve_entry(method: str, path: str) -> PolicyEntry | None:
    for e in get_policy():
        if e.method == method and e.path == path:
            return e
    for e in get_policy():
        if e.method == method and "{" in e.path and _match_path(e.path, path):
            return e
    return None


def _http_error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status, detail={"code": code, "message": message}
    )


_IDENTITY_BODY_FIELDS = ("actor", "actor_id", "operator", "reviewer", "approved_by")


def _identity_fields_present(request: Request) -> bool:
    """§3.3：body/query 是否携带身份字段（只记存在标记，值不进审计）。"""

    body = getattr(request.state, "policy_body", None)
    if isinstance(body, dict) and any(f in body for f in _IDENTITY_BODY_FIELDS):
        return True
    return any(f in request.query_params for f in _IDENTITY_BODY_FIELDS)


def _identity_conflict(request: Request, principal: Principal) -> bool:
    """§3.3：body 身份字段与 Principal 冲突才 409；相同值仅忽略。"""

    body = getattr(request.state, "policy_body", None)
    if isinstance(body, dict):
        for field in ("actor", "actor_id", "operator", "reviewer", "approved_by"):
            if field in body and body[field] != principal.actor_id:
                return True
        if "enterprise_id" in body:
            body_enterprise = str(body["enterprise_id"])
            principal_enterprise = str(principal.enterprise_id)
            if body_enterprise != principal_enterprise:
                return True
    return False


def require_action(
    action: Action,
    resource_loader: ResourceLoader,
    session_provider: Callable[[], Any] | None = None,
) -> Callable[..., Any]:
    """§5 授权依赖工厂：返回 AuthorizationDependency。

    执行顺序（§4.2 + §6）：
    1. entry 解析（未登记 / blocked → 403，handler 永不执行）；
    2. loader 只读解析 ResourceRef（lineage 断裂 → 403 resource_scope_unresolved）；
    3. step3 精确组合：entry.action × loader 声明 resource_type 与入参一致；
    4. authorize 纯函数判定；
    5. 决策审计 durable（失败 → 503 audit_unavailable，handler 不执行）；
    6. deny → 403（reason_code 即 deny code）；allow → 返回 AuthorizationContext。
    """

    session_dep = session_provider or get_readonly_session

    # 注意：不使用 Annotated 字符串注解——`from __future__ import annotations`
    # 会把闭包变量 session_dep 变成不可解析的 ForwardRef，FastAPI 会把 session
    # 误判为 query 参数。Depends 放在默认值位置（定义时求值）。
    async def _dependency(
        request: Request,
        principal: Principal = Depends(PRINCIPAL_DEP),  # noqa: B008
        session: Session = Depends(session_dep),  # noqa: B008
        audit: AuditWriter = Depends(get_audit_writer),  # noqa: B008
    ) -> AuthorizationContext:
        correlation_id = getattr(request.state, "correlation_id", "")
        request_id = getattr(request.state, "request_id", "")

        entry = resolve_entry(request.method, request.url.path)
        decision: Decision
        resource: ResourceRef

        if entry is None or entry.is_blocked or entry.action != action:
            # 未登记 / blocked / action 与 policy 不符：一律 fail closed，handler 永不执行
            if entry is None or entry.action != action:
                decision = Decision(allowed=False, reason_code=ReasonCode.ACTION_RESOURCE_MISMATCH)
            else:
                decision = Decision(allowed=False, reason_code=ReasonCode.ROUTE_BLOCKED)
            resource = _public_ref("route", f"{request.method} {request.url.path}")
        else:
            if entry.resource_loader.startswith("load_body_"):
                # §5 loader 为同步签名：body 由本依赖预读进 request.state
                # （§6 durable 前不 mutation）
                request.state.policy_body = await request.json()
            try:
                resource = resource_loader(request, session)
            except ResourceScopeUnresolved as unresolved:
                resource = _public_ref(unresolved.resource_type, unresolved.resource_id)
                decision = Decision(
                    allowed=False, reason_code=ReasonCode.RESOURCE_SCOPE_UNRESOLVED
                )
            else:
                # step3：action × resource_type 精确组合（§4.2-3；policy 登记的 loader 契约为准）
                expected_type = LOADER_RESOURCE_TYPE.get(entry.resource_loader)
                if expected_type is not None and resource.resource_type != expected_type:
                    decision = Decision(
                        allowed=False, reason_code=ReasonCode.ACTION_RESOURCE_MISMATCH
                    )
                else:
                    decision = authorize(principal, action, resource)

        identity_fields_present = _identity_fields_present(request)
        audit_context = AuditContext(
            actor_id=principal.actor_id,
            role=principal.role,
            enterprise_id=principal.enterprise_id,
            correlation_id=correlation_id,
            action=action,
            resource_scope=resource.scope,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
            model_boundary=None,
            identity_field_present=identity_fields_present,
        )
        try:
            audit.write_decision(
                audit_context=audit_context, decision=decision, request_id=request_id
            )
        except Exception as exc:
            raise _http_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                ReasonCode.AUDIT_UNAVAILABLE.value,
                "授权决策审计未 durable，请求被拒绝（fail closed）: " + str(exc),
            ) from exc

        if not decision.allowed:
            raise _http_error(
                status.HTTP_403_FORBIDDEN,
                decision.reason_code.value,
                f"授权拒绝：{decision.reason_code.value}",
            )
        # §3.3：body 身份字段与 Principal 冲突 → allow 审计 durable 后 409
        if _identity_conflict(request, principal):
            raise _http_error(
                status.HTTP_409_CONFLICT,
                "actor_conflict",
                "请求体身份字段与 Principal 冲突（§3.3）",
            )
        return AuthorizationContext(
            principal=principal,
            action=action,
            resource=resource,
            decision=decision,
            correlation_id=correlation_id,
        )

    return _dependency


@dataclass(frozen=True)
class AuthorizationContext:
    """§5 冻结：handler 只能在本对象返回后运行。"""

    principal: Principal
    action: Action
    resource: ResourceRef
    decision: Decision
    correlation_id: str


__all__ = [
    "LOADERS",
    "LOADER_RESOURCE_TYPE",
    "PRINCIPAL_DEP",
    "TSV_PATH",
    "AuditUnavailable",
    "AuthorizationContext",
    "CoverageReport",
    "PolicyEntry",
    "PolicyValidationError",
    "ResourceLoader",
    "ResourceScopeUnresolved",
    "get_audit_writer",
    "get_policy",
    "get_readonly_session",
    "iter_openapi_routes",
    "load_policy",
    "register_audit_writer",
    "require_action",
    "resolve_entry",
    "scan_two_way",
]
