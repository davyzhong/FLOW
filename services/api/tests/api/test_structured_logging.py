"""U8-C 结构化日志测试：JSON 行、脱敏、请求关联与旅程串联。"""

from __future__ import annotations

import contextlib
import json
import logging
from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from flow_api.infrastructure.logging import (
    JsonFormatter,
    bind_log_context,
    current_log_context,
    log_event,
    mask_sensitive,
)
from flow_api.main import app


class _JsonCapture(logging.Handler):
    """挂载 JsonFormatter 的捕获器：直接验证真实格式化产物。"""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[dict] = []
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        with contextlib.suppress(json.JSONDecodeError):
            self.lines.append(json.loads(self.format(record)))


@pytest.fixture
def json_log() -> Iterator[_JsonCapture]:
    capture = _JsonCapture()
    root = logging.getLogger()
    root.addHandler(capture)
    yield capture
    root.removeHandler(capture)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _json_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    records = []
    for record in caplog.records:
        formatted = caplog.handler.format(record)
        try:
            records.append(json.loads(formatted))
        except json.JSONDecodeError:
            continue
    return records


def test_mask_sensitive_by_key_name() -> None:
    payload = {
        "authorization": "Bearer abc",
        "access_token": "t-1",
        "Password": "p-1",
        "db_password": "p-2",
        "request_id": "r-1",
        "nested": {"api_key": "k-9", "sha256": "h"},
        "items": [{"client_secret": "s", "ok": 1}],
    }
    masked = mask_sensitive(payload)
    assert masked["authorization"] == "***"
    assert masked["access_token"] == "***"
    assert masked["Password"] == "***"
    assert masked["db_password"] == "***"
    assert masked["request_id"] == "r-1"
    assert masked["nested"]["api_key"] == "***"
    assert masked["nested"]["sha256"] == "h"
    assert masked["items"][0]["client_secret"] == "***"
    assert masked["items"][0]["ok"] == 1


def test_log_event_emits_json_with_context(json_log: _JsonCapture) -> None:
    logger = logging.getLogger("flow.test")
    bind_log_context(batch_id="b-1", build_id="u-2")
    log_event(logger, logging.INFO, "publication.succeeded", snapshot_id="s-3")
    records = json_log.lines
    assert records, "应产出可解析的 JSON 日志行"
    line = next(r for r in records if r.get("event") == "publication.succeeded")
    assert line["batch_id"] == "b-1"
    assert line["build_id"] == "u-2"
    assert line["snapshot_id"] == "s-3"
    assert line["level"] == "INFO"


def test_mask_applies_to_context_and_fields(json_log: _JsonCapture) -> None:
    logger = logging.getLogger("flow.test")
    bind_log_context(auth_token="raw-token")
    log_event(logger, logging.INFO, "download.served", client_password="raw-pass", sha256="h")
    records = json_log.lines
    line = next(r for r in records if r.get("event") == "download.served")
    assert line["auth_token"] == "***"
    assert line["client_password"] == "***"
    assert line["sha256"] == "h"


def test_middleware_assigns_request_id_and_logs(client: TestClient, json_log: _JsonCapture) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code in (200, 404)
    request_id = response.headers.get("X-Request-Id")
    assert request_id
    records = [r for r in json_log.lines if r.get("event") == "request.completed"]
    if not records:
        flow_api_logger = logging.getLogger("flow.api")
        root = logging.getLogger()
        print(
            "MW_DEBUG lines=", len(json_log.lines),
            "flow_api_effective=", flow_api_logger.getEffectiveLevel(),
            "flow_api_disabled=", flow_api_logger.disabled,
            "root_level=", root.level,
            "root_handlers=", [type(h).__name__ for h in root.handlers],
        )
    assert records, "请求完成应产出结构化日志"
    assert all(r.get("request_id") for r in records)
    # 中间件日志不得携带授权头原值
    assert all("authorization" not in json.dumps(r).lower() for r in records)


def test_journey_ids_flow_through_context(json_log: _JsonCapture) -> None:
    logger = logging.getLogger("flow.test")
    bind_log_context(batch_id=str(uuid4()))
    assert current_log_context().get("batch_id")
    log_event(logger, logging.INFO, "import.published")
    bind_log_context(snapshot_id=str(uuid4()))
    log_event(logger, logging.INFO, "report.snapshot_frozen")
    records = json_log.lines
    imported = next(r for r in records if r.get("event") == "import.published")
    frozen = next(r for r in records if r.get("event") == "report.snapshot_frozen")
    # 旅程串联：同批次 id 在冻结日志中仍可见（上下文累加，不互斥）
    assert imported["batch_id"]
    assert frozen["batch_id"] == imported["batch_id"]  # 旅程串联：批次 id 跨步骤保持
    assert frozen["snapshot_id"]
