from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.intake import IdentityTimestampMixin


class CopilotInteraction(IdentityTimestampMixin, Base):
    __tablename__ = "copilot_interaction"
    __table_args__ = (
        CheckConstraint(
            "use_case in ('mapping_explanation', 'investigation_qa', 'report_outline')",
            name="ck_copilot_interaction_use_case",
        ),
        CheckConstraint(
            "outcome in ('accepted', 'rejected')",
            name="ck_copilot_interaction_outcome",
        ),
    )

    finding_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE")
    )
    import_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="CASCADE")
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="CASCADE")
    )
    use_case: Mapped[str] = mapped_column(String(64), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    template_version: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    context_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_references: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    response_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    rejection_reasons: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)


__all__ = ["CopilotInteraction"]
