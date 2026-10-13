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


def load_damai_operating_facts(
    path: Path, *, repo_root: Path
) -> list[OperatingFact]:
    """把大麦运营披露层（引用来源登记的菜鸟披露事实）转换为统一事实。

    2026-10-13 来源重整后：件量/占比/Non-IFRS 均为披露事实层（disclosed_fact），
    血缘指向 config/damai/source_facts_v1.yaml；Q1 stub 期间未经审计；
    演示期间（canonical FY2025/FY2026）无披露值，不生成事实（unavailable）。
    """

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    source_ref = str(payload["source_ref"])
    source_path = repo_root / source_ref
    if not source_path.is_file():
        raise ValueError(f"大麦运营事实血缘文件缺失: {source_ref}")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    stub_periods = set(payload.get("unaudited_periods") or ())
    entity_note = "大麦演示主体引用菜鸟披露（申请版本 draft）"
    facts: list[OperatingFact] = []

    def _damai_fact(
        *,
        metric_code: str,
        metric_name: str,
        period_label: str,
        value: Decimal | str | int | float,
        unit: str,
        caliber_note: str,
        source_page: str,
    ) -> OperatingFact:
        numeric_value: Decimal | None
        text_value: str | None
        if isinstance(value, str):
            numeric_value, text_value = None, value
        else:
            numeric_value, text_value = Decimal(str(value)), None
        is_stub = period_label in stub_periods
        return OperatingFact(
            company_name="大麦物流",
            stock_code="DAMAI.SYN",
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

    volume_pages = {
        "international_parcels": "23",
        "china_orders_fulfilled": "23",
    }
    for code, name in (
        ("international_parcels", "跨境及国际包裹量"),
        ("china_orders_fulfilled", "中国物流订单量"),
    ):
        unit = "百万件" if code == "international_parcels" else "百万单"
        for label, value in payload["operating_volume"][code].items():
            note = f"披露事实：菜鸟申请稿 Selected Operating Data；{entity_note}"
            if label in stub_periods:
                note += "；未经审计（原文 Unaudited）"
            facts.append(
                _damai_fact(
                    metric_code=code,
                    metric_name=name,
                    period_label=str(label),
                    value=value,
                    unit=unit,
                    caliber_note=note,
                    source_page=volume_pages[code],
                )
            )

    share_names = {
        "international_logistics": "国际物流收入占比",
        "china_logistics": "中国物流收入占比",
        "technology_and_other_services": "技术及其他服务收入占比",
    }
    shares = payload["business_line_revenue_share"]
    share_period = str(shares.get("period", "FY2023"))
    for code, value in shares.items():
        if code not in share_names:
            continue
        facts.append(
            _damai_fact(
                metric_code=f"business_line_share.{code}",
                metric_name=share_names[code],
                period_label=share_period,
                value=value,
                unit="比率",
                caliber_note=(
                    f"披露事实：FY2023 OUR SERVICE OFFERINGS 管理层口径，"
                    f"不延用于其他期间；{entity_note}"
                ),
                source_page="356",
            )
        )

    non_ifrs_names = {
        "adjusted_net_profit": ("经调整净利润", "人民币百万元"),
        "adjusted_net_profit_margin": ("经调整净利率", "比率"),
        "adjusted_ebitda": ("经调整 EBITDA", "人民币百万元"),
        "adjusted_ebitda_margin": ("经调整 EBITDA 利润率", "比率"),
    }
    for code, values in (payload.get("non_ifrs") or {}).items():
        if code not in non_ifrs_names:
            continue
        name, unit = non_ifrs_names[code]
        for label, value in values.items():
            facts.append(
                _damai_fact(
                    metric_code=code,
                    metric_name=name,
                    period_label=str(label),
                    value=value,
                    unit=unit,
                    caliber_note=(
                        f"Non-IFRS 管理层口径（MPM），不得与 IFRS 净利润混同；{entity_note}"
                    ),
                    source_page="21",
                )
            )
    return facts


__all__ = [
    "OperatingFact",
    "facts_for_period",
    "load_cainiao_operating_facts",
    "load_damai_operating_facts",
    "period_type",
    "previous_comparable_period",
]
