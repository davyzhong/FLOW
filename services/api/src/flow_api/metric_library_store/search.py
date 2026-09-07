"""指标库搜索：代码 / 主名 / 别名解析到同一指标身份（P01，I07 前置）。

别名与主名同权重：resolve_metric_identity("FCF") 与
resolve_metric_identity("自由现金流") 必须返回同一条目（同一身份）。
匹配优先级：metric_code 精确 > 名称精确 > 别名精确 > 前缀模糊（仅代码与名称）。
"""

from __future__ import annotations

from typing import Any


def resolve_metric_identity(entries: list[Any], term: str) -> Any | None:
    """按代码/主名/别名解析指标身份；无匹配返回 None，多匹配取精确级最高。"""

    text = term.strip()
    if not text:
        return None

    def _aliases(entry: Any) -> list[str]:
        return [str(alias) for alias in (getattr(entry, "aliases", None) or [])]

    exact_code = [e for e in entries if getattr(e, "metric_code", "") == text]
    if exact_code:
        return exact_code[0]
    exact_name = [e for e in entries if getattr(e, "name", "") == text]
    if exact_name:
        return exact_name[0]
    exact_alias = [e for e in entries if text in _aliases(e)]
    if exact_alias:
        return exact_alias[0]

    lowered = text.lower()
    prefix = [
        e for e in entries
        if getattr(e, "metric_code", "").lower().startswith(lowered)
        or getattr(e, "name", "").startswith(text)
    ]
    if len(prefix) == 1:
        return prefix[0]
    if prefix:
        raise ValueError(f"搜索词 {text!r} 命中多个指标，需更精确")
    return None


__all__ = ["resolve_metric_identity"]
