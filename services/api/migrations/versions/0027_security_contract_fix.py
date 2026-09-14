"""S01 R1 安全合同补强：企业域引导数据 + 批次归属回填。

- `analysis_batch.created_by`：批次创建者（owner 校验数据来源，bootstrap 默认
  `flow-dev-bp`，与 dev principal / 种子 binding 同一身份）；
- 引导 `analysis_cycle`（单租户 bootstrap 企业）并把存量 legacy/public 批次
  统一转为 `module_kind='internal'`、挂接 cycle——满足
  `ck_analysis_batch_module_combo` 合法组合，使 batch-scoped 路由的
  lineage loader（§4.1 deny_legacy）可解析；
- 幂等：已回填（analysis_cycle_id 非空）的批次不重复处理；
- downgrade 完整还原列与引导数据（cycle 删除前清空引用）。
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0027_security_contract_fix"
down_revision: str | None = "0026_security_audit"
branch_labels = None
depends_on = None

# bootstrap 企业（与 scripts/seed_dev_principal.py 的 DEV_ENTERPRISE_ID 一致）
BOOTSTRAP_ENTERPRISE_ID = "00000000-0000-0000-0000-00000000d001"
BOOTSTRAP_ACTOR = "flow-dev-bp"
BOOTSTRAP_CYCLE_PERIOD = "2026-09"


def upgrade() -> None:
    op.add_column(
        "analysis_batch",
        sa.Column("created_by", sa.String(length=255), nullable=False, server_default=BOOTSTRAP_ACTOR),
    )

    bind = op.get_bind()
    # 引导 enterprise（analysis_cycle.enterprise_id 的 FK 目标；幂等）
    ent_row = bind.execute(
        sa.text("SELECT id FROM enterprise WHERE id = :eid"),
        {"eid": BOOTSTRAP_ENTERPRISE_ID},
    ).first()
    if ent_row is None:
        bind.execute(
            sa.text(
                "INSERT INTO enterprise (id, code, name, created_at)"
                " VALUES (:eid, 'flow-bootstrap', 'FLOW Bootstrap Enterprise', now())"
            ),
            {"eid": BOOTSTRAP_ENTERPRISE_ID},
        )

    # 引导 cycle（幂等）
    cycle_row = bind.execute(
        sa.text(
            "SELECT id FROM analysis_cycle WHERE enterprise_id = :eid AND period_key = :pk"
        ),
        {"eid": BOOTSTRAP_ENTERPRISE_ID, "pk": BOOTSTRAP_CYCLE_PERIOD},
    ).first()
    if cycle_row is None:
        bind.execute(
            sa.text(
                "INSERT INTO analysis_cycle (id, enterprise_id, period_key, status, created_at)"
                " VALUES (gen_random_uuid(), :eid, :pk, 'open', now())"
            ),
            {"eid": BOOTSTRAP_ENTERPRISE_ID, "pk": BOOTSTRAP_CYCLE_PERIOD},
        )
        cycle_row = bind.execute(
            sa.text(
                "SELECT id FROM analysis_cycle WHERE enterprise_id = :eid AND period_key = :pk"
            ),
            {"eid": BOOTSTRAP_ENTERPRISE_ID, "pk": BOOTSTRAP_CYCLE_PERIOD},
        ).first()
    cycle_id = cycle_row[0]

    # 存量批次转 internal + 挂 cycle + created_by 回填（幂等）
    bind.execute(
        sa.text(
            "UPDATE analysis_batch"
            " SET module_kind = 'internal',"
            "     fact_context_version = 2,"
            "     analysis_cycle_id = :cid,"
            "     created_by = :actor"
            " WHERE analysis_cycle_id IS NULL"
            "   AND (module_kind = 'legacy' OR module_kind = 'public')"
        ),
        {"cid": cycle_id, "actor": BOOTSTRAP_ACTOR},
    )
    bind.execute(
        sa.text(
            "UPDATE analysis_batch SET created_by = :actor"
            " WHERE created_by = 'system' OR created_by IS NULL"
        ),
        {"actor": BOOTSTRAP_ACTOR},
    )


def downgrade() -> None:
    bind = op.get_bind()
    # 只回退本迁移引入的归属：internal 且挂到引导 cycle 的批次
    bind.execute(
        sa.text(
            "UPDATE analysis_batch b"
            " SET module_kind = 'legacy', fact_context_version = 1, analysis_cycle_id = NULL"
            " FROM analysis_cycle c"
            " WHERE b.analysis_cycle_id = c.id"
            "   AND c.enterprise_id = :eid AND c.period_key = :pk"
        ),
        {"eid": BOOTSTRAP_ENTERPRISE_ID, "pk": BOOTSTRAP_CYCLE_PERIOD},
    )
    bind.execute(
        sa.text(
            "DELETE FROM analysis_cycle WHERE enterprise_id = :eid AND period_key = :pk"
        ),
        {"eid": BOOTSTRAP_ENTERPRISE_ID, "pk": BOOTSTRAP_CYCLE_PERIOD},
    )
    bind.execute(
        sa.text("DELETE FROM enterprise WHERE id = :eid"),
        {"eid": BOOTSTRAP_ENTERPRISE_ID},
    )
    op.drop_column("analysis_batch", "created_by")
