#!/usr/bin/env python3
"""大麦 synthetic 演示指标覆盖矩阵生成器（Task B3）。

与 P5 公开真实财报矩阵同一引擎（复用 scripts/p5_query_facts.py 的 AST 求值），
事实来源换成发行版合成财报 fixtures/damai/statements/damai_fy*.yaml，
口径映射用 config/statements/item_alias_map_v1.yaml 的 damai_syn 段。

缺数不编造：指标公式首个缺失输入原样写入 missing；不用 0 补值。
产出 config/metrics/damai_demo_metric_coverage_v1.yaml（synthetic: true），
供 /api/v1/metric-library/coverage?dataset=damai 只读投影。

自检：引擎算出的毛利率必须与发行包 manifest 的 fiscal_year_summary 一致
（两路径一致才落盘，防映射错误）。
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from p5_query_facts import Engine, Missing, fmt_value

STATEMENTS_DIR = ROOT / "fixtures/damai/statements"
ALIAS_MAP = ROOT / "config/statements/item_alias_map_v1.yaml"
METRICS_YAML = ROOT / "docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml"
MANIFEST = ROOT / "fixtures/damai/manifest.json"
DATASET_OUT = ROOT / "config/metrics/damai_demo_metric_coverage_v1.yaml"

# 只用三张主表：所有者权益变动表是衍生表，项目与主表重复，不重复取数
SOURCE_STATEMENTS = ("合并利润表", "合并资产负债表", "合并现金流量表")
COMPANY = "damai_syn"
UNIT = "百万元"  # 发行版财报原始单位为元，事实库统一换算为百万元
# 发布工件时间戳与内容绑定；数据合同更新并重新审核时再前移，重复构建不漂移。
DATASET_GENERATED_AT = "2026-09-26T03:11:24+00:00"


def _mapped_item(entry: object) -> tuple[str, bool] | None:
    """别名映射条目 → (item_id, abs 语义)；未映射行返回 None（如实跳过）。"""

    if isinstance(entry, str):
        return entry, False
    if isinstance(entry, dict) and "item" in entry:
        return str(entry["item"]), bool(entry.get("abs"))
    return None


def build_damai_facts() -> list[dict[str, object]]:
    """发行版财报 × damai_syn 映射段 → P5 同构事实行（值换算为百万元）。"""

    alias_doc = yaml.safe_load(ALIAS_MAP.read_text(encoding="utf-8"))
    section = alias_doc["companies"][COMPANY]["statements"]
    facts: list[dict[str, object]] = []
    for fy in ("FY2025", "FY2026"):
        doc = yaml.safe_load(
            (STATEMENTS_DIR / f"damai_{fy.lower()}.yaml").read_text(encoding="utf-8")
        )
        for statement_type in SOURCE_STATEMENTS:
            spec = section[statement_type]
            roles: dict[str, str] = spec["roles"]
            mapping: dict[str, object] = spec["map"]
            for row in doc["statements"][statement_type]:
                mapped = _mapped_item(mapping.get(row["item"]))
                if mapped is None:
                    continue
                item_id, take_abs = mapped
                for column, role in roles.items():
                    raw = row.get(column)
                    if raw is None:
                        continue
                    value = Decimal(str(raw)) / Decimal(1000000)
                    if take_abs:
                        value = abs(value)
                    facts.append(
                        {
                            "company": COMPANY,
                            "period": fy,
                            "item_id": item_id,
                            "role": role,
                            "value": float(value),
                            "unit": UNIT,
                        }
                    )
    return facts


def main() -> None:
    facts = build_damai_facts()
    metrics_doc = yaml.safe_load(METRICS_YAML.read_text(encoding="utf-8"))
    engine = Engine({"facts": facts}, metrics_doc)
    snapshots = sorted({(f["company"], f["period"]) for f in facts})
    total_metrics = len(metrics_doc["metrics_general"])

    # 一致性自检：引擎毛利率 vs 发行包 manifest（两路径独立）
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for fy, summary in manifest["fiscal_year_summary"].items():
        engine_gm = engine.ev_metric("gross_margin", COMPANY, fy)
        manifest_gm = float(summary["gross_margin"])
        assert abs(engine_gm - manifest_gm) < 2e-4, (
            f"{fy} 毛利率两路径不一致: engine={engine_gm} vs manifest={manifest_gm}"
        )

    computable = {snapshot: 0 for snapshot in snapshots}
    metric_rows = []
    for metric in metrics_doc["metrics_general"]:
        cells = {}
        for company, period in snapshots:
            key = f"{company} {period}"
            try:
                value = engine.ev_metric(metric["metric_code"], company, period)
                cells[key] = {
                    "display": fmt_value(metric, value, UNIT),
                    "missing": None,
                }
                computable[(company, period)] += 1
            except Missing as error:
                cells[key] = {"display": None, "missing": str(error)}
        metric_rows.append(
            {
                "metric_code": metric["metric_code"],
                "name": metric["name"],
                "unit": metric["unit"],
                "cells": cells,
            }
        )

    dataset = {
        "dataset_id": "flow.damai_demo_metric_coverage.v1",
        "title": "大麦物流 synthetic 演示指标覆盖矩阵",
        "generator": "scripts/build_damai_metric_coverage.py",
        "generated_at": DATASET_GENERATED_AT,
        "facts_source": "fixtures/damai/statements/（发行版合成财报）",
        "alias_map": "config/statements/item_alias_map_v1.yaml#damai_syn",
        "synthetic": True,
        "caliber_notes": [
            "本矩阵为 synthetic 演示数据，非任何真实公司财报",
            "avg 为（期末+期初）/2、prior 为上年同期列；发行版无 FY2024，FY2025 同比指标无比较期、FY2026 使用 FY2025 比较列",
            "事实仅含三张主表的已映射行；权益变动表等衍生表不重复取数",
            "绝对额指标已按百万元换算为亿元展示",
            "缺口即真实缺口：缺少的事实输入原样标注，不以 0 补值",
        ],
        "snapshots": [
            {
                "company": company,
                "period": period,
                "unit": UNIT,
                "computable": computable[(company, period)],
                "total": total_metrics,
            }
            for company, period in snapshots
        ],
        "metrics": metric_rows,
    }
    DATASET_OUT.write_text(
        yaml.safe_dump(dataset, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    for company, period in snapshots:
        print(f"  {company} {period}: {computable[(company, period)]}/{total_metrics} 指标可计算")
    print(f"written -> {DATASET_OUT}")


if __name__ == "__main__":
    main()
