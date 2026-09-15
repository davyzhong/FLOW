"""S01 §7 四阶段审计原子性故障注入测试（R2 重写：pipeline → four_stage）。

验证：
- prepare 阶段失败（资源不存在/冻结 hash 不一致）→ 对象存储零调用、attempt 零落库；
- intent commit 失败 → PublicationIntentNotDurable（503 语义）且对象写 0 次；
- 对象写失败 → failure outcome durable 且 publication 状态 failed；
- 四阶段函数自身不 commit（事务边界由路由层控制，§7.2）；
- intent/outcome 审计经独立短事务落 AuditEvent。
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    ImportVersion,
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.publishing import PublicationAttempt, ReportSnapshot
from flow_api.publication.four_stage import (
    AuditContext,
    PublicationFormat,
    PublicationFreezeConflict,
    PublicationIntentNotDurable,
    PublicationNotFound,
    PublicationRequest,
    build_publication_failure,
    canonical_source_sha256,
    execute_object,
    finalize_failure,
    finalize_success,
    prepare_intent,
)
from flow_api.publishing import (  # noqa: F401
    objective_freeze,  # 注册 objective_report_snapshot 元数据
)
from flow_api.publishing.four_stage_binding import (  # noqa: F401
    _verify_report_snapshot,  # 注册 report_snapshot 资源校验器
)
from flow_api.publishing.models import ReportView, SnapshotIdentity, view_to_json
from flow_api.security.audit import AuditUnavailable, register_audit_writer
from flow_api.security.authorization import Action
from flow_api.security.principal import Role

# bootstrap 单租户企业（0027 引导；与 conftest/种子链一致）
ENTERPRISE_ID = UUID("00000000-0000-0000-0000-00000000d001")


class _RecordingAuditWriter:
    """记录 intent/outcome 调用；可注入失败。"""

    def __init__(self) -> None:
        self.intents: list[UUID] = []
        self.outcomes: list[tuple[UUID, str | None]] = []
        self.fail = False

    def write_decision(self, **_: object) -> None:
        return None

    def write_intent(self, *, intent_event_id: UUID, **_: object) -> None:
        if self.fail:
            raise AuditUnavailable("audit down")
        self.intents.append(intent_event_id)

    def write_outcome(
        self, *, intent_event_id: UUID, error_code: str | None = None, **_: object
    ) -> None:
        if self.fail:
            raise AuditUnavailable("audit down")
        self.outcomes.append((intent_event_id, error_code))


class _ExplodingStore:
    """在 write 时抛异常的对象存储（匹配 §7.2 write_if_absent 协议）。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> object:
        self.calls.append(f"write:{object_key}")
        raise RuntimeError("对象存储不可达")


class _CountingStore:
    def __init__(self) -> None:
        self.writes = 0
        self.objects: dict[str, bytes] = {}

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> object:
        from flow_api.publication.four_stage import StoredObjectRef

        self.writes += 1
        self.objects[object_key] = content
        return StoredObjectRef(
            stored_object_id=uuid4(),
            object_key=object_key,
            content_type=content_type,
            content_sha256=content_sha256,
            size_bytes=len(content),
        )


def _renderers() -> dict:
    return {
        PublicationFormat.HTML: lambda prepared, plan: b"<html>test</html>",
    }


def _audit_context() -> AuditContext:
    return AuditContext(
        actor_id="flow-dev-bp",
        role=Role.ANALYST,
        enterprise_id=ENTERPRISE_ID,
        correlation_id="corr-atomicity",
        action=Action.PUBLISHING_REPORT_PUBLISH,
        resource_scope="enterprise",
        resource_type="report_snapshot",
        resource_id="pending",
        model_boundary=None,
    )


def _request(
    report: ReportSnapshot, source_hash: str, formats=(PublicationFormat.HTML,)
) -> PublicationRequest:
    return PublicationRequest(
        publication_id=None,
        idempotency_key=f"key-{uuid4().hex[:8]}",
        resource_type="report_snapshot",
        resource_id=str(report.id),
        enterprise_id=ENTERPRISE_ID,
        source_payload_sha256=source_hash,
        formats=tuple(sorted(formats, key=lambda f: f.value)),
    )


