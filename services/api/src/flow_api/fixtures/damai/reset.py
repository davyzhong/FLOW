"""Transaction-scoped cleanup for the Damai synthetic business batch."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _repository_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到 FLOW 仓库根目录")


def reset_damai_business_data(session: Session, enterprise_id: UUID) -> dict[str, int]:
    """Execute the package SQL reset within the caller's transaction.

    The SQL targets only the named Damai batch joined through this enterprise's cycle.
    System dictionaries, enterprise/cycle rows, statement publication history, audit
    events, and shared stored objects are retained. The caller rolls back if reseeding
    or subsequent verification fails.
    """
    connection = session.connection()
    from flow_api.settings import get_settings

    connection.execute(
        text("SELECT set_config('flow.target_enterprise_id', :enterprise_id, true)"),
        {"enterprise_id": str(enterprise_id)},
    )
    connection.execute(
        text("SELECT set_config('flow.audit_retention_days', :retention_days, true)"),
        {"retention_days": str(get_settings().flow_audit_retention_days)},
    )
    sql_path = _repository_root() / "data/enterprise/damai-logistics/v1/sql/20_business_reset.sql"
    source = sql_path.read_text(encoding="utf-8")
    statements = []
    for fragment in source.split(";"):
        statement = "\n".join(
            line for line in fragment.splitlines() if not line.lstrip().startswith("--")
        ).strip()
        if statement:
            statements.append(statement)
    if not statements:
        raise RuntimeError("企业业务重置 SQL 为空")
    for statement in statements:
        connection.exec_driver_sql(statement)
    row = connection.exec_driver_sql(
        "SELECT batches, imports, snapshots, cycles_reopened, review_events_archived "
        "FROM _damai_reset_counts"
    ).one()
    return {
        "batches_deleted": int(row.batches),
        "imports_deleted": int(row.imports),
        "snapshots_deleted": int(row.snapshots),
        "cycles_reopened": int(row.cycles_reopened),
        "review_events_archived": int(row.review_events_archived),
    }


__all__ = ["reset_damai_business_data"]
