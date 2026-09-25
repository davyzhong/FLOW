"""大麦物流演示数据画像（Task 1，D052 方案 B / 规格 v1.1 §3）。

全部实体为 synthetic；金额单位人民币万元，计算全程 Decimal；
enterprise 复用固定 bootstrap UUID——当前授权契约整库单企业，
seed 时将该企业幂等配置为「大麦物流」。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Literal

PROFILE_VERSION = "damai-profile-v1"

# 当前授权契约（S01 2A）：整库单企业，复用固定 bootstrap UUID。
# seed 时幂等 UPDATE 该企业为大麦物流（不新建第二企业）。
DAMAI_BOOTSTRAP_ENTERPRISE_ID = uuid.UUID("00000000-0000-0000-0000-00000000d001")
DAMAI_ENTERPRISE_CODE = "damai-logistics"
DAMAI_ENTERPRISE_NAME = "大麦物流集团（synthetic 演示企业）"
DAMAI_DISCLOSURE_NOTE = (
    "synthetic 演示数据：规模锚取公开材料（菜鸟 FY2025 收入、京东物流毛利率），"
    "全部实体与交易均为虚构，不代表任何真实企业。"
)


def _month_range(start: str, count: int) -> tuple[str, ...]:
    year, month = (int(x) for x in start.split("-"))
    months: list[str] = []
    for _ in range(count):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return tuple(months)


PRIOR_MONTHS: Final[tuple[str, ...]] = _month_range("2024-09", 12)
ANALYSIS_MONTHS: Final[tuple[str, ...]] = _month_range("2025-09", 12)


@dataclass(frozen=True, slots=True)
class BusinessFamily:
    family_id: str
    name: str
    target_weight: Decimal


@dataclass(frozen=True, slots=True)
class PlantedEvent:
    """有意植入、可由确定性规则发现的分析事件（原因保持候选假设）。"""

    event_id: str
    kind: Literal[
        "peak_volume_price_pressure",
        "domestic_efficiency_gain",
        "major_customer_ar_deterioration",
        "region_revenue_below_budget",
        "profit_cash_divergence",
        "mix_shift_margin_change",
    ]
    scope: str
    note: str


@dataclass(frozen=True, slots=True)
class DamaiProfileV1:
    profile_version: str
    synthetic: bool
    enterprise_code: str
    enterprise_name: str
    enterprise_uuid: uuid.UUID
    disclosure_note: str
    prior_months: tuple[str, ...]
    analysis_months: tuple[str, ...]
    annual_revenue_target: tuple[Decimal, Decimal]  # 万元（低, 高）
    gross_margin_target: tuple[Decimal, Decimal]
    business_families: tuple[BusinessFamily, ...]
    business_units: tuple[str, ...]
    regions: tuple[str, ...]
    customers: tuple[str, ...]
    products: tuple[str, ...]
    planted_events: tuple[PlantedEvent, ...]
    customer_segments: tuple[str, ...]
    customer_assignments: dict[str, dict[str, object]]
    product_assignments: dict[str, dict[str, str]]


BUSINESS_FAMILIES: Final[tuple[BusinessFamily, ...]] = (
    BusinessFamily("international_cross_border", "国际与跨境物流", Decimal("0.474")),
    BusinessFamily("china_logistics", "中国物流", Decimal("0.462")),
    BusinessFamily("tech_and_other", "科技及其他服务", Decimal("0.064")),
)

BUSINESS_UNITS: Final[tuple[str, ...]] = (
    "国际供应链事业部",
    "跨境包裹事业部",
    "国内仓配事业部",
    "末端配送与冷链事业部",
)

REGIONS: Final[tuple[str, ...]] = (
    "华东区",
    "华南区",
    "华北区",
    "西南区",
    "中亚区",
    "海外区",
)

CUSTOMERS: Final[tuple[str, ...]] = tuple(
    f"匿名客户 {i:03d}（synthetic）" for i in range(1, 41)
)

PRODUCTS: Final[tuple[str, ...]] = (
    "跨境标准包裹",
    "跨境供应链专线",
    "海外仓履约",
    "国内仓配一体",
    "供应链干线",
    "末端配送",
    "冷链运输",
    "物流科技平台服务",
)

CUSTOMER_SEGMENTS: Final[tuple[str, ...]] = (
    "电商平台客户",
    "品牌直客",
    "中小企业客户",
    "政企与项目客户",
)

# 客群信用期（天）：账期越长 AR 余额系数越高
_SEGMENT_CREDIT_TERM_DAYS: Final[dict[str, int]] = {
    "电商平台客户": 30,
    "品牌直客": 45,
    "中小企业客户": 60,
    "政企与项目客户": 90,
}


def _build_customer_assignments() -> dict[str, dict[str, object]]:
    """40 客户固定主数据归属（spec §3.3）：客群/主区域/信用期按编号确定性轮换。"""

    assignments: dict[str, dict[str, object]] = {}
    for index in range(1, 41):
        segment = CUSTOMER_SEGMENTS[(index - 1) % len(CUSTOMER_SEGMENTS)]
        assignments[f"DM-CUST-{index:03d}"] = {
            "segment": segment,
            "primary_region": REGIONS[(index - 1) % len(REGIONS)],
            "credit_term_days": _SEGMENT_CREDIT_TERM_DAYS[segment],
        }
    return assignments


CUSTOMER_ASSIGNMENTS: Final[dict[str, dict[str, object]]] = _build_customer_assignments()

# 8 产品固定归属业务族与业务单元（spec §3.3 主数据映射）
PRODUCT_ASSIGNMENTS: Final[dict[str, dict[str, str]]] = {
    "P-01": {"family_id": "international_cross_border", "business_unit": "跨境包裹事业部"},
    "P-02": {"family_id": "international_cross_border", "business_unit": "国际供应链事业部"},
    "P-03": {"family_id": "international_cross_border", "business_unit": "国际供应链事业部"},
    "P-04": {"family_id": "china_logistics", "business_unit": "国内仓配事业部"},
    "P-05": {"family_id": "china_logistics", "business_unit": "国内仓配事业部"},
    "P-06": {"family_id": "china_logistics", "business_unit": "末端配送与冷链事业部"},
    "P-07": {"family_id": "china_logistics", "business_unit": "末端配送与冷链事业部"},
    "P-08": {"family_id": "tech_and_other", "business_unit": "国内仓配事业部"},
}

# 产品毛利率偏移（叠加在业务族基线之上；E6 组合变化的数值载体）
PRODUCT_MARGIN_OFFSET: Final[dict[str, Decimal]] = {
    "P-01": Decimal("0"),
    "P-02": Decimal("0.01"),
    "P-03": Decimal("-0.005"),
    "P-04": Decimal("0.005"),
    "P-05": Decimal("0"),
    "P-06": Decimal("-0.01"),
    "P-07": Decimal("0.005"),
    "P-08": Decimal("0.06"),
}

PLANTED_EVENTS: Final[tuple[PlantedEvent, ...]] = (
    PlantedEvent(
        "E1", "peak_volume_price_pressure", "国际与跨境物流",
        "旺季件量上升且运输单价上行：收入增长、毛利率承压",
    ),
    PlantedEvent(
        "E2", "domestic_efficiency_gain", "中国物流",
        "仓配效率改善，单位成本下降",
    ),
    PlantedEvent(
        "E3", "major_customer_ar_deterioration", "两个大客户",
        "31–60/61–90/90+ 账龄上升，回款恶化",
    ),
    PlantedEvent(
        "E4", "region_revenue_below_budget", "单一区域",
        "实际收入低于预算",
    ),
    PlantedEvent(
        "E5", "profit_cash_divergence", "全公司",
        "经营利润与经营现金流短期背离",
    ),
    PlantedEvent(
        "E6", "mix_shift_margin_change", "产品组合",
        "组合变化改变整体单均收入与毛利率",
    ),
)

DAMAI_PROFILE_V1 = DamaiProfileV1(
    profile_version=PROFILE_VERSION,
    synthetic=True,
    enterprise_code=DAMAI_ENTERPRISE_CODE,
    enterprise_name=DAMAI_ENTERPRISE_NAME,
    enterprise_uuid=DAMAI_BOOTSTRAP_ENTERPRISE_ID,
    disclosure_note=DAMAI_DISCLOSURE_NOTE,
    prior_months=PRIOR_MONTHS,
    analysis_months=ANALYSIS_MONTHS,
    annual_revenue_target=(
        Decimal("10500000.0000"),  # 1,050 亿 = 1,050 万万元
        Decimal("11500000.0000"),  # 1,150 亿
    ),
    gross_margin_target=(Decimal("0.09"), Decimal("0.11")),
    business_families=BUSINESS_FAMILIES,
    business_units=BUSINESS_UNITS,
    regions=REGIONS,
    customers=CUSTOMERS,
    products=PRODUCTS,
    planted_events=PLANTED_EVENTS,
    customer_segments=CUSTOMER_SEGMENTS,
    customer_assignments=CUSTOMER_ASSIGNMENTS,
    product_assignments=PRODUCT_ASSIGNMENTS,
)

__all__ = [
    "ANALYSIS_MONTHS",
    "BUSINESS_FAMILIES",
    "BUSINESS_UNITS",
    "CUSTOMER_ASSIGNMENTS",
    "CUSTOMER_SEGMENTS",
    "CUSTOMERS",
    "DAMAI_BOOTSTRAP_ENTERPRISE_ID",
    "DAMAI_PROFILE_V1",
    "PRIOR_MONTHS",
    "PRODUCTS",
    "PRODUCT_ASSIGNMENTS",
    "PRODUCT_MARGIN_OFFSET",
    "REGIONS",
]
