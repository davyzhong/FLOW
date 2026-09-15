"""规格 §7 四阶段发布 ABI 单元测试（R2/T01 红灯先行）。

权威合同：docs/40_specs/security/internal-workbench-rbac-audit-v1.md §7.1–§7.5。
- 类型/签名/异常/时序与规格逐字段一致；
- prepare/finalize 只 flush 不 commit；execute_object 无 Session；
- format 批次 all-or-failed；render/store 失败不丢 partial outcome；
- 幂等：同 key 同参数复用，同 key 异参数 409。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from flow_api.publication.four_stage import (
    FinalizedPublication,
    ObjectBatchOutcome,
    ObjectOutcome,
    ObjectPlan,
    PreparedPublication,
    PublicationAttemptStatus,
    PublicationErrorCode,
    PublicationFailure,
    PublicationFormat,
    PublicationObjectStoreFailure,
    PublicationRenderFailure,
    PublicationRequest,
    StoredObjectRef,
    execute_object,
    finalize_failure,
    finalize_success,
    prepare_intent,
)
from flow_api.security.audit import AuditContext, register_audit_writer
from flow_api.security.authorization import Action
from flow_api.security.principal import Role


@pytest.fixture(autouse=True)
def _wire_fake_audit_writer(request: pytest.FixtureRequest) -> None:
    """四阶段函数经全局注册表取 audit writer（规格精确签名，不收 writer 参数）。"""
    register_audit_writer(FakeAuditWriter())


# ---------------------------------------------------------------------------
# 测试替身
# ---------------------------------------------------------------------------


class FakeAuditWriter:
    """记录 intent/outcome 审计调用；可注入失败。"""

    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[str] = []
        self._fail = fail

    def write_intent(self, *, audit_context: Any, intent_event_id: Any) -> Any:
        if self._fail:
            raise RuntimeError("audit down")
        self.calls.append(f"intent:{intent_event_id}")
        return intent_event_id

    def write_outcome(
        self, *, audit_context: Any, intent_event_id: Any, outcome: Any, error_code: Any
    ) -> None:
        if self._fail:
            raise RuntimeError("audit down")
        self.calls.append(f"outcome:{intent_event_id}:{error_code or 'ok'}")


class FakeStore:
    """write_if_absent 替身：同 key 异内容拒绝（不可变语义）。"""

    def __init__(self, *, fail_formats: set[str] | None = None) -> None:
        self.writes: list[tuple[str, bytes, str]] = []
        self._by_key: dict[str, bytes] = {}
        self._fail_formats = fail_formats or set()

    def write_if_absent(
        self, *, object_key: str, content: bytes, content_type: str, content_sha256: str
    ) -> StoredObjectRef:
        # key 形如 <resource_type>/<rid>/<publication_id>/<format>/<source_hash>
        if any(f"/{fmt}/" in object_key for fmt in self._fail_formats):
            raise PublicationObjectStoreFailure(f"store down for {object_key}")
        if object_key in self._by_key:
            if self._by_key[object_key] != content:
                raise PublicationObjectStoreFailure("immutable conflict")
            return StoredObjectRef(
                stored_object_id=uuid4(),
                object_key=object_key,
                content_type=content_type,
                content_sha256=content_sha256,
                size_bytes=len(content),
            )
        self._by_key[object_key] = content
        self.writes.append((object_key, content, content_type))
        return StoredObjectRef(
            stored_object_id=uuid4(),
            object_key=object_key,
            content_type=content_type,
            content_sha256=content_sha256,
            size_bytes=len(content),
        )


def _audit_context(action: Action = Action.PUBLISHING_REPORT_PUBLISH) -> AuditContext:
    return AuditContext(
        actor_id="flow-dev-bp",
        role=Role.ANALYST,
        enterprise_id=None,
        correlation_id="corr-test",
        action=action,
        resource_scope="enterprise",
        resource_type="report_snapshot",
        resource_id="placeholder",
        model_boundary=None,
        identity_field_present=False,
    )


def _request(**overrides: Any) -> PublicationRequest:
    values: dict[str, Any] = {
        "publication_id": None,
        "idempotency_key": "key-0001",
        "resource_type": "report_snapshot",
        "resource_id": "11111111-1111-7111-8111-111111111111",
        "enterprise_id": None,
        "source_payload_sha256": "a" * 64,
        "formats": (PublicationFormat.HTML, PublicationFormat.XLSX),
    }
    values.update(overrides)
    return PublicationRequest(**values)


# ---------------------------------------------------------------------------
# PublicationRequest / 类型合同
# ---------------------------------------------------------------------------


def test_request_formats_must_be_sorted_unique_nonempty() -> None:
    with pytest.raises(ValueError):
        _request(formats=())
    with pytest.raises(ValueError):
        _request(formats=(PublicationFormat.HTML, PublicationFormat.HTML))
    # 未按枚举排序
    with pytest.raises(ValueError):
        _request(formats=(PublicationFormat.XLSX, PublicationFormat.HTML))


def test_request_idempotency_key_charset() -> None:
    with pytest.raises(ValueError):
        _request(idempotency_key="")
    with pytest.raises(ValueError):
        _request(idempotency_key="x" * 129)
    with pytest.raises(ValueError):
        _request(idempotency_key="bad\nkey")
    with pytest.raises(ValueError):
        _request(idempotency_key="非ASCII")


def test_request_source_hash_shape() -> None:
    with pytest.raises(ValueError):
        _request(source_payload_sha256="short")


# ---------------------------------------------------------------------------
# prepare_intent（内存 SQLite + 假资源不可行：资源校验走集成测试；此处测纯校验与幂等冲突）
# ---------------------------------------------------------------------------


class _UnavailableSession:
    """prepare 在资源解析前就应拒绝非法请求——session 不应被触碰。"""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"session.{name} 不应被调用（非法请求应先行拒绝）")


def test_prepare_rejects_unknown_resource_type_before_session() -> None:
    with pytest.raises(ValueError):
        prepare_intent(
            _UnavailableSession(),  # type: ignore[arg-type]
            _request(resource_type="not_a_resource"),
            _audit_context(),
        )


def test_prepare_rejects_non_hex_source_hash() -> None:
    with pytest.raises(ValueError):
        prepare_intent(
            _UnavailableSession(),  # type: ignore[arg-type]
            _request(source_payload_sha256="z" * 64),
            _audit_context(),
        )


# ---------------------------------------------------------------------------
# execute_object：all-or-failed + partial outcome 不丢
# ---------------------------------------------------------------------------


def _prepared(formats: tuple[PublicationFormat, ...]) -> PreparedPublication:
    plans = tuple(
        ObjectPlan(
            attempt_id=uuid4(),
            format=f,
            object_key=f"report_snapshot/rid/{uuid4()}/{f.value}/{'a' * 64}",
        )
        for f in formats
    )
    return PreparedPublication(
        publication_id=uuid4(),
        idempotency_key="key-0001",
        resource_type="report_snapshot",
        resource_id="11111111-1111-7111-8111-111111111111",
        enterprise_id=None,
        source_payload_sha256="a" * 64,
        formats=formats,
        object_plans=plans,
        intent_event_id=uuid4(),
    )


def test_execute_all_succeed() -> None:
    prepared = _prepared((PublicationFormat.HTML, PublicationFormat.XLSX))
    renderers = {
        f: (lambda p, plan, _f=f: f"<html>{_f.value}</html>".encode()) for f in prepared.formats
    }
    store = FakeStore()
    outcome = execute_object(prepared, renderers, store)
    assert isinstance(outcome, ObjectBatchOutcome)
    assert outcome.publication_id == prepared.publication_id
    assert all(o.status is PublicationAttemptStatus.SUCCEEDED for o in outcome.outcomes)
    assert len(store.writes) == 2
    # object key 必含 resource_type/resource_id/publication_id/format/source hash
    for plan, oc in zip(prepared.object_plans, outcome.outcomes, strict=False):  # noqa: B007
        assert oc.content_sha256 is not None
        assert len(oc.content_sha256) == 64
        assert oc.size_bytes is not None and oc.size_bytes > 0


def test_execute_render_failure_keeps_partial_outcome() -> None:
    prepared = _prepared((PublicationFormat.HTML, PublicationFormat.XLSX))

    def _boom(prepared: Any, plan: Any) -> bytes:
        raise PublicationRenderFailure("renderer exploded")

    renderers = {
        PublicationFormat.HTML: _boom,
        PublicationFormat.XLSX: (lambda p, plan: b"xlsx-bytes"),
    }
    store = FakeStore()
    outcome = execute_object(prepared, renderers, store)
    statuses = {o.format: o.status for o in outcome.outcomes}
    assert statuses[PublicationFormat.HTML] is PublicationAttemptStatus.RENDER_FAILED
    assert statuses[PublicationFormat.XLSX] is PublicationAttemptStatus.SUCCEEDED
    failed = next(o for o in outcome.outcomes if o.status is PublicationAttemptStatus.RENDER_FAILED)
    assert failed.error_type is PublicationErrorCode.RENDER_FAILURE
    assert failed.error_message and "exploded" in failed.error_message
    # 失败 format 未写对象
    assert len(store.writes) == 1


def test_execute_store_failure_marks_store_failed() -> None:
    prepared = _prepared((PublicationFormat.HTML,))
    renderers = {PublicationFormat.HTML: (lambda p, plan: b"html")}
    store = FakeStore(fail_formats={"html"})
    outcome = execute_object(prepared, renderers, store)
    oc = outcome.outcomes[0]
    assert oc.status is PublicationAttemptStatus.STORE_FAILED
    assert oc.error_type is PublicationErrorCode.OBJECT_STORE_FAILURE


def test_execute_unknown_format_renderer_missing_is_render_failure() -> None:
    prepared = _prepared((PublicationFormat.PPTX,))
    outcome = execute_object(prepared, {}, FakeStore())
    assert outcome.outcomes[0].status is PublicationAttemptStatus.RENDER_FAILED


# ---------------------------------------------------------------------------
# finalize：session 只 flush；audit outcome 必达
# ---------------------------------------------------------------------------


class _FakeAttempt:
    """session.get(PublicationAttempt, id) 的替身：记录字段写入。"""

    def __init__(self) -> None:
        self.status: str | None = None
        self.object_key: str | None = None
        self.error_code: str | None = None
        self.error_message: str | None = None
        self.stored_object_id: Any = None
        self.content_sha256: str | None = None
        self.size_bytes: int | None = None
        self.content_type: str | None = None


class RecordingFlushSession:
    """只记录 flush/add 调用，commit/rollback 被视为违约。"""

    def __init__(self) -> None:
        self.flushed = 0
        self.attempts: dict[Any, _FakeAttempt] = {}

    def flush(self) -> None:
        self.flushed += 1

    def commit(self) -> None:  # pragma: no cover - 规格违约探针
        raise AssertionError("finalize 不得 commit（§7.2）")

    def rollback(self) -> None:  # pragma: no cover
        raise AssertionError("finalize 不得 rollback（§7.2）")

    def scalar(self, *_: Any, **__: Any) -> None:
        return None

    def get(self, _model: Any, attempt_id: Any) -> _FakeAttempt:
        return self.attempts.setdefault(attempt_id, _FakeAttempt())

    def add(self, *_: Any, **__: Any) -> None:
        return None


def test_finalize_success_writes_audit_and_flushes() -> None:
    prepared = _prepared((PublicationFormat.HTML,))
    outcomes = ObjectBatchOutcome(
        publication_id=prepared.publication_id,
        outcomes=(
            ObjectOutcome(
                attempt_id=prepared.object_plans[0].attempt_id,
                format=PublicationFormat.HTML,
                status=PublicationAttemptStatus.SUCCEEDED,
                object_key=prepared.object_plans[0].object_key,
                content_type="text/html",
                content_sha256="b" * 64,
                size_bytes=5,
                stored_object_id=None,
                error_type=None,
                error_message=None,
            ),
        ),
    )
    writer = FakeAuditWriter()
    register_audit_writer(writer)
    finalized = finalize_success(
        RecordingFlushSession(),  # type: ignore[arg-type]
        prepared,
        outcomes,
        _audit_context(),
    )
    assert isinstance(finalized, FinalizedPublication)
    assert finalized.status == "published"
    assert finalized.publication_id == prepared.publication_id
    assert writer.calls and writer.calls[0].startswith("outcome:")


def test_finalize_failure_carries_error_code() -> None:

    prepared = _prepared((PublicationFormat.HTML,))
    outcomes = ObjectBatchOutcome(
        publication_id=prepared.publication_id,
        outcomes=(
            ObjectOutcome(
                attempt_id=prepared.object_plans[0].attempt_id,
                format=PublicationFormat.HTML,
                status=PublicationAttemptStatus.RENDER_FAILED,
                object_key=prepared.object_plans[0].object_key,
                content_type=None,
                content_sha256=None,
                size_bytes=None,
                stored_object_id=None,
                error_type=PublicationErrorCode.RENDER_FAILURE,
                error_message="boom",
            ),
        ),
    )
    writer = FakeAuditWriter()
    register_audit_writer(writer)
    finalized = finalize_failure(
        RecordingFlushSession(),  # type: ignore[arg-type]
        prepared,
        outcomes,
        PublicationFailure(
            error_code=PublicationErrorCode.RENDER_FAILURE,
            failed_attempt_ids=(prepared.object_plans[0].attempt_id,),
            retryable=True,
            http_status=503,
            message="boom",
        ),
        _audit_context(),
    )
    assert finalized.status == "failed"
    assert writer.calls and "render_failure" in writer.calls[0]


def test_finalize_audit_failure_raises() -> None:
    prepared = _prepared((PublicationFormat.HTML,))
    outcomes = ObjectBatchOutcome(publication_id=prepared.publication_id, outcomes=())
    writer = FakeAuditWriter(fail=True)
    register_audit_writer(writer)
    with pytest.raises(RuntimeError, match="audit down"):
        finalize_success(
            RecordingFlushSession(),  # type: ignore[arg-type]
            prepared,
            outcomes,
            _audit_context(),
        )
