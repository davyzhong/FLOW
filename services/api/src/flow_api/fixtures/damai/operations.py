"""大麦运营披露层（披露事实版，2026-10-13 来源重整）。

DAMAI.SYN 的 /operations 数据不再由 canonical 合成推导，而是直接引用
`config/damai/source_facts_v1.yaml` 来源登记中的菜鸟公开披露事实
（四分型的 disclosed_fact 层）：
- 分部序列：阿里年报/业绩公告 FY2019–FY2025 菜鸟分部收入与经调整 EBITA；
  FY2026 起菜鸟并入「所有其他」分部，无单独披露（unavailable，如实缺省，
  不得从混合组汇总反推）；
- 运营事实：申请稿 Selected Operating Data 件量（FY2021–FY2023 + 两个未经
  审计 Q1 stub）、FY2023 业务线收入占比、Non-IFRS 指标、网络快照；
- 演示期间（canonical FY2025/FY2026 月度）不属于披露期间，件量/占比不再
  用「收入 ÷ 客单价」推导补位（该口径已被 2026-10-12 审计判定为数量级与
  字段语义错误，见 U-CN-VOLUME-FINE-GRAINS）；
- 血缘：source_ref 指向来源登记，series/metrics 逐值携带 fact_id，可回溯
  原件 SHA 与页锚。

单位：分部序列/运营金额为人民币百万元；件量为百万件/百万单（披露原口径）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REGISTRY_REL = "config/damai/source_facts_v1.yaml"
REGISTRY_ID = "flow.damai_source_facts.v1"
_SEGMENT_YEARS = tuple(f"FY{year}" for year in range(2019, 2026))
_VOLUME_METRICS = ("international_parcels", "china_orders_fulfilled")
_VOLUME_UNITS = {"international_parcels": "百万件", "china_orders_fulfilled": "百万单"}
_VOLUME_NAMES = {
    "international_parcels": "跨境及国际包裹量",
    "china_orders_fulfilled": "中国物流订单量",
}
_SHARE_METRICS = (
    "international_logistics",
    "china_logistics",
    "technology_and_other_services",
)
_NON_IFRS_METRICS = (
    "adjusted_net_profit",
    "adjusted_net_profit_margin",
    "adjusted_ebitda",
    "adjusted_ebitda_margin",
)


def _load_registry() -> dict[str, Any]:
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / REGISTRY_REL
        if candidate.is_file():
            loaded: dict[str, Any] = yaml.safe_load(
                candidate.read_text(encoding="utf-8")
            )
            if loaded.get("registry_id") != REGISTRY_ID:
                raise ValueError(
                    f"来源登记 registry_id 不符：期望 {REGISTRY_ID}，"
                    f"实际 {loaded.get('registry_id')}"
                )
            return loaded
    raise FileNotFoundError(f"来源登记缺失：{REGISTRY_REL}（先运行构建脚本）")


def _fact_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {fact["fact_id"]: fact for fact in registry["facts"]}


def build_damai_operations_payloads() -> dict[str, dict[str, Any]]:
    """从来源登记生成 segment_series 与 operating_metrics（确定性，披露事实）。"""

    registry = _load_registry()
    facts = _fact_index(registry)
    sha_prefix = registry["sources"]["CNAI-IPO-2023"]["sha256"][:16]

    segment_series: dict[str, Any] = {
        "sample": "damai_segment_series",
        "company": "大麦物流（演示主体）——分部序列为菜鸟披露事实（演示引用）",
        "data_layer": "disclosed_fact",
        "unit": "人民币百万元",
        "entity_note": "分部序列为菜鸟披露事实（阿里年报/业绩公告，MPM 口径），大麦演示主体引用",
        "note": (
            "分部序列直接引用来源登记的菜鸟披露值（阿里年报/业绩公告分部披露，"
            "MPM 口径）：FY2026 起菜鸟重分类进「所有其他」分部，报告未单列菜鸟，"
            "不设 FY2026 值，也不得从混合组汇总反推。大麦演示报告期间的合成报表"
            "不属于本数据集。"
        ),
        "source_ref": REGISTRY_REL,
        "source_registry_id": REGISTRY_ID,
        "source_sha256_prefix": sha_prefix,
        "series": {},
        "unavailable_periods": {
            "FY2026": "菜鸟并入阿里「所有其他」分部，报告未单列（U-CN-FY2026-STANDALONE）",
        },
    }
    for period in _SEGMENT_YEARS:
        revenue_id = f"CN-SEG-{period}-SEGMENT_REVENUE"
        revenue_fact = facts.get(revenue_id)
        if revenue_fact is None:
            raise KeyError(f"来源登记缺少分部收入事实：{revenue_id}")
        entry: dict[str, Any] = {
            "segment_revenue": revenue_fact["value"],
            "fact_ids": {"segment_revenue": revenue_id},
        }
        ebita_id = f"CN-SEG-{period}-ADJUSTED_EBITA"
        ebita_fact = facts.get(ebita_id)
        if ebita_fact is not None:
            entry["adjusted_ebita"] = ebita_fact["value"]
            entry["fact_ids"]["adjusted_ebita"] = ebita_id
        segment_series["series"][period] = entry

    volume_facts = {
        metric: {
            fact["period"]: (fact_id, fact["value"])
            for fact_id, fact in facts.items()
            if fact_id.startswith("CN-OPS-") and fact["item_en"] == metric
        }
        for metric in _VOLUME_METRICS
    }
    volume_periods = sorted(
        {period for per_metric in volume_facts.values() for period in per_metric}
    )
    stub_periods = [period for period in volume_periods if period.startswith("Q1")]

    operating_metrics: dict[str, Any] = {
        "sample": "damai_operating_metrics",
        "data_layer": "disclosed_fact",
        "note": (
            "运营披露事实直接引用来源登记（菜鸟申请稿 Selected Operating Data、"
            "Non-IFRS、OUR SERVICE OFFERINGS 与网络快照）；Q1 stub 期间未经审计；"
            "演示期间（canonical FY2025/FY2026）无披露值，按 unavailable 处理，"
            "不再用收入推导件量。"
        ),
        "source_ref": REGISTRY_REL,
        "source_registry_id": REGISTRY_ID,
        "source_sha256_prefix": sha_prefix,
        "periods": volume_periods,
        "unaudited_periods": stub_periods,
        "operating_volume": {
            "unit": "百万件/百万单（披露原口径）",
            **{
                metric: {
                    period: value for period, (_fid, value) in per_metric.items()
                }
                for metric, per_metric in volume_facts.items()
            },
            "fact_ids": {
                metric: {period: fid for period, (fid, _v) in per_metric.items()}
                for metric, per_metric in volume_facts.items()
            },
        },
        "business_line_revenue_share": {
            "period": "FY2023",
            "note": "FY2023 管理层口径业务线收入占比（OUR SERVICE OFFERINGS）；不延用于其他期间",
            **{
                metric: facts[f"CN-SHARE-FY2023-{metric.upper()}"]["value"]
                for metric in _SHARE_METRICS
            },
            "fact_ids": {
                metric: f"CN-SHARE-FY2023-{metric.upper()}" for metric in _SHARE_METRICS
            },
        },
        "non_ifrs": {
            "note": "Non-IFRS 为管理层口径（MPM），调节表见申请稿；不得与 IFRS 净利润混同",
            **{
                metric: {
                    fact["period"]: fact["value"]
                    for fact_id, fact in facts.items()
                    if fact_id.startswith("CN-NIFRS-") and fact["item_en"] == metric
                }
                for metric in _NON_IFRS_METRICS
            },
        },
        "network_snapshot": _network_snapshot(),
        "unavailable": [
            {
                "scope": "演示期间（canonical FY2025/FY2026）的月度/客户/产品件量与业务线占比",
                "reason": (
                    "公开材料未披露该粒度与期间（U-CN-VOLUME-FINE-GRAINS）；"
                    "由收入推导件量的旧口径已废弃"
                ),
            }
        ],
    }
    return {
        "segment_series": segment_series,
        "operating_metrics": operating_metrics,
    }


def _network_snapshot() -> dict[str, Any]:
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / "docs/implementation/p5/cainiao_operating_metrics.yaml"
        if candidate.is_file():
            doc = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            snapshot = doc.get("network_snapshot") or {}
            return {
                "note": (
                    "菜鸟网络快照（披露原文，点值非年度序列）；大麦演示主体引用；"
                    "页锚见来源登记与申请稿 p243/245/274"
                ),
                **snapshot,
            }
    raise FileNotFoundError("cainiao_operating_metrics.yaml 缺失")


__all__ = ["build_damai_operations_payloads"]
