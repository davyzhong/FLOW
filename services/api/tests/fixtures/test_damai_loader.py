"""Task 4：大麦演示装载器 DB 集成测试（聚焦财报装载子链）。

- enterprise 幂等复用 bootstrap UUID 并改名为大麦物流（授权契约单企业）；
- 两份合成财报（FY2025/FY2026）导入 + 归一化 + 发布：source SHA 非空、
  归一行含 item_id、report published；
- 二次 seed 幂等：报告身份/归一行数不增长。
事务回滚注入测试与指标快照/Finding 编排（规格 §4.3 全量）在后续切片。
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai.loader import seed_damai_demo
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (StatementNormalizedItem, StatementLineItem, StatementReport):
        session.execute(delete(table))
        session.commit()
    yield session
    session.close()
    engine.dispose()


def test_seed_loads_enterprise_and_two_published_reports(db_session: Session) -> None:
    receipt = seed_damai_demo(db_session)

    assert receipt["enterprise"]["id"] == "00000000-0000-0000-0000-00000000d001"
    assert "大麦" in receipt["enterprise"]["name"]
    assert len(receipt["reports"]) == 2
    for report in receipt["reports"]:
        assert report["status"] == "published"
        assert report["normalized_rows"] > 0
        assert report["source_sha256"]


def test_seed_is_idempotent_on_identity_and_rows(db_session: Session) -> None:
    first = seed_damai_demo(db_session)
    second = seed_damai_demo(db_session)

    total = len(
        list(db_session.execute(text("SELECT id FROM statement_report")))
    )
    assert total == 2, "重复 seed 不得新建报告"
    assert [r["report_id"] for r in second["reports"]] == [
        r["report_id"] for r in first["reports"]
    ]


# ---------------------------------------------------------------------------
# Task A3 红灯：独立 DAMAI.SYN 财报身份 + 正式审核链（规格 §4.3）
# ---------------------------------------------------------------------------


def test_seed_uses_damai_syn_identity_and_governed_publish(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """财报必须来自 fixtures/damai/statements/damai_fy*.yaml（SHA 可核对），
    身份为独立 DAMAI.SYN，发布必须经 ReviewService.publish——不得直改
    report.status，也不得读取/冒充 9988.HK 阿里巴巴 fixture。"""

    from flow_api.statements.review import ReviewService

    publish_calls: list[str] = []
    original_publish = ReviewService.publish

    def spy(self: ReviewService, report_id, *, operator: str):  # noqa: ANN001
        publish_calls.append(str(report_id))
        return original_publish(self, report_id, operator=operator)

    monkeypatch.setattr(ReviewService, "publish", spy)
    receipt = seed_damai_demo(db_session)

    assert len(publish_calls) == 2, (
        "两份财报都必须经 ReviewService.publish 发布（监视点未触发 = 直改状态）"
    )
    assert set(publish_calls) == {r["report_id"] for r in receipt["reports"]}
    for report in receipt["reports"]:
        row = db_session.get(StatementReport, report["report_id"])
        assert row is not None
        assert row.stock_code == "DAMAI.SYN", "必须为独立 synthetic 身份"
        assert row.status == "published"
        yaml_path = (
            REPO_ROOT
            / "fixtures/damai/statements"
            / f"damai_{report['fy'].lower()}.yaml"
        )
        expected_sha = hashlib.sha256(yaml_path.read_bytes()).hexdigest()
        assert row.source_sha256 == expected_sha, (
            "source SHA 必须来自大麦发行版 yaml，而非阿里巴巴 fixture"
        )
    alibaba_rows = db_session.execute(
        text("SELECT count(*) FROM statement_report WHERE stock_code = '9988.HK'")
    ).scalar_one()
    assert alibaba_rows == 0, "大麦 seed 不得创建/复用 9988.HK 报告身份"


def test_review_publish_blocks_tampered_damai_report(db_session: Session) -> None:
    """审核链门禁必须有牙：破坏 资产=负债+权益 的财报不得发布。"""

    import yaml

    from flow_api.statements.importer import import_statement_report
    from flow_api.statements.review import ReviewBlockedError, ReviewService

    yaml_path = REPO_ROOT / "fixtures/damai/statements/damai_fy2026.yaml"
    payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    for row in payload["statements"]["合并资产负债表"]:
        if row["item"] == "资产总计":
            row["期末余额"] = str(Decimal(str(row["期末余额"])) + Decimal("1"))
    report = import_statement_report(
        db_session,
        company_name="大麦物流",
        stock_code="DAMAI.SYN",
        report_kind="年报",
        period_label="FY2026",
        payload=payload,
        source_ref="synthetic/damai-logistics-demo-v1/tampered",
        source_sha256="0" * 64,
    )
    with pytest.raises(ReviewBlockedError):
        ReviewService(db_session).publish(report.id, operator="damai-demo-seed")
