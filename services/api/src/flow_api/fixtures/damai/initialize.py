"""One-transaction full/business-only initializer for the Damai enterprise package."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.enterprise.directory import sync_enterprise_directory
from flow_api.enterprise.models import AnalysisCycle, Enterprise
from flow_api.fixtures.damai.loader import seed_damai_demo
from flow_api.fixtures.damai.reset import reset_damai_business_data
from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricDefinitionDependency,
    MetricSnapshot,
)
from flow_api.infrastructure.models.canonical import (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
    Organization,
)
from flow_api.infrastructure.models.enterprise_directory import (
    EnterpriseMember,
    EnterpriseOrgUnit,
)
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.persistence import _definition_config
from flow_api.security.models import RoleBinding

ENTERPRISE_CODE = "damai-logistics"
ENTERPRISE_PACKAGE = Path("data/enterprise/damai-logistics/v1")
METRIC_CATALOG = Path("config/metrics/flow_v1_metrics.yaml")


def _repository_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到 FLOW 仓库根目录")


def _verify_system_dictionary(session: Session, root: Path) -> None:
    """Require platform-owned metric definitions to exist and match; never seed globals."""
    catalog = load_metric_catalog(root / METRIC_CATALOG)
    definitions: dict[str, MetricDefinition] = {}
    for metric in catalog.metrics:
        current = session.scalar(
            select(MetricDefinition).where(
                MetricDefinition.metric_code == metric.metric_code,
                MetricDefinition.version == metric.version,
            )
        )
        if current is None:
            raise RuntimeError(f"系统指标字典尚未初始化: {metric.metric_code}@{metric.version}")
        expected = _definition_config(metric)
        if (
            current.name != metric.name
            or current.business_definition != metric.business_definition
            or current.formula != metric.formula
            or current.aggregation != metric.aggregation
            or current.unit != metric.unit
            or current.definition_config != expected
        ):
            raise RuntimeError(
                f"系统指标定义与大麦数据包依赖不一致: {metric.metric_code}@{metric.version}"
            )
        definitions[metric.metric_code] = current
    for metric in catalog.metrics:
        current_edges = tuple(
            session.scalars(
                select(MetricDefinitionDependency.dependency_definition_id)
                .where(
                    MetricDefinitionDependency.metric_definition_id
                    == definitions[metric.metric_code].id
                )
                .order_by(MetricDefinitionDependency.position)
            ).all()
        )
        expected_edges = tuple(definitions[code].id for code in metric.dependencies)
        if current_edges != expected_edges:
            raise RuntimeError(
                f"系统指标依赖关系尚未初始化或与版本不一致: {metric.metric_code}@{metric.version}"
            )


def _verify_business_org_refs(session: Session, root: Path, enterprise_id: UUID) -> None:
    import json

    rows = [
        json.loads(line)
        for line in (root / ENTERPRISE_PACKAGE / "business/canonical/organizations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    package_codes = {str(row["code"]) for row in rows}
    existing = set(
        session.scalars(
            select(EnterpriseOrgUnit.code).where(
                EnterpriseOrgUnit.enterprise_id == enterprise_id,
                EnterpriseOrgUnit.status == "active",
            )
        ).all()
    )
    missing = sorted(package_codes - existing)
    if missing:
        raise RuntimeError("仅重置业务时，现存组织建制缺少业务数据引用: " + ", ".join(missing))
    dimensions = set(
        session.scalars(select(Organization.code).where(Organization.code.in_(package_codes))).all()
    )
    missing_dimensions = sorted(package_codes - dimensions)
    if missing_dimensions:
        raise RuntimeError("系统分析组织维度尚未初始化: " + ", ".join(missing_dimensions))


def _verify_rebuilt_package(
    session: Session, root: Path, enterprise_id: UUID, mode: str
) -> dict[str, int]:
    import json

    batches = session.scalars(
        select(AnalysisBatch)
        .join(AnalysisCycle, AnalysisCycle.id == AnalysisBatch.analysis_cycle_id)
        .where(
            AnalysisBatch.name == "damai-demo-v1",
            AnalysisCycle.enterprise_id == enterprise_id,
        )
    ).all()
    if len(batches) != 1:
        raise RuntimeError(f"大麦包应有且仅有一个业务批次，实际为 {len(batches)}")
    batch = batches[0]
    import_ids = select(ImportVersion.id).where(ImportVersion.batch_id == batch.id)
    published_imports = session.scalar(
        select(func.count())
        .select_from(ImportVersion)
        .where(ImportVersion.batch_id == batch.id, ImportVersion.is_published.is_(True))
    )
    if published_imports != 1:
        raise RuntimeError(f"大麦业务批次应有且仅有一个已发布导入版本，实际为 {published_imports}")

    canonical_manifest = json.loads(
        (root / ENTERPRISE_PACKAGE / "business/canonical/manifest.json").read_text(encoding="utf-8")
    )
    expected = {
        "financial_actuals": canonical_manifest["files"]["financial_actuals.jsonl"]["row_count"],
        "monthly_budgets": canonical_manifest["files"]["monthly_budgets.jsonl"]["row_count"],
        "operating_actuals": canonical_manifest["files"]["operating_actuals.jsonl"]["row_count"],
        "ar_collections": canonical_manifest["files"]["ar_collections.jsonl"]["row_count"],
    }
    checks = (
        ("financial_actuals", FactFinancialActual, FactFinancialActual.import_version_id),
        ("monthly_budgets", FactBudget, FactBudget.import_version_id),
        ("operating_actuals", FactOperatingActual, FactOperatingActual.import_version_id),
        ("ar_collections", FactArCollection, FactArCollection.import_version_id),
    )
    counts: dict[str, int] = {}
    for name, model, import_version_column in checks:
        actual = session.scalar(
            select(func.count())
            .select_from(model)
            .where(import_version_column.in_(import_ids))
        )
        counts[name] = int(actual or 0)
        if counts[name] != int(expected[name]):
            raise RuntimeError(
                f"大麦事实行数不符 {name}: actual={counts[name]} expected={expected[name]}"
            )

    snapshots = session.scalar(
        select(func.count()).select_from(MetricSnapshot).where(MetricSnapshot.batch_id == batch.id)
    )
    if snapshots != 12:
        raise RuntimeError(f"大麦分析快照应有 12 个，实际为 {snapshots}")
    package_users = [
        json.loads(line)
        for line in (root / ENTERPRISE_PACKAGE / "organization/users.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    for user in package_users:
        member = session.scalar(
            select(EnterpriseMember).where(
                EnterpriseMember.enterprise_id == enterprise_id,
                EnterpriseMember.actor_id == user["actor_id"],
                EnterpriseMember.status == "active",
            )
        )
        binding = session.scalar(
            select(RoleBinding).where(
                RoleBinding.enterprise_id == enterprise_id,
                RoleBinding.actor_id == user["actor_id"],
                RoleBinding.role == user["role_code"],
                RoleBinding.active.is_(True),
            )
        )
        if member is None or binding is None:
            raise RuntimeError(f"企业模拟身份或角色绑定缺失: {user['actor_id']}")
    return {**counts, "metric_snapshots": int(snapshots), "members_verified": len(package_users)}


def initialize_damai_enterprise(
    session: Session,
    mode: str,
    *,
    seed: Callable[..., dict[str, object]] = seed_damai_demo,
) -> dict[str, object]:
    """Run full organization sync or business-only reset within caller transaction."""
    if mode not in {"full", "business"}:
        raise ValueError("mode 必须是 full 或 business")
    root = _repository_root()
    enterprise = session.scalar(select(Enterprise).where(Enterprise.code == ENTERPRISE_CODE))
    if enterprise is None:
        raise RuntimeError(
            f"系统中尚无企业 {ENTERPRISE_CODE!r}；请先在系统内创建企业空间再初始化企业账套"
        )
    _verify_system_dictionary(session, root)
    org_receipt = None
    if mode == "full":
        org_receipt = sync_enterprise_directory(
            session, enterprise.id, root / ENTERPRISE_PACKAGE / "organization"
        )
    else:
        _verify_business_org_refs(session, root, enterprise.id)
    reset_receipt = reset_damai_business_data(session, enterprise.id)
    seed_receipt = seed(session, sync_organization=False, upsert_enterprise=False)
    session.flush()
    verification = _verify_rebuilt_package(session, root, enterprise.id, mode)
    return {
        "mode": mode,
        "enterprise_id": str(enterprise.id),
        "organization": org_receipt,
        "business_reset": reset_receipt,
        "seed": seed_receipt,
        "verification": verification,
    }


__all__ = ["initialize_damai_enterprise"]
