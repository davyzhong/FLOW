"""T10-B3 扩展：page_anchor 锚定模式词汇表扩充。

背景（2026-09-25 P1 审计修正）：L1 答案集新增两类定位模式——
- `strong-sign-flip-loss-row`（25 字符）：繁体中文年报把亏损行印成正数
  （如"淨損失 9,083"），抽取按会计符号记负值，行名+绝对值同页即强锚；
- `visual-verified`（15 字符）：主表页为图像层无文本（京东物流 2025 年报
  现金流量表），以渲染 PNG 人工目视核对为准，证据 SHA 由
  `config/statements/l1_visual_verified.yaml` 登记并 fail-closed 校验。

0029 的 String(16) 与 check 约束 ('strong','weak') 无法容纳。
本迁移拓宽列到 String(32) 并重建 check 约束；downgrade 完整还原。
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0030_page_anchor_vocabulary"
down_revision: str | None = "0029_statement_provenance"
branch_labels = None
depends_on = None

_NEW_MODES = ("strong", "weak", "strong-sign-flip-loss-row", "visual-verified")
_OLD_MODES = ("strong", "weak")


def upgrade() -> None:
    op.drop_constraint(
        "ck_statement_line_item_page_anchor", "statement_line_item", type_="check"
    )
    op.alter_column(
        "statement_line_item",
        "page_anchor",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_statement_line_item_page_anchor",
        "statement_line_item",
        "page_anchor IS NULL OR page_anchor IN ("
        + ", ".join(f"'{m}'" for m in _NEW_MODES)
        + ")",
    )


def downgrade() -> None:
    # 先清掉新模式行，避免还原约束时违规
    op.execute(
        "UPDATE statement_line_item SET page_anchor = NULL "
        "WHERE page_anchor IN ('strong-sign-flip-loss-row', 'visual-verified')"
    )
    op.drop_constraint(
        "ck_statement_line_item_page_anchor", "statement_line_item", type_="check"
    )
    op.alter_column(
        "statement_line_item",
        "page_anchor",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_statement_line_item_page_anchor",
        "statement_line_item",
        "page_anchor IS NULL OR page_anchor IN ("
        + ", ".join(f"'{m}'" for m in _OLD_MODES)
        + ")",
    )
