"""MPM 分类语义（P01，订正 C02）：企业管理口径与 IFRS 18 监管定义分开。

规则（tests/metrics/test_mpm_classification.py 有正反例）：
- `mpm: true` 是监管级断言（该指标已在公开财报中列报为管理定义业绩指标，
  且具备调节关系），必须携带结构化判定 `mpm_review`，其中
  determination == "verified_applicable" 且 verified 为真；
- 仅"管理常用"（如 FCF、EBITDA 家族）只允许 determination == "candidate"，
  且 mpm 必须为 false——是否属 MPM 依公司实际财报逐例判定，不静态授予；
- 准则定义小计、成本口径、内部经营指标 determination == "not_applicable"。
"""

from __future__ import annotations

from typing import Any

_MPM_REVIEW_REQUIRED = ("determination", "verified")
_DETERMINATIONS = ("verified_applicable", "candidate", "management_caliber", "not_applicable")


def review_violation(entry: Any) -> str | None:
    """返回条目 MPM 标注的问题描述；合规返回 None。"""

    code = getattr(entry, "metric_code", "<unknown>")
    if not getattr(entry, "mpm", False):
        review = getattr(entry, "mpm_review", None)
        if review is None:
            return None
        if not isinstance(review, dict):
            return f"{code}: mpm_review 必须为结构化判定对象"
        determination = review.get("determination")
        if determination not in _DETERMINATIONS:
            return f"{code}: mpm_review.determination 非法（{determination!r}）"
        return None
    review = getattr(entry, "mpm_review", None)
    if not isinstance(review, dict):
        return f"{code}: mpm=true 缺少结构化判定 mpm_review（裸布尔无效）"
    for field in _MPM_REVIEW_REQUIRED:
        if field not in review:
            return f"{code}: mpm_review 缺少必填字段 {field}"
    if review.get("determination") != "verified_applicable":
        return (
            f"{code}: mpm=true 但 determination={review.get('determination')!r}；"
            "只有 verified_applicable 可携带监管 MPM 标签"
        )
    if review.get("verified") is not True:
        return f"{code}: mpm=true 但判定未经核验（verified 非 true）"
    if not str(review.get("basis", "")).strip():
        return f"{code}: mpm=true 缺少判定依据（basis）"
    return None


def assert_mpm_labels_valid(entries: list[Any]) -> None:
    """批量校验；存在违规即抛 ValueError（聚合全部问题便于一次修复）。"""

    violations = [text for entry in entries if (text := review_violation(entry))]
    if violations:
        raise ValueError("MPM 标注违规：" + "；".join(violations))


__all__ = ["assert_mpm_labels_valid", "review_violation"]
