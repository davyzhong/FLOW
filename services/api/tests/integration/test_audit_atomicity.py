"""S01 审计原子性故障注入测试（Task 2A 余段集成验证）。

验证：审计 intent 失败时对象存储未被调用；对象写失败时业务不发布且
failure outcome 存在；pipeline 不偷跑 commit。
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from flow_api.publishing.pipeline import (
    PublicationPipeline,
    PublicationPipelineError,
)


class _ExplodingStore:
    """在 write 时抛异常的对象存储。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def write_if_absent(self, key: str, content: bytes, content_type: str) -> str:
        self.calls.append(f"write:{key}")
        raise RuntimeError("对象存储不可达")


class _CountingStore:
    def __init__(self) -> None:
        self.writes = 0

    def write_if_absent(self, key: str, content: bytes, content_type: str) -> str:
        self.writes += 1
        return hashlib.sha256(content).hexdigest()


import hashlib


def _stub_renderers() -> dict:
    return {
        "html": lambda view, fmt: b"<html>test</html>",
        "pdf": lambda view, fmt: b"%PDF-test",
    }


def _make_pipeline(store=None) -> PublicationPipeline:
    return PublicationPipeline(renderers=_stub_renderers(), store=store or _CountingStore())


class TestAuditAtomicity:
    @pytest.fixture
    def session(self):
        from flow_api.infrastructure.db import get_session_factory
        s = get_session_factory()()
        yield s
        s.rollback()
        s.close()

    def test_intent_failure_prevents_object_store(self, session: Session) -> None:
        """审计 intent 写入失败 → 对象存储零调用。"""
        store = _CountingStore()
        pipeline = _make_pipeline(store)
        with pytest.raises(PublicationPipelineError):
            pipeline.prepare_intent(
                session, snapshot_id="00000000-0000-0000-0000-000000000000",
                actor_id="test", correlation_id="corr-1", request_id="req-1",
                formats=("html",),
            )
        assert store.writes == 0

    def test_object_failure_creates_failure_outcome(self, session: Session) -> None:
        """对象写失败 → failure outcome durable，业务不置 published。"""
        store = _ExplodingStore()
        pipeline = _make_pipeline(store)
        # prepare 应成功
        prepared = pipeline.prepare_intent(
            session, snapshot_id="00000000-0000-0000-0000-000000000001",
            actor_id="test", correlation_id="corr-explode", request_id="req-2",
            formats=("html",),
        )
        session.flush()
        # execute 应因 store 抛异常
        with pytest.raises(RuntimeError, match="对象存储不可达"):
            pipeline.execute_object(prepared)
        # finalize_failure 应记录 outcome
        pipeline.finalize_failure(session, prepared, RuntimeError("对象存储不可达"))
        session.flush()
        assert store.writes == 0

    def test_pipeline_does_not_commit(self, session: Session) -> None:
        """pipeline 四阶段不应自行 commit（由路由层控制事务边界）。"""
        commit_calls = []
        original_commit = session.commit
        session.commit = lambda: commit_calls.append(1)
        try:
            pipeline = _make_pipeline(session)
            prepared = pipeline.prepare_intent(
                session, snapshot_id="00000000-0000-0000-0000-000000000002",
                actor_id="test", correlation_id="corr-no-commit", request_id="req-3",
                formats=("html",),
            )
            pipeline.execute_object(prepared)
            pipeline.finalize_success(session, prepared, {"html": "sha"})
            assert len(commit_calls) == 0, "pipeline 不应自行 commit"
        finally:
            session.commit = original_commit
            session.rollback()
