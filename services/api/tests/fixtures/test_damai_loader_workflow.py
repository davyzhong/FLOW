"""Task B2：大麦 Finding/证据/结论/冻结工作流契约测试（红灯先行）。

- 植入事件表达为可追溯分析信号；系统 Finding 只由现有 playbook 产生（≤5 个），
  预算差异/组合信号只作为证据或次级解释写入结论，不伪造第 6 个 playbook；
- 落库状态覆盖 candidate → in_review → approved：每个 Finding 的首条 review_event
  必须是 submitted（该 decision 仅从 candidate 合法），至少一个 approved、
  至少一个停在 in_review；只有 approved Finding 进入冻结报告；
- 冻结内部分析报告、两年客观财报快照和经营概览，receipt 中的 SHA 必须可重算；
- 结论四段齐备且可追溯：发行包 manifest SHA + canonical import-version + 证据引用；
- 二次 seed 工作流对象零增长；冻结故障注入回滚零残留。
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from integration.intake_service_support import clean
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai import loader as damai_loader
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.investigation.state_machines import (
    ReviewBlockedError,
    decide_finding_transition,
)
from flow_api.publishing.objective_freeze import payload_hash
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]

_BASE_TABLES = (
    "statement_normalized_item",
    "statement_line_item",
    "statement_report",
    "metric_value",
    "metric_snapshot",
    "analysis_run",
    "import_version",
    "source_file",
    "stored_object",
    "analysis_batch",
)
_WORKFLOW_TABLES = (
    "finding",
    "evidence",
    "conclusion",
    "review_event",
    "report_snapshot",
    "report_snapshot_item",
    "objective_report_snapshot",
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def _wipe(session: Session) -> None:
    clean(session)  # canonical 事实/维度 + intake 链全清（须先于 batch 删除，FK RESTRICT）
    for table in (
        MetricValue,
        AnalysisRun,
        MetricSnapshot,
        AnalysisBatch,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    for table in _WORKFLOW_TABLES:
        session.execute(text(f"DELETE FROM {table}"))
    session.commit()


@pytest.fixture(scope="module")
def seeded() -> Iterator[tuple[Session, dict[str, Any]]]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    _wipe(session)
    receipt = damai_loader.seed_damai_demo(session)
    session.commit()
    yield session, receipt
    session.close()
    engine.dispose()


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    _wipe(session)
    yield session
    session.close()
    engine.dispose()


def _counts(session: Session, tables: tuple[str, ...]) -> dict[str, int]:
    return {
        table: session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in tables
    }


# --------------------------------------------------------------- 状态机契约


def test_candidate_cannot_be_approved_directly() -> None:
    """candidate 只能经 submitted 进 in_review；直接 approved 必须被门禁阻断。"""

    with pytest.raises(ReviewBlockedError) as excinfo:
        decide_finding_transition("candidate", "approved")
    assert excinfo.value.code == "invalid_transition"
    assert decide_finding_transition("candidate", "submitted") == "in_review"
    assert (
        decide_finding_transition(
            "in_review",
            "approved",
            evidence_statuses=("verified",),
            conclusion_complete=True,
        )
        == "approved"
    )


# ----------------------------------------------------------- 工作流落库状态


def test_findings_cover_review_trajectory(
    seeded: tuple[Session, dict[str, Any]],
) -> None:
    session, receipt = seeded
    workflow = receipt["workflow"]
    findings = workflow["findings"]
    assert 1 <= len(findings) <= 5, "系统 Finding 只由现有 5 个 playbook 产生"
    statuses = {item["status"] for item in findings}
    assert "approved" in statuses, "至少一个 Finding 必须完成签发"
    assert "in_review" in statuses, "至少一个 Finding 必须停在复核中（演示待办）"

    # 每个 Finding 的首条事件必须是 submitted（仅从 candidate 合法 → candidate 状态被覆盖）
    per_finding = session.execute(
        text(
            "SELECT finding_id, decision FROM review_event WHERE sequence = 1"
        )
    ).fetchall()
    assert per_finding, "每个 Finding 必须有复核事件链"
    assert {row.decision for row in per_finding} == {"submitted"}
    approved_events = session.execute(
        text("SELECT count(*) FROM review_event WHERE decision = 'approved'")
    ).scalar_one()
    assert approved_events >= 1


def test_only_approved_findings_enter_frozen_report(
    seeded: tuple[Session, dict[str, Any]],
) -> None:
    session, receipt = seeded
    from flow_api.publishing.service import build_report_view

    snapshot_id = receipt["workflow"]["freezes"]["internal_report"]["report_snapshot_id"]
    report = session.execute(
        text("SELECT frozen_view FROM report_snapshot WHERE id = :rid"),
        {"rid": snapshot_id},
    ).one()
    assert report.frozen_view, "冻结报告必须有 frozen_view 载荷"
    from flow_api.infrastructure.models.publishing import ReportSnapshot

    snapshot = session.get(ReportSnapshot, snapshot_id)
    assert snapshot is not None
    view = build_report_view(session, snapshot)
    assert view.findings, "冻结报告至少含一个 Finding"
    approved_ids = {
        item["finding_id"]
        for item in receipt["workflow"]["findings"]
        if item["status"] == "approved"
    }
    assert {finding.finding_id for finding in view.findings} == approved_ids, (
        "只有 approved Finding 可进入正式结论（冻结报告）"
    )


# ------------------------------------------------------------------- 冻结


def test_freeze_hashes_recompute_from_payload(
    seeded: tuple[Session, dict[str, Any]],
) -> None:
    session, receipt = seeded
    freezes = receipt["workflow"]["freezes"]

    for group in ("objective_statements", "operations_overview"):
        entries = freezes[group]
        assert len(entries) == 2, f"{group} 必须覆盖两年财报"
        assert {entry["fy"] for entry in entries} == {"FY2025", "FY2026"}
        for entry in entries:
            row = session.execute(
                text(
                    "SELECT payload, payload_hash FROM objective_report_snapshot"
                    " WHERE id = :sid"
                ),
                {"sid": entry["snapshot_id"]},
            ).one()
            assert row.payload_hash == entry["payload_hash"]
            assert payload_hash(row.payload) == entry["payload_hash"], (
                "冻结 SHA 必须能从载荷重算"
            )

    internal = freezes["internal_report"]
    from flow_api.infrastructure.models.publishing import ReportSnapshot
    from flow_api.publishing.service import build_report_view, digest_view

    snapshot = session.get(ReportSnapshot, internal["report_snapshot_id"])
    assert snapshot is not None
    assert digest_view(build_report_view(session, snapshot)) == internal["view_sha256"]


# --------------------------------------------------------------- 结论追溯


def test_conclusions_traceable_to_release_and_canonical(
    seeded: tuple[Session, dict[str, Any]],
) -> None:
    session, receipt = seeded
    workflow = receipt["workflow"]
    manifest_sha = workflow["manifest_sha256"]
    import_version_id = receipt["analytics"]["import_version_id"]
    expected_manifest = hashlib.sha256(
        (REPO_ROOT / "fixtures/damai/manifest.json").read_bytes()
    ).hexdigest()
    assert manifest_sha == expected_manifest, "receipt 必须携带发行包 manifest SHA"

    rows = session.execute(
        text(
            "SELECT finding_id, verified_facts, analysis_judgment, open_questions,"
            " recommendation FROM conclusion"
        )
    ).fetchall()
    assert len(rows) == len(workflow["findings"]), "每个 Finding 必须有结论"
    for row in rows:
        for section in (
            row.verified_facts,
            row.analysis_judgment,
            row.open_questions,
            row.recommendation,
        ):
            assert section and section.strip(), "结论四段必须齐备"
        evidence_refs = session.execute(
            text("SELECT object_id FROM evidence WHERE finding_id = :fid"),
            {"fid": row.finding_id},
        ).fetchall()
        canonical_ref = f"import-version:{import_version_id}"
        assert canonical_ref in {r.object_id for r in evidence_refs}
        assert manifest_sha in row.verified_facts, "结论必须追溯到发行包 SHA"
        assert canonical_ref in row.verified_facts, "结论必须追溯到 canonical 记录集"


def test_implanted_signals_recorded_in_workflow_receipt(
    seeded: tuple[Session, dict[str, Any]],
) -> None:
    _, receipt = seeded
    signals = receipt["workflow"]["signals"]
    assert len(signals) >= 6, "六个植入事件都必须表达为可追溯信号"
    codes = {signal["event_code"] for signal in signals}
    assert codes == {"E1", "E2", "E3", "E4", "E5", "E6"}
    for signal in signals:
        assert signal["channel"] in ("finding", "evidence", "conclusion")
        assert signal["reference"], "每个信号必须有可追溯引用"


# --------------------------------------------------------------- 幂等与故障


def test_second_seed_keeps_workflow_counts_stable(db_session: Session) -> None:
    damai_loader.seed_damai_demo(db_session)
    db_session.commit()
    first = _counts(db_session, _WORKFLOW_TABLES)
    assert first["conclusion"] >= 1
    assert first["report_snapshot"] >= 1
    assert first["objective_report_snapshot"] >= 4  # 两年财报 ×（客观快照 + 经营概览）

    damai_loader.seed_damai_demo(db_session)
    db_session.commit()
    second = _counts(db_session, _WORKFLOW_TABLES)
    assert second == first, f"二次 seed 工作流计数必须零增长：{first} → {second}"


def test_seed_rolls_back_when_objective_freeze_fails(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """冻结故障注入：客观财报冻结失败时全部对象零残留（顶层提交语义）。"""

    def fail_freeze(session: Session, *, report_id: object) -> None:
        raise RuntimeError("injected_objective_freeze_failure")

    monkeypatch.setattr(
        damai_loader, "freeze_objective_statement_report", fail_freeze
    )
    with pytest.raises(RuntimeError, match="injected_objective_freeze_failure"):
        damai_loader.seed_damai_demo(db_session)
    db_session.rollback()
    assert set(_counts(db_session, _BASE_TABLES + _WORKFLOW_TABLES).values()) == {0}, (
        "冻结失败不得留部分数据"
    )
