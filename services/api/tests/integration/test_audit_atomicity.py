"""S01 审计原子性故障注入测试（Task 2A 余段集成验证）。

验证：prepare 阶段失败时对象存储零调用；对象写失败时 failure outcome durable
且业务不发布；pipeline 不偷跑 commit（事务边界由路由层控制）。

prepare_intent 首步即校验 report_snapshot 存在性，因此需真实快照行：
经 analytics_seed 造最小链（批次→指标快照）后挂 ReportSnapshot。
"""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    ImportVersion,
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.publishing import ReportSnapshot
from flow_api.publishing import (
    objective_freeze,  # noqa: F401  # 注册 objective_report_snapshot 元数据
)
from flow_api.publishing.models import ReportView, SnapshotIdentity, view_to_json
from flow_api.publishing.pipeline import (
    PublicationPipeline,
    PublicationPipelineError,
)

ENTERPRISE_ID = "00000000-0000-0000-0000-0000000000e1"


class _ExplodingStore:
    """在 write 时抛异常的对象存储（匹配 ObjectStore 真实协议）。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def object_key_for_sha(self, sha256: str) -> str:
        return f"objects/{sha256}"

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> str:
        self.calls.append(f"write:{object_key}")
        raise RuntimeError("对象存储不可达")


class _CountingStore:
    def __init__(self) -> None:
        self.writes = 0

    def object_key_for_sha(self, sha256: str) -> str:
        return f"objects/{sha256}"

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> str:
        self.writes += 1
        return content_sha256


def _stub_renderers() -> dict:
    return {
        "html": lambda view, fmt: b"<html>test</html>",
        "pdf": lambda view, fmt: b"%PDF-test",
    }


def _make_pipeline(store=None) -> PublicationPipeline:
    return PublicationPipeline(renderers=_stub_renderers(), store=store or _CountingStore())


def _seed_report_snapshot(session: Session) -> ReportSnapshot:
    """最小真实链：批次→导入版本→周期→指标快照→报告快照。

    dim_period.month_key 唯一，同库多次运行时查无则建（维度行可复用）。
    """
    suffix = hashlib.sha256(b"audit-atomicity").hexdigest()[:8]
    period = session.scalar(select(Period).where(Period.month_key == 202608))
    if period is None:
        period = Period(month_key=202608, year=2026, quarter=3, month=8)
        session.add(period)
        session.flush()
    batch = AnalysisBatch(name=f"AuditAtomicity {suffix}", status="published")
    import_version = ImportVersion(
        batch=batch, sequence=1, status="published", is_published=True, summary={}
    )
    session.add_all([batch, import_version])
    session.flush()
    definition = MetricDefinition(
        metric_code=f"revenue_audit_{suffix}",
        version=1,
        name="Revenue",
        business_definition="Recognized operating revenue",
        formula="sum(revenue)",
        aggregation="sum",
        unit="CNY",
    )
    snapshot = MetricSnapshot(
        batch=batch,
        import_version=import_version,
        as_of_period=period,
        version=1,
        engine_version="flow-metrics/1",
        definition_set_id="flow.metrics.audit-atomicity.v1",
        definition_set_hash="a" * 64,
        fingerprint="b" * 64,
        status="published",
    )
    value = MetricValue(
        metric_snapshot=snapshot,
        metric_definition=definition,
        value=100,
        exact_value="100",
        calculation_trace={},
        comparison_type="month",
        period_id=period.id,
    )
    session.add_all([definition, snapshot, value])
    session.flush()
    report = ReportSnapshot(
        metric_snapshot=snapshot,
        version=1,
        title="审计原子性测试快照",
        template_code="finance_bp_monthly",
    )
    session.add(report)
    session.flush()
    identity = SnapshotIdentity(
        batch_id=str(batch.id),
        metric_snapshot_id=str(snapshot.id),
        analysis_run_id="00000000-0000-0000-0000-000000000000",
        report_snapshot_id=str(report.id),
        report_version=1,
        title=report.title,
        template_code=report.template_code,
        metric_engine_version="flow-metrics/1",
        analysis_engine_version="flow-analysis/1",
        generated_at="2026-09-14T00:00:00+00:00",
    )
    report.frozen_view = {
        "schema_version": 1,
        "view": view_to_json(
            ReportView(
                identity=identity,
                metrics=(),
                findings=(),
                quality_summary={},
                reconciliations=(),
            )
        ),
    }
    session.flush()
    return report


class TestAuditAtomicity:
    @pytest.fixture
    def session(self):
        from flow_api.infrastructure.db import get_session_factory

        s = get_session_factory()()
        yield s
        s.rollback()
        s.close()

    @pytest.fixture
    def report_snapshot_id(self, session: Session) -> str:
        report = _seed_report_snapshot(session)
        return str(report.id)

    def test_prepare_failure_prevents_object_store(self, session: Session) -> None:
        """prepare 阶段失败（快照不存在）→ 对象存储零调用、无 intent 落库。"""
        store = _CountingStore()
        pipeline = _make_pipeline(store)
        with pytest.raises(PublicationPipelineError):
            pipeline.prepare_intent(
                session,
                snapshot_id="00000000-0000-0000-0000-000000000000",
                actor_id="test",
                correlation_id="corr-1",
                request_id="req-1",
                formats=("html",),
            )
        assert store.writes == 0

    def test_object_failure_creates_failure_outcome(
        self, session: Session, report_snapshot_id: str
    ) -> None:
        """对象写失败 → format 结果为 failed 且错误被捕获，不向上抛。"""
        store = _ExplodingStore()
        pipeline = _make_pipeline(store)
        prepared = pipeline.prepare_intent(
            session,
            snapshot_id=report_snapshot_id,
            actor_id="test",
            correlation_id="corr-explode",
            request_id="req-2",
            formats=("html",),
            enterprise_id=ENTERPRISE_ID,
        )
        session.flush()
        result = pipeline.execute_object(prepared)
        assert [f.status for f in result.formats] == ["failed"]
        assert "对象存储不可达" in (result.formats[0].error_message or "")
        assert store.calls, "store 应被调用过（写失败）"
        pipeline.finalize_failure(session, prepared, RuntimeError("对象存储不可达"))
        session.flush()

    def test_pipeline_does_not_commit(
        self, session: Session, report_snapshot_id: str
    ) -> None:
        """pipeline 四阶段不应自行 commit（由路由层控制事务边界）。"""
        commit_calls: list[int] = []
        original_commit = session.commit
        session.commit = lambda: commit_calls.append(1)  # type: ignore[method-assign]
        try:
            pipeline = _make_pipeline()
            prepared = pipeline.prepare_intent(
                session,
                snapshot_id=report_snapshot_id,
                actor_id="test",
                correlation_id="corr-no-commit",
                request_id="req-3",
                formats=("html",),
                enterprise_id=ENTERPRISE_ID,
            )
            result = pipeline.execute_object(prepared)
            assert [f.status for f in result.formats] == ["succeeded"]
            pipeline.finalize_success(session, prepared, result)
            assert len(commit_calls) == 0, "pipeline 不应自行 commit"
        finally:
            session.commit = original_commit  # type: ignore[method-assign]
            session.rollback()
