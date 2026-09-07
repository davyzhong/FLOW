"""主题合同：四问统领、六专题展开、横向偿债（P02，I06/I07/I14）。

主题是"阅读路线 + 可用性合同"，不是新指标口径：
- metric_refs 只引用指标字典已登记代码（不另建第二套口径）；
- 每个主题声明 required_facts / allowed_grains / comparison_modes /
  unavailable_reasons——前提缺失时给出解释性空状态，不返回 0、不静默换期间；
- 四问与专题为多对多映射；essential 十指标是默认阅读子集（元数据标记）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

QuestionId = Literal["growth", "profit", "capital", "cash"]
UnavailableReasons = dict[str, str]


class EssentialMetric(BaseModel):
    """十指标默认子集条目：元数据标记，不改口径。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_code: str
    question: QuestionId
    alternative: str | None = None
    unavailable_when: str


class TopicContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    topic_id: str
    name: str
    questions: tuple[QuestionId, ...]
    metric_refs: tuple[str, ...]
    required_facts: tuple[str, ...]
    required_facts_optional: tuple[str, ...] = ()
    required_extra: tuple[str, ...] = ()
    allowed_grains: tuple[str, ...]
    comparison_modes: tuple[str, ...]
    charts: tuple[str, ...]
    unavailable_reasons: UnavailableReasons = Field(default_factory=dict)
    notes: str = ""


class QuestionRoute(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: QuestionId
    name: str
    default_metrics: tuple[str, ...]


class TopicsCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    topics_catalog_id: str
    status: str
    decision_ref: str
    created: str
    questions: tuple[QuestionRoute, ...]
    essential_metrics: tuple[EssentialMetric, ...]
    topics: tuple[TopicContract, ...]

    def route(self, question: QuestionId) -> QuestionRoute:
        return next(q for q in self.questions if q.question_id == question)


def load_topic_catalog(path: str | Path) -> TopicsCatalog:
    payload: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("topics catalog must be a mapping")
    payload["created"] = str(payload.get("created", ""))
    payload["questions"] = [
        {"question_id": key, **value} for key, value in payload.get("questions", {}).items()
    ]
    return TopicsCatalog.model_validate(payload)


def topics_catalog_hash(catalog: TopicsCatalog) -> str:
    payload = json.dumps(
        catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_metric_refs(catalog: TopicsCatalog, registered_codes: set[str]) -> list[str]:
    """metric_refs 与 essential 引用的代码必须已在指标字典登记；返回未知代码。"""

    referenced: set[str] = set()
    for topic in catalog.topics:
        referenced.update(topic.metric_refs)
    referenced.update(item.metric_code for item in catalog.essential_metrics)
    return sorted(referenced - registered_codes)


def topic_availability(
    topic: TopicContract,
    *,
    available_facts: set[str],
    available_extras: set[str] | None = None,
    allowed_grains: set[str] | None = None,
    comparison_modes: set[str] | None = None,
) -> list[str]:
    """主题可用性：返回解释性空状态的 reason key 列表；空列表 = 可用。

    - required_facts 任一缺失 → missing_fact；
    - required_extra（如 budget_version）缺失 → 对应 key（如 no_budget_version）；
    - 颗粒度不在 allowed_grains → grain_mismatch；
    - 比较场景不在 comparison_modes → comparison_unavailable。
    """

    extras = available_extras or set()
    reasons: list[str] = []
    if any(fact not in available_facts for fact in topic.required_facts):
        reasons.append("missing_fact")
    for extra in topic.required_extra:
        if extra not in extras:
            reasons.append(f"no_{extra}")
    if allowed_grains is not None and not allowed_grains & set(topic.allowed_grains):
        reasons.append("grain_mismatch")
    if comparison_modes is not None and not comparison_modes & set(topic.comparison_modes):
        reasons.append("comparison_unavailable")
    return reasons


def topics_for_question(catalog: TopicsCatalog, question: QuestionId) -> tuple[TopicContract, ...]:
    return tuple(topic for topic in catalog.topics if question in topic.questions)


def essential_for_question(
    catalog: TopicsCatalog, question: QuestionId
) -> tuple[EssentialMetric, ...]:
    return tuple(item for item in catalog.essential_metrics if item.question == question)


__all__ = [
    "EssentialMetric",
    "QuestionRoute",
    "TopicContract",
    "TopicsCatalog",
    "essential_for_question",
    "load_topic_catalog",
    "topic_availability",
    "topics_catalog_hash",
    "topics_for_question",
    "validate_metric_refs",
]
