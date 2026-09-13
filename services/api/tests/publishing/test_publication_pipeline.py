"""S01 §7.1 publishing 四阶段 ABI 单元测试。

mock Session + mock store + patch build_report_view；不连真实 DB/S3。
覆盖：
- prepare_intent 写入 PublicationAttempt status=running（flush 不 commit）
- execute_object 无 Session 调用 store.write_if_absent
- finalize_success 把 status=succeeded 写回 + 关联 stored_object
- finalize_failure 把 status=failed + error_message 写回
- pipeline 不自行 commit（mock session 不应收到 .commit()）
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from flow_api.publishing.pipeline import (
    PreparedPublication,
    PublicationFormatResult,
    PublicationPipeline,
    PublicationPipelineError,
    PublicationResult,
)


def _stub_view() -> Any:
    return object()


def _stub_renderers() -> dict[str, Any]:
    def _render(_view: Any, fmt: str) -> bytes:
        return f"<html>{fmt}</html>".encode()

    return {"html": _render, "xlsx": _render, "pptx": _render}


def _stub_store() -> MagicMock:
    store = MagicMock()
    store.object_key_for_sha.side_effect = lambda s: f"raw/{s[:2]}/{s}"
    store.write_if_absent.return_value = ("a" * 64, True)
    return store


def _stub_session() -> MagicMock:
    session = MagicMock()
    snapshot = MagicMock()
    snapshot.id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    snapshot.enterprise_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000002")
    session.get.return_value = snapshot
    scalar = MagicMock()
    scalar.return_value = None
    session.scalar = scalar
    return session


_SNAPSHOT_ID = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
_ENTERPRISE_ID = __import__("uuid").UUID("00000000-0000-0000-0000-000000000002")
_INTENT_ID = __import__("uuid").UUID("00000000-0000-0000-0000-000000000003")


@patch("flow_api.publishing.pipeline.build_report_view", return_value=_stub_view())
def test_prepare_intent_creates_running_attempt(_mock_view: Any) -> None:
    session = _stub_session()
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    prepared = pipeline.prepare_intent(
        session,
        snapshot_id=_SNAPSHOT_ID,
        actor_id="actor-1",
        correlation_id="corr-1",
        request_id="req-1",
        formats=("html", "xlsx"),
    )
    assert isinstance(prepared, PreparedPublication)
    assert prepared.formats == ("html", "xlsx")
    assert prepared.sequence == 1
    assert session.add.called
    assert session.flush.called
    assert not session.commit.called


@patch("flow_api.publishing.pipeline.build_report_view", return_value=_stub_view())
def test_prepare_intent_rejects_unknown_format(_mock_view: Any) -> None:
    session = _stub_session()
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
            formats=("html", "docx"),
        )
    except PublicationPipelineError as error:
        assert "docx" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


@patch("flow_api.publishing.pipeline.build_report_view", return_value=_stub_view())
def test_prepare_intent_rejects_empty_formats(_mock_view: Any) -> None:
    session = _stub_session()
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
            formats=(),
        )
    except PublicationPipelineError as error:
        assert "non-empty" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


@patch("flow_api.publishing.pipeline.build_report_view", return_value=_stub_view())
def test_prepare_intent_rejects_missing_snapshot(_mock_view: Any) -> None:
    session = _stub_session()
    session.get.return_value = None
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    try:
        pipeline.prepare_intent(
            session,
            snapshot_id=_SNAPSHOT_ID,
            actor_id="a",
            correlation_id="c",
            request_id="r",
            formats=("html",),
        )
    except PublicationPipelineError as error:
        assert "not found" in str(error)
    else:
        raise AssertionError("expected PublicationPipelineError")


def test_execute_object_calls_write_if_absent_with_expected_args() -> None:
    store = _stub_store()
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=store)
    prepared = PreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html", "xlsx"),
        idempotency_key=("publication", "snap", "1", "html,xlsx"),
        view=_stub_view(),
        sequence=1,
        intent_event_id=_INTENT_ID,
    )
    result = pipeline.execute_object(prepared)
    assert store.write_if_absent.call_count == 2
    kwargs1 = store.write_if_absent.call_args_list[0].kwargs
    assert kwargs1["content_type"] == "text/html; charset=utf-8"
    assert len(kwargs1["content_sha256"]) == 64
    assert isinstance(result, PublicationResult)
    assert len(result.formats) == 2
    for f in result.formats:
        assert f.status == "succeeded"
        assert f.content_sha256


def test_execute_object_partial_failure_continues_other_formats() -> None:
    def _render_html(_view: Any, fmt: str) -> bytes:
        if fmt == "html":
            return b"<html>ok</html>"
        raise RuntimeError("simulated renderer failure")

    store = _stub_store()
    pipeline = PublicationPipeline(
        renderers={"html": _render_html, "xlsx": _render_html, "pptx": _render_html},
        store=store,
    )
    prepared = PreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html", "xlsx", "pptx"),
        idempotency_key=("publication", "snap", "1", "html,pptx,xlsx"),
        view=_stub_view(),
        sequence=1,
        intent_event_id=_INTENT_ID,
    )
    result = pipeline.execute_object(prepared)
    statuses = {f.format: f.status for f in result.formats}
    assert statuses == {"html": "succeeded", "xlsx": "failed", "pptx": "failed"}


def test_execute_object_uses_write_if_absent_idempotently() -> None:
    store = _stub_store()
    store.write_if_absent.return_value = ("a" * 64, False)  # 已存在
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=store)
    prepared = PreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("publication", "snap", "1", "html"),
        view=_stub_view(),
        sequence=1,
        intent_event_id=_INTENT_ID,
    )
    result = pipeline.execute_object(prepared)
    # write_if_absent 返回 False (已存在) 时仍标 succeeded，幂等
    assert result.formats[0].status == "succeeded"
    # sha 由 hashlib 算（与 mock 返回无关）
    assert len(result.formats[0].content_sha256) == 64


def test_finalize_success_writes_outcome() -> None:
    session = _stub_session()
    attempt_row = MagicMock()
    attempt_row.format = "html"
    attempt_row.status = "running"
    attempt_row.stored_object_id = None
    # finalize_success 顺序：查 attempt → 查 stored_object
    scalars = iter([attempt_row, None])
    session.scalar = MagicMock(side_effect=lambda q: next(scalars))
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    prepared = PreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("publication", "snap", "1", "html"),
        view=_stub_view(),
        sequence=1,
        intent_event_id=_INTENT_ID,
    )
    result = PublicationResult(
        formats=(
            PublicationFormatResult(
                format="html",
                content_sha256="a" * 64,
                size_bytes=12,
                content_type="text/html; charset=utf-8",
                status="succeeded",
            ),
        )
    )
    pipeline.finalize_success(session, prepared, result)
    assert attempt_row.status == "succeeded"
    assert not session.commit.called


def test_finalize_failure_writes_failed_status_and_message() -> None:
    session = _stub_session()
    attempt_row = MagicMock()
    attempt_row.format = "html"
    attempt_row.status = "running"
    # finalize_failure 只查 attempt 一次
    session.scalar = MagicMock(return_value=attempt_row)
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=_stub_store())
    prepared = PreparedPublication(
        snapshot_id=_SNAPSHOT_ID,
        enterprise_id=_ENTERPRISE_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
        idempotency_key=("publication", "snap", "1", "html"),
        view=_stub_view(),
        sequence=1,
        intent_event_id=_INTENT_ID,
    )
    pipeline.finalize_failure(session, prepared, RuntimeError("boom"))
    assert attempt_row.status == "failed"
    assert "boom" in attempt_row.error_message
    assert not session.commit.called


@patch("flow_api.publishing.pipeline.build_report_view", return_value=_stub_view())
def test_pipeline_does_not_commit_throughout_lifecycle(_mock_view: Any) -> None:
    """完整四阶段跑一遍：pipeline 任何阶段都不调 session.commit()。"""
    session = _stub_session()
    store = _stub_store()
    pipeline = PublicationPipeline(renderers=_stub_renderers(), store=store)
    prepared = pipeline.prepare_intent(
        session,
        snapshot_id=_SNAPSHOT_ID,
        actor_id="a",
        correlation_id="c",
        request_id="r",
        formats=("html",),
    )
    result = pipeline.execute_object(prepared)
    attempt_row = MagicMock()
    attempt_row.format = "html"
    scalars = iter([attempt_row, None])
    session.scalar = MagicMock(side_effect=lambda q: next(scalars))
    pipeline.finalize_success(session, prepared, result)
    assert not session.commit.called
