"""公开经营数据的 typed 中间层（O2）。

外部 YAML 只在本模块边界被理解；分析引擎消费统一的 OperatingFact，
不直接依赖来源文件的嵌套结构。期间筛选采用严格相等，年度、季度和时点
事实不做摊分或隐式替代。
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

PeriodType = Literal["fiscal_year", "fiscal_quarter", "point_in_time"]
Assurance = Literal["audited", "unaudited", "management_disclosure"]


class OperatingFact(BaseModel):
    """一个保持期间、量纲和来源的经营事实。"""

    model_config = ConfigDict(extra="forbid")

    company_name: str
    stock_code: str
    metric_code: str
    metric_name: str
    period_label: str
    period_type: PeriodType
    numeric_value: Decimal | None = None
    text_value: str | None = None
    unit: str
    assurance: Assurance
    is_stub: bool = False
    disclosure_level: Literal["L1_public"] = "L1_public"
    caliber_note: str
    source_ref: str
    source_sha256: str
    source_page: str

    @model_validator(mode="after")
    def exactly_one_value(self) -> OperatingFact:
        if (self.numeric_value is None) == (self.text_value is None):
            raise ValueError("经营事实必须且只能包含 numeric_value/text_value 之一")
        if len(self.source_sha256) != 64:
            raise ValueError("source_sha256 必须是完整 64 位摘要")
        return self


_ANNUAL = re.compile(r"^FY(?P<year>\d{4})$")
_QUARTER = re.compile(r"^Q(?P<quarter>[1-4])FY(?P<year>\d{4})$")


def period_type(period_label: str) -> PeriodType:
    if _ANNUAL.fullmatch(period_label):
        return "fiscal_year"
    if _QUARTER.fullmatch(period_label):
        return "fiscal_quarter"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", period_label):
        return "point_in_time"
    raise ValueError(f"不支持的经营事实期间: {period_label}")


def previous_comparable_period(period_label: str) -> str | None:
    """只返回同频可比期间；时点事实不擅自推导比较期。"""

    annual = _ANNUAL.fullmatch(period_label)
    if annual:
        return f"FY{int(annual.group('year')) - 1}"
    quarter = _QUARTER.fullmatch(period_label)
    if quarter:
        return f"Q{quarter.group('quarter')}FY{int(quarter.group('year')) - 1}"
    return None


def facts_for_period(
    facts: list[OperatingFact], period_label: str
) -> list[OperatingFact]:
    """严格期间筛选；不回退最新值、不跨频率替代。"""

    return [fact for fact in facts if fact.period_label == period_label]


def _source_digest(source_path: Path, expected_prefix: str) -> str:
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if not digest.startswith(expected_prefix):
        raise ValueError(
            f"来源摘要不匹配: expected prefix {expected_prefix}, got {digest}"
        )
    return digest


def _fact(
    *,
    metric_code: str,
    metric_name: str,
    period_label: str,
    value: Decimal | str | int | float,
    unit: str,
    source_ref: str,
    source_sha256: str,
    source_page: str,
    caliber_note: str,
    stub_periods: dict[str, object],
) -> OperatingFact:
    numeric_value: Decimal | None
    text_value: str | None
    if isinstance(value, str):
        numeric_value, text_value = None, value
    else:
        numeric_value, text_value = Decimal(str(value)), None
    is_stub = period_label in stub_periods
    return OperatingFact(
        company_name="菜鸟智慧物流网络",
        stock_code="CAINIAO",
        metric_code=metric_code,
        metric_name=metric_name,
        period_label=period_label,
        period_type=period_type(period_label),
        numeric_value=numeric_value,
        text_value=text_value,
        unit=unit,
        assurance="unaudited" if is_stub else "management_disclosure",
        is_stub=is_stub,
        caliber_note=caliber_note,
        source_ref=source_ref,
        source_sha256=source_sha256,
        source_page=source_page,
    )


def load_cainiao_operating_facts(
    path: Path, *, repo_root: Path
) -> list[OperatingFact]:
    """把菜鸟招股书经营披露转换为统一事实，不更改原始 YAML。"""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    source_ref = str(payload["source_pdf"])
    source_sha256 = _source_digest(
        repo_root / source_ref, str(payload["source_sha256_prefix"])
    )
    stub_periods: dict[str, object] = payload.get("stub_periods", {})
    facts: list[OperatingFact] = []

    metric_specs = (
        (
            "operating_volume",
            "international_parcels",
            "国际物流包裹量",
            "百万件",
            "22",
            "Selected Operating Data；期间累计值",
        ),
        (
            "operating_volume",
            "china_orders_fulfilled",
            "中国消费者物流履约单量",
            "百万单",
            "22",
            "Selected Operating Data；期间累计值",
        ),
        (
            "non_ifrs",
            "adjusted_net_profit",
            "经调整净利润",
            "人民币百万元",
            "18-20",
            "Non-IFRS 管理层口径；不得与 IFRS 净利润混同",
        ),
        (
            "non_ifrs",
            "adjusted_net_profit_margin",
            "经调整净利率",
            "比率",
            "18-20",
            "Non-IFRS 管理层口径；小数表示",
        ),
        (
            "non_ifrs",
            "adjusted_ebitda",
            "经调整 EBITDA",
            "人民币百万元",
            "18-20",
            "Non-IFRS 管理层口径；调节项目见原文",
        ),
        (
            "non_ifrs",
            "adjusted_ebitda_margin",
            "经调整 EBITDA 率",
            "比率",
            "18-20",
            "Non-IFRS 管理层口径；小数表示",
        ),
    )
    for group, code, name, unit, page, note in metric_specs:
        for label, value in payload[group][code].items():
            facts.append(
                _fact(
                    metric_code=code,
                    metric_name=name,
                    period_label=str(label),
                    value=value,
                    unit=unit,
                    source_ref=source_ref,
                    source_sha256=source_sha256,
                    source_page=page,
                    caliber_note=note,
                    stub_periods=stub_periods,
                )
            )

    share_names = {
        "international_logistics": "国际物流收入占比",
        "china_logistics": "中国物流收入占比",
        "technology_and_other_services": "技术及其他服务收入占比",
    }
    for code, value in payload["business_line_revenue_share"].items():
        facts.append(
            _fact(
                metric_code=f"business_line_share.{code}",
                metric_name=share_names[code],
                period_label="FY2023",
                value=value,
                unit="比率",
                source_ref=source_ref,
                source_sha256=source_sha256,
                source_page="253",
                caliber_note="管理层业务线口径，非 IFRS 分部报告",
                stub_periods=stub_periods,
            )
        )
    return facts


__all__ = [
    "OperatingFact",
    "facts_for_period",
    "load_cainiao_operating_facts",
    "period_type",
    "previous_comparable_period",
]