def _cleanup_seed(session: Session, created: dict) -> None:
    """清理 seed 提交过的行（四阶段编排必须 commit）。

    snapshot 置 draft 规避 published append-only 防线；dim_period.month_key
    有唯一约束，本用例新建时必须在 teardown 删除，避免污染 canonical 测试。
    """
    report = created.get("report")
    if report is not None:
        fresh = session.get(ReportSnapshot, report.id)
        if fresh is not None:
            session.delete(fresh)
            session.flush()
    for key in ("value", "snapshot", "definition", "import_version", "batch"):
        obj = created.get(key)
        if obj is not None:
            session.delete(obj)
            session.flush()
    if created.get("period_created"):
        session.delete(created["period"])
        session.flush()
    session.commit()


def _seed_report_snapshot(session: Session) -> tuple[ReportSnapshot, dict]:
    """最小真实链：批次→导入版本→周期→指标快照→报告快照（含 frozen_view）。

    dim_period.month_key 唯一，同库多次运行时查无则建（维度行可复用）。
    """
    suffix = uuid4().hex[:8]
    created: dict = {}
    period = session.scalar(select(Period).where(Period.month_key == 202608))
    if period is None:
        period = Period(month_key=202608, year=2026, quarter=3, month=8)
        session.add(period)
        session.flush()
        created["period_created"] = True
    # 批次挂 bootstrap cycle（§4.1 lineage：batch → cycle → enterprise 可解析）
    from flow_api.enterprise.models import AnalysisCycle

    cycle = session.scalar(select(AnalysisCycle).limit(1))
    if cycle is None:
        session.execute(
            text("INSERT INTO enterprise (id) VALUES (:eid) ON CONFLICT (id) DO NOTHING"),
            {"eid": "00000000-0000-0000-0000-00000000d001"},
        )
        cycle = AnalysisCycle(enterprise_id=ENTERPRISE_ID, period="2026-08")
        session.add(cycle)
        session.flush()
    batch = AnalysisBatch(
        name=f"AuditAtomicity {suffix}",
        status="published",
        module_kind="internal",
        fact_context_version=2,
        analysis_cycle_id=cycle.id,
        created_by="flow-dev-bp",
    )
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
        status="failed",
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
    created.update(
        period=period,
        batch=batch,
        import_version=import_version,
        definition=definition,
        snapshot=snapshot,
        value=value,
        report=report,
    )
    return report, created


