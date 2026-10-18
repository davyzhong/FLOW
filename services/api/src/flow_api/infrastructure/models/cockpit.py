"""CFO 驾驶舱行动项模型（批次 B3）。

设计边界（实施方案批次 B / 设计文档 §10）：
- 行动项是「财务结论闭环」的最小载体：从 Finding 派生，只读展示 + CFO 确认；
- 不做通用任务管理（无指派/排期/通知字段，D001 边界）；
- 确认动作不改本表任何业务行（B5：只写 durable AuditEvent，allow 决策即
  确认凭证，resource_id = 行动项 id）；本表不可变（无 UPDATE/DELETE 路径）。
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.domain.ids import new_uuid7
from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.intake import IdentityTimestampMixin


class ActionItem(IdentityTimestampMixin, Base):
    """行动项：Finding 的 CFO 闭环载体（不可变行 + 审计确认）。"""

    __tablename__ = "cockpit_action_item"
    __table_args__ = (
        CheckConstraint(
            "length(title) between 1 and 200", name="ck_action_item_title_len"
        ),
        Index(
            "ix_action_item_enterprise_created",
            "enterprise_id",
            "created_at",
        ),
        {
            "comment": (
                "驾驶舱行动项（批次 B3）：Finding 派生、只读展示、"
                "确认动作仅写 durable AuditEvent（不改本行）"
            )
        },
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(), primary_key=True, default=new_uuid7
    )
    enterprise_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    finding_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("finding.id"), nullable=False
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("metric_snapshot.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
