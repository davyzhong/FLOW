"""结构化日志（U8-C）：JSON 行输出 + 旅程关联上下文 + 敏感字段脱敏。

设计约束（统一计划 U8-C）：
- 导入、构建、冻结、发布尝试、下载按 batch/build/snapshot/publication 等关联身份串起一次旅程；
- 原始敏感值（令牌、密钥、口令、授权头）不得进入日志；
- 零第三方依赖：stdlib logging + JSON 序列化，进程内 contextvar 传递关联字段。
"""

from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|cookie|credential)",
    re.IGNORECASE,
)
_MASK = "***"

_log_context: ContextVar[dict[str, Any] | None] = ContextVar("flow_log_context", default=None)


def bind_log_context(**fields: Any) -> None:
    """把旅程关联身份（batch_id/build_id/snapshot_id/publication_id/...）绑定到当前上下文。"""
    merged = {**(_log_context.get() or {}), **{k: v for k, v in fields.items() if v is not None}}
    _log_context.set(merged)


def current_log_context() -> dict[str, Any]:
    return dict(_log_context.get() or {})


def mask_sensitive(value: Any) -> Any:
    """递归脱敏：命中敏感键名（含子串，大小写不敏感）的值替换为 ***。"""
    if isinstance(value, dict):
        return {
            k: (_MASK if _SENSITIVE_KEY.search(str(k)) else mask_sensitive(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [mask_sensitive(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    """一行一条 JSON：时间、级别、logger、事件与合并后的关联字段（已脱敏）。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "flow_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        payload.update(current_log_context())
        return json.dumps(mask_sensitive(payload), ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """幂等配置根处理器；重复调用不叠加 handler。"""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, "_flow_structured", False):
            return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler._flow_structured = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(level)
    # flow.* 命名空间显式 INFO：测试进程里 pytest 会把 root 压到 WARNING，
    # 业务旅程事件（INFO）不能因此被丢弃。
    logging.getLogger("flow").setLevel(min(level, logging.INFO))


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """按结构化字段记一条事件日志；fields 与上下文合并后统一脱敏。"""
    logger.log(level, event, extra={"flow_fields": {"event": event, **fields}})
