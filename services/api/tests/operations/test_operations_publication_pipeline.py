"""S01 §7.1 operations publication 四阶段 ABI 单元测试。

只测 OperationsPublicationPipeline 与 publishing/pipeline.py 共享的 §7.1 行为：
- prepare_intent 校验 snapshot + enterprise_id
- execute_object 无 Session 调 store.write_if_absent
- finalize_success / finalize_failure 写 outcome（不 commit）
- 不支持的 format 拒绝
- operations report_type 必须是 operations_overview
"""
from __future__ import annotations

from unittest.mock import MagicMock

from flow_api.operations.pipeline import OperationsPublicationPipeline
from flow_api.publishing.pipeline import PublicationPipelineError


def _stub_store() -> MagicMock:
    store = MagicMock()
    store.object_key_for_sha.side_effect = lambda s: f"raw/{s[:2]}/{s}"
    store.write_if_absent.return_value = ("a" * 64, True)
    return store


def _stub_session(report_type: str = "operations_overview") -> MagicMock:
    session = MagicMock()
    snapshot = MagicMock()
    snapshot.id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    snapshot.enterprise_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000002")
    snapshot.report_type = report_type
    snapshot.payload = {"a": 1}
    session.get.return_value = snapshot
    scalar = MagicMock()
    scalar.return_value = None
    session.scalar = scalar
    return session


_SNAPSHOT_ID = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
_ENTERPRISE_ID = __import__("uuid").UUID("00000000-0000-0000-0000-000000000002")


def test_prepare_intent_creates_running_attempt_for_operations() -> None:
    session = _stub_session()
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    prepared = pipeline.prepare_intent(
        session,
        snapshot_id=_SNAPSHOT_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("pptx", "xlsx", "html"),
    )
    assert prepared.snapshot_id == _SNAPSHOT_ID
    assert prepared.enterprise_id == _ENTERPRISE_ID
    assert prepared.formats == ("pptx", "xlsx", "html")
    assert prepared.sequence == 1
    assert session.add.called
    assert session.flush.called
    assert not session.commit.called


def test_prepare_intent_rejects_non_operations_snapshot() -> None:
    session = _stub_session(report_type="other")
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
        )
    except PublicationPipelineError as error:
        assert "operations_overview" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


def test_prepare_intent_rejects_unknown_format() -> None:
    session = _stub_session()
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
            formats=("pptx", "docx"),
        )
    except PublicationPipelineError as error:
        assert "docx" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


def test_prepare_intent_rejects_missing_snapshot() -> None:
    session = _stub_session()
    session.get.return_value = None
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
        )
    except PublicationPipelineError as error:
        assert "not found" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


def test_execute_object_calls_store_write_if_absent() -> None:
    from unittest.mock import patch

    from flow_api.operations.pipeline import OperationsPreparedPublication

    store = _stub_store()
    pipeline = OperationsPublicationPipeline(store=store)
    session = _stub_session()
    prepared = OperationsPreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("operations", str(_SNAPSHOT_ID), "1"),
        payload={"a": 1},
        sequence=1,
        intent_event_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000003"),
    )
    # patch html renderer 避免 OperationsOverview 验证失败
    with patch(
        "flow_api.operations.pipeline.render_operations_html",
        return_value="<html>ops</html>",
    ):
        result = pipeline.execute_object(prepared)
    assert store.write_if_absent.called
    assert len(result.formats) == 1
    assert result.formats[0].status == "succeeded"
    assert not session.commit.called


def test_finalize_success_does_not_commit() -> None:
    session = _stub_session()
    attempt_row = MagicMock()
    attempt_row.format = "html"
    attempt_row.status = "running"
    attempt_row.stored_object_id = None
    scalars = iter([attempt_row, None])
    session.scalar = MagicMock(side_effect=lambda q: next(scalars))
    from flow_api.operations.pipeline import OperationsPreparedPublication
    from flow_api.publishing.pipeline import PublicationFormatResult, PublicationResult

    prepared = OperationsPreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("operations", str(_SNAPSHOT_ID), "1"),
        payload={"a": 1},
        sequence=1,
        intent_event_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000003"),
    )
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    pipeline.finalize_success(
        session,
        prepared,
        PublicationResult(
            formats=(
                PublicationFormatResult(
                    format="html",
                    content_sha256="a" * 64,
                    size_bytes=12,
                    content_type="text/html; charset=utf-8",
                    status="succeeded",
                ),
            )
        ),
    )
    assert attempt_row.status == "succeeded"
    assert not session.commit.called


def test_finalize_failure_does_not_commit() -> None:
    session = _stub_session()
    attempt_row = MagicMock()
    attempt_row.format = "html"
    attempt_row.status = "running"
    session.scalar = MagicMock(return_value=attempt_row)
    from flow_api.operations.pipeline import OperationsPreparedPublication

    prepared = OperationsPreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("operations", str(_SNAPSHOT_ID), "1"),
        payload={"a": 1},
        sequence=1,
        intent_event_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000003"),
    )
    pipeline = OperationsPublicationPipeline(store=_stub_store())
    pipeline.finalize_failure(session, prepared, RuntimeError("boom"))
    assert attempt_row.status == "failed"
    assert "boom" in attempt_row.error_message
    assert not session.commit.called