class TestFourStageAuditAtomicity:
    @pytest.fixture
    def session(self):
        from flow_api.infrastructure.db import get_session_factory

        s = get_session_factory()()
        yield s
        s.rollback()
        s.close()

    @pytest.fixture
    def audit(self) -> _RecordingAuditWriter:
        writer = _RecordingAuditWriter()
        register_audit_writer(writer)
        return writer

    @pytest.fixture
    def report_snapshot(self, session: Session):
        report, created = _seed_report_snapshot(session)
        session.commit()
        yield report
        _cleanup_seed(session, created)

    def test_prepare_failure_prevents_object_store(
        self, session: Session, audit: _RecordingAuditWriter
    ) -> None:
        """prepare 阶段失败（快照不存在）→ 对象存储零调用、attempt 零落库、无 intent 审计。"""
        store = _CountingStore()
        request = PublicationRequest(
            publication_id=None,
            idempotency_key="key-missing",
            resource_type="report_snapshot",
            resource_id="00000000-0000-0000-0000-000000000000",
            enterprise_id=ENTERPRISE_ID,
            source_payload_sha256="a" * 64,
            formats=(PublicationFormat.HTML,),
        )
        with pytest.raises(PublicationNotFound):
            prepare_intent(session, request, _audit_context())
        assert store.writes == 0
        assert audit.intents == []

    def test_source_hash_mismatch_is_freeze_conflict(
        self, session: Session, audit: _RecordingAuditWriter, report_snapshot: ReportSnapshot
    ) -> None:
        """冻结输入 hash 与请求不一致 → 409 语义（PublicationFreezeConflict），无副作用。"""
        store = _CountingStore()
        wrong_hash = "f" * 64
        with pytest.raises(PublicationFreezeConflict):
            prepare_intent(session, _request(report_snapshot, wrong_hash), _audit_context())
        assert store.writes == 0
        assert audit.intents == []

    def test_intent_commit_failure_is_not_durable(
        self, session: Session, audit: _RecordingAuditWriter, report_snapshot: ReportSnapshot
    ) -> None:
        """intent commit 失败 → PublicationIntentNotDurable（§7.5）；对象写 0 次。"""
        store = _CountingStore()
        source_hash = canonical_source_sha256(report_snapshot.frozen_view["view"])
        prepare_intent(session, _request(report_snapshot, source_hash), _audit_context())

        def broken_commit() -> None:
            raise RuntimeError("db connection lost")

        original_commit = session.commit
        session.commit = broken_commit  # type: ignore[method-assign]
        try:
            with pytest.raises(PublicationIntentNotDurable):
                try:
                    session.commit()  # 路由编排的 caller commit #1
                except Exception as error:  # noqa: BLE001
                    raise PublicationIntentNotDurable(str(error)) from error
        finally:
            session.commit = original_commit  # type: ignore[method-assign]
        session.rollback()
        assert store.writes == 0, "intent 未 durable 时 render/store 不得发生（§7.3-2）"

    def test_object_failure_creates_failure_outcome(
        self, session: Session, audit: _RecordingAuditWriter, report_snapshot: ReportSnapshot
    ) -> None:
        """对象写失败 → STORE_FAILED outcome 被捕获，failure finalize durable。"""
        store = _ExplodingStore()
        source_hash = canonical_source_sha256(report_snapshot.frozen_view["view"])
        prepared = prepare_intent(session, _request(report_snapshot, source_hash), _audit_context())
        session.commit()
        outcome = execute_object(prepared, _renderers(), store)
        assert store.calls, "store 应被调用过（写失败）"
        failure = build_publication_failure(outcome)
        assert failure is not None
        assert failure.error_code.value == "publication_object_store_failure"
        finalized = finalize_failure(session, prepared, outcome, failure, _audit_context())
        session.commit()
        assert finalized.status == "failed"
        attempt = session.get(PublicationAttempt, prepared.object_plans[0].attempt_id)
        assert attempt is not None
        assert attempt.status == "store_failed"
        assert attempt.error_code == "publication_object_store_failure"
        assert audit.outcomes and audit.outcomes[0][1] == "publication_object_store_failure"

    def test_four_stage_functions_do_not_commit(
        self, session: Session, audit: _RecordingAuditWriter, report_snapshot: ReportSnapshot
    ) -> None:
        """四阶段函数不应自行 commit（§7.2：事务边界由路由层控制）。"""
        commit_calls: list[int] = []
        original_commit = session.commit
        session.commit = lambda: commit_calls.append(1)  # type: ignore[method-assign]
        try:
            source_hash = canonical_source_sha256(report_snapshot.frozen_view["view"])
            prepared = prepare_intent(
                session, _request(report_snapshot, source_hash), _audit_context()
            )
            outcome = execute_object(prepared, _renderers(), _CountingStore())
            finalize_success(session, prepared, outcome, _audit_context())
            assert commit_calls == [], "四阶段函数不应自行 commit"
        finally:
            session.commit = original_commit  # type: ignore[method-assign]
            session.rollback()

    def test_intent_audit_failure_rolls_back_prepared_state(
        self, session: Session, report_snapshot: ReportSnapshot
    ) -> None:
        """intent 审计失败 → AuditUnavailable 上抛（路由层 rollback → 503 fail closed）。"""
        audit = _RecordingAuditWriter()
        audit.fail = True
        register_audit_writer(audit)
        source_hash = canonical_source_sha256(report_snapshot.frozen_view["view"])
        with pytest.raises(AuditUnavailable):
            prepare_intent(session, _request(report_snapshot, source_hash), _audit_context())
        session.rollback()
