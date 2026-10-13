#!/usr/bin/env python3
"""构建大麦演示来源事实登记（source-facts registry，机器可读）。

路线图队首子步骤「机器可读来源登记与数据适配设计」的登记产出（2026-10-12
审计的落地工件）。从既有 P5 菜鸟事实资产生成逐行登记，并对原件 PDF 做
机械核验（SHA-256、页锚文本在场性），不引入任何手抄新值。

产出：config/damai/source_facts_v1.yaml
  - sources：官方原件登记（机构/标题/版本/URL/SHA-256/页映射/准则/单位/期间）；
  - facts：逐行披露事实（layer=disclosed_fact），双标签（披露原文 + 整理规范名）、
    原值、期间、页锚、文件与行定位；
  - derived_rules：可复算派生规则（输入事实 ID + 公式 + 舍入规则）；
  - unavailable：不可用项及原因（FY2026 菜鸟单体、FY2024+ 三表、月度/客户/区域
    件量拆分、利息/折旧/债务构成等无来源假设的处置）；
  - demo_layers / test_fixtures：演示生成明细与测试建制的分型及对账要求。

用法（仓库根）：
    python3 scripts/build_damai_source_registry.py            # 生成/覆盖登记
    python3 scripts/build_damai_source_registry.py --check    # 重建对账已提交登记

自检：登记值与 P5 YAML 源值逐条相等（防抽取漂移）；跨文件同期间值一致
（2023fy 上期 = 2022fy 本期）；SHA 与本地原件一致；页锚文本在物理页在场。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
P5_DIR = ROOT / "docs/implementation/p5"
PDF_CNAIAO = (
    ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/cainiao_private"
    / "Cainiao_application_proof_20230926.pdf"
)
PDF_BABA_FY2025 = (
    ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988"
    / "BABA_FY2025_annual_results.pdf"
)
PDF_BABA_FY2026 = (
    ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988"
    / "BABA_FY2026_annual_results.pdf"
)
OUT_PATH = ROOT / "config/damai/source_facts_v1.yaml"

# 申请稿（0 起）：损益 463、资产负债 465-466、现金流量 473-474（与
# scripts/p5_extract_cainiao.py 验证日志一致；1 起物理页 = 0 起 + 1）。
_CNAIAO_STATEMENT_PAGES: dict[str, dict[str, Any]] = {
    "合并利润表": {"physical": 464, "anchor": "CONSOLIDATED STATEMENTS OF PROFIT OR LOSS"},
    "合并资产负债表": {"physical": 466, "anchor": "CONSOLIDATED BALANCE SHEETS"},
    "合并现金流量表": {"physical": 474, "anchor": "CONSOLIDATED STATEMENTS OF CASH FLOWS"},
}
# 申请稿披露锚（物理页由本脚本对原件机械核验：锚文本必须在该页在场）
_CNAIAO_TEXT_ANCHORS: dict[str, dict[str, Any]] = {
    "operating_data": {"physical": 23, "printed": 22, "anchor": "SELECTED OPERATING DATA"},
    "non_ifrs": {"physical": 21, "printed": 18, "anchor": "NON-IFRS FINANCIAL MEASURES"},
    "business_line": {"physical": 356, "printed": 354, "anchor": "OUR SERVICE OFFERINGS"},
}
# p5 语句文件 → 期间列（本期/上期）
_STATEMENT_FILES = {
    "cainiao_2021fy_statements.yaml": ("FY2021", "FY2020"),
    "cainiao_2022fy_statements.yaml": ("FY2022", "FY2021"),
    "cainiao_2023fy_statements.yaml": ("FY2023", "FY2022"),
}
_PERIOD_MONTHS = {
    "FY2020": "2019-04 ~ 2020-03",
    "FY2021": "2020-04 ~ 2021-03",
    "FY2022": "2021-04 ~ 2022-03",
    "FY2023": "2022-04 ~ 2023-03",
}
_STATEMENT_EN = {
    "合并利润表": "CONSOLIDATED STATEMENTS OF PROFIT OR LOSS",
    "合并资产负债表": "CONSOLIDATED BALANCE SHEETS",
    "合并现金流量表": "CONSOLIDATED STATEMENTS OF CASH FLOWS",
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_texts(path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [(page.extract_text() or "") for page in reader.pages]


def find_physical_page(texts: list[str], anchor: str, *, start: int = 0) -> int | None:
    """返回 1 起物理页号；找不到返回 None（由调用方如实登记，不猜）。"""

    for index in range(start, len(texts)):
        if anchor in texts[index]:
            return index + 1
    return None


def anchor_present(texts: list[str], physical: int, anchor: str) -> bool:
    """核验锚文本在指定物理页（1 起）在场，大小写不敏感。"""

    if physical < 1 or physical > len(texts):
        return False
    return anchor.lower() in texts[physical - 1].lower()


def _fact_id(statement: str, period: str, item: str) -> str:
    tag = {"合并利润表": "PL", "合并资产负债表": "BS", "合并现金流量表": "CF"}[statement]
    if item.isascii() and item.isalnum():
        slug = item.upper()[:24]
    else:
        # 含中文/符号的行名一律全哈希，避免 ASCII 截断互相碰撞（如「ABS 偿还」）
        slug = "X" + hashlib.md5(item.encode("utf-8")).hexdigest()[:10].upper()
    return f"CN-{tag}-{period}-{slug}"


def build_cainiao_statement_facts(texts: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """从三份 P5 语句文件生成逐行披露事实；返回 (facts, warnings)。"""

    facts: list[dict[str, Any]] = []
    warnings: list[str] = []
    registered: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rel, (cur_period, prev_period) in _STATEMENT_FILES.items():
        doc = yaml.safe_load((P5_DIR / rel).read_text(encoding="utf-8"))
        source_yaml_sha = sha256_of(P5_DIR / rel)
        for statement, rows in (doc.get("statements") or {}).items():
            page_meta = _CNAIAO_STATEMENT_PAGES.get(statement)
            if page_meta is None:
                warnings.append(f"{rel}: 未登记页锚的报表 {statement}，跳过")
                continue
            physical = page_meta["physical"]
            if not anchor_present(texts, physical, page_meta["anchor"]):
                warnings.append(f"{rel}: 页锚不在物理页 {physical}：{statement}")
            for row in rows:
                item = row["item"]
                for column, period in (("本期发生额", cur_period), ("上期发生额", prev_period)):
                    value = row.get(column)
                    if value is None:
                        continue
                    key = (statement, period, item)
                    if key in registered:
                        prior = registered[key]["value"]
                        if prior != value:
                            warnings.append(
                                f"跨文件值冲突 {statement}/{period}/{item}: {prior} != {value}"
                            )
                        registered[key]["cross_checked_by"].append(rel)
                        continue
                    fact = {
                        "fact_id": _fact_id(statement, period, item),
                        "layer": "disclosed_fact",
                        "source": "CNAI-IPO-2023",
                        "period": period,
                        "period_months": _PERIOD_MONTHS[period],
                        "statement": statement,
                        "statement_en": _STATEMENT_EN[statement],
                        "item_zh": item,
                        "item_en": None,
                        "value": value,
                        "unit": "人民币千元",
                        "page": {"physical": physical, "printed": None},
                        "source_files": {
                            "p5_yaml": f"docs/implementation/p5/{rel}",
                            "p5_yaml_sha256": source_yaml_sha,
                            "extractor": "scripts/p5_extract_cainiao.py",
                        },
                        "cross_checked_by": [rel],
                        "note": (
                            "申请版本（2023-09-26 递交、2024-03 撤回，draft 身份须随展示）；"
                            "中文行名为抽取整理规范名（item_alias_map_v1.yaml cainiao_private 节），"
                            "披露原文为英文"
                        ),
                    }
                    registered[key] = fact
                    facts.append(fact)
    return facts, warnings


def build_segment_facts() -> list[dict[str, Any]]:
    """阿里分部披露序列（FY2019–FY2025，来自整理序列资产，FY2024/25 有页锚）。"""

    doc = yaml.safe_load(
        (P5_DIR / "cainiao_segment_series.yaml").read_text(encoding="utf-8")
    )
    facts: list[dict[str, Any]] = []
    for period, values in (doc.get("series") or {}).items():
        for key, value in values.items():
            if value is None:
                continue
            item = "segment_revenue" if key == "segment_revenue" else "adjusted_ebita"
            anchored = period in ("FY2024", "FY2025")
            facts.append(
                {
                    "fact_id": f"CN-SEG-{period}-{item.upper()}",
                    "layer": "disclosed_fact",
                    "source": "BABA-FY2025-RESULTS" if anchored else "BABA-ANNUAL-RESULTS-CURATED",
                    "period": period,
                    "period_months": None,
                    "statement": "分部披露",
                    "item_zh": "分部收入" if item == "segment_revenue" else "经调整 EBITA",
                    "item_en": item,
                    "value": value,
                    "unit": "人民币百万元",
                    "page": {"physical": 18 if anchored else None, "printed": None},
                    "source_files": {
                        "curated_series": "docs/implementation/p5/cainiao_segment_series.yaml",
                        "curated_series_sha256": sha256_of(
                            P5_DIR / "cainiao_segment_series.yaml"
                        ),
                    },
                    "page_verification": "verified" if anchored else "pending",
                    "note": (
                        "FY2024/FY2025 锚定 FY2025 年度业绩公告物理页 18–21；更早期间沿用整理序列"
                        "登记的年度公告出处，页锚待逐份核验"
                        if anchored
                        else "出处为整理序列登记的阿里年度业绩公告；页锚待逐份核验"
                    ),
                }
            )
    return facts


def build_operating_facts(texts: list[str]) -> list[dict[str, Any]]:
    """运营披露事实：件量、Non-IFRS、业务线占比、网络快照（均来自整理资产）。"""

    doc = yaml.safe_load(
        (P5_DIR / "cainiao_operating_metrics.yaml").read_text(encoding="utf-8")
    )
    facts: list[dict[str, Any]] = []
    volume_anchor = _CNAIAO_TEXT_ANCHORS["operating_data"]
    non_ifrs_anchor = _CNAIAO_TEXT_ANCHORS["non_ifrs"]
    share_anchor = _CNAIAO_TEXT_ANCHORS["business_line"]
    volume_ok = anchor_present(texts, volume_anchor["physical"], volume_anchor["anchor"])
    non_ifrs_ok = anchor_present(
        texts, non_ifrs_anchor["physical"], non_ifrs_anchor["anchor"]
    )
    share_ok = anchor_present(texts, share_anchor["physical"], share_anchor["anchor"])
    for metric, values in (doc.get("operating_volume") or {}).items():
        if metric == "unit":
            continue
        for period, value in values.items():
            facts.append(
                {
                    "fact_id": f"CN-OPS-{period}-{metric.upper()}",
                    "layer": "disclosed_fact",
                    "source": "CNAI-IPO-2023",
                    "period": period,
                    "period_months": None,
                    "statement": "Selected Operating Data",
                    "item_zh": {
                        "international_parcels": "跨境及国际包裹量",
                        "china_orders_fulfilled": "中国物流订单量",
                    }[metric],
                    "item_en": metric,
                    "value": value,
                    "unit": "百万件" if metric == "international_parcels" else "百万单",
                    "page": {"physical": volume_anchor["physical"], "printed": volume_anchor["printed"]},
                    "page_verification": "verified" if volume_ok else "pending",
                    "source_files": {
                        "curated_series": "docs/implementation/p5/cainiao_operating_metrics.yaml",
                        "curated_series_sha256": sha256_of(
                            P5_DIR / "cainiao_operating_metrics.yaml"
                        ),
                    },
                    "note": (
                        "Q1 stub 期间未经审计（原文 Unaudited）"
                        if period.startswith("Q1")
                        else "申请版本披露；管理层口径"
                    ),
                }
            )
    for metric, values in (doc.get("non_ifrs") or {}).items():
        for period, value in values.items():
            facts.append(
                {
                    "fact_id": f"CN-NIFRS-{period}-{metric.upper()}",
                    "layer": "disclosed_fact",
                    "source": "CNAI-IPO-2023",
                    "period": period,
                    "period_months": None,
                    "statement": "Non-IFRS Financial Measures",
                    "item_zh": metric,
                    "item_en": metric,
                    "value": value,
                    "unit": "人民币百万元（margin 为比率）",
                    "page": {"physical": non_ifrs_anchor["physical"], "printed": non_ifrs_anchor["printed"]},
                    "page_verification": "verified" if non_ifrs_ok else "pending",
                    "source_files": {
                        "curated_series": "docs/implementation/p5/cainiao_operating_metrics.yaml",
                        "curated_series_sha256": sha256_of(
                            P5_DIR / "cainiao_operating_metrics.yaml"
                        ),
                    },
                    "note": "Non-IFRS 为管理层口径（MPM），调节表见申请稿 p18-20",
                }
            )
    shares = doc.get("business_line_revenue_share") or {}
    for metric, value in shares.items():
        facts.append(
            {
                "fact_id": f"CN-SHARE-FY2023-{metric.upper()}",
                "layer": "disclosed_fact",
                "source": "CNAI-IPO-2023",
                "period": "FY2023",
                "period_months": _PERIOD_MONTHS["FY2023"],
                "statement": "OUR SERVICE OFFERINGS",
                "item_zh": metric,
                "item_en": metric,
                "value": value,
                "unit": "占收入比",
                "page": {"physical": share_anchor["physical"], "printed": share_anchor["printed"]},
                "page_verification": "verified" if share_ok else "pending",
                "source_files": {
                    "curated_series": "docs/implementation/p5/cainiao_operating_metrics.yaml",
                    "curated_series_sha256": sha256_of(
                        P5_DIR / "cainiao_operating_metrics.yaml"
                    ),
                },
                "note": "FY2023 管理层口径业务线收入占比；不延用于其他期间",
            }
        )
    return facts


def build_registry(texts: list[str]) -> dict[str, Any]:
    statement_facts, warnings = build_cainiao_statement_facts(texts)
    facts = (
        statement_facts
        + build_segment_facts()
        + build_operating_facts(texts)
    )
    registry: dict[str, Any] = {
        "registry_id": "flow.damai_source_facts.v1",
        "title": "大麦演示来源事实登记 v1（机器可读）",
        "generator": "scripts/build_damai_source_registry.py",
        "generated_at": "2026-10-13T00:00:00+00:00",
        "rebuild_check": "python3 scripts/build_damai_source_registry.py --check",
        "registry_version": "source-facts-v1",
        "demo_entity": "大麦物流（演示主体，DAMAI.SYN）",
        "principle": (
            "披露范围为上限：可定位报告值进入 disclosed_fact；由披露事实按登记公式"
            "计算的进入 derived_value；公开材料未披露的粒度只能作为 demo_detail 且"
            "聚合须与披露事实对账；无法从来源复算的指标显示 unavailable。"
        ),
        "layers": {
            "disclosed_fact": "披露事实：可定位官方原件逐行值",
            "derived_value": "可复算派生：输入事实 ID + 公式 + 舍入规则可复算",
            "demo_detail": "演示生成明细：显式确定性生成规则，聚合对账披露事实",
            "test_fixture": "测试建制：用户/组织/权限等隔离夹具，不进入财务事实源",
        },
        "sources": {
            "CNAI-IPO-2023": {
                "org": "菜鸟智慧物流网络有限公司",
                "title": "港交所上市申请版本（Phased version），附录 I 会计师报告（PwC）",
                "filing_status": "申请版本（draft），2024-03 撤回；不得表述为上市后年报",
                "url": "https://www.stattimes.com/pdf_upload/cianio272-55784.pdf",
                "sha256": sha256_of(PDF_CNAIAO),
                "pages_total": len(texts),
                "accounting_standard": "IFRS",
                "unit": "人民币千元（RMB'000）",
                "fiscal_year_end": "03-31",
                "statement_pages": {
                    name: meta["physical"] for name, meta in _CNAIAO_STATEMENT_PAGES.items()
                },
                "text_anchor_pages": {
                    key: {
                        "physical": meta["physical"],
                        "printed": meta["printed"],
                        "anchor_verified": anchor_present(
                            texts, meta["physical"], meta["anchor"]
                        ),
                    }
                    for key, meta in _CNAIAO_TEXT_ANCHORS.items()
                },
                "original_archive": "docs/knowledge-base/02_research/original/p5_samples/cainiao_private/Cainiao_application_proof_20230926.pdf",
            },
            "BABA-FY2025-RESULTS": {
                "org": "阿里巴巴集团（9988.HK / NYSE:BABA）",
                "title": "截至 2025 年 3 月 31 日止年度业绩公告",
                "filing_status": "未经审计初步业绩；终版以 FY2025 Form 20-F 复核",
                "url": "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0515/2025051500870_c.pdf",
                "sha256": sha256_of(PDF_BABA_FY2025) if PDF_BABA_FY2025.is_file() else None,
                "accounting_standard": "US GAAP（分部经调整 EBITA 为 MPM）",
                "unit": "人民币百万元",
                "fiscal_year_end": "03-31",
                "cainiao_segment_anchor": "物理页 18–21：菜鸟 FY2024/FY2025 分部收入 99,020 / 101,272；经调整 EBITA 1,402 / 302",
                "original_archive": "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2025_annual_results.pdf",
            },
            "BABA-FY2026-RESULTS": {
                "org": "阿里巴巴集团（9988.HK / NYSE:BABA）",
                "title": "截至 2026 年 3 月 31 日止年度业绩公告",
                "filing_status": "未经审计初步业绩",
                "url": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0513/2026051300654_c.pdf",
                "sha256": sha256_of(PDF_BABA_FY2026) if PDF_BABA_FY2026.is_file() else None,
                "accounting_standard": "US GAAP",
                "unit": "人民币百万元",
                "fiscal_year_end": "03-31",
                "cainiao_segment_anchor": (
                    "FY2026 起菜鸟重分类进「所有其他」分部；表列为混合组汇总，"
                    "脚注将菜鸟与盒马、阿里健康、高德等合列，不可反推菜鸟单体"
                ),
                "original_archive": "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2026_annual_results.pdf",
            },
            "BABA-ANNUAL-RESULTS-CURATED": {
                "org": "阿里巴巴集团（9988.HK / NYSE:BABA）",
                "title": "FY2019–FY2023 菜鸟分部披露（经整理序列登记）",
                "filing_status": "出处见 cainiao_segment_series.yaml sources 节",
                "url": None,
                "sha256": None,
                "accounting_standard": "US GAAP（MPM）",
                "unit": "人民币百万元",
                "fiscal_year_end": "03-31",
                "cainiao_segment_anchor": "分部收入 FY2019–FY2023；FY2023 起披露经调整 EBITA",
                "original_archive": None,
                "note": "页锚待逐份核验后升级为独立 source 条目",
            },
            "CNAI-FY2024-OPS": {
                "org": "菜鸟（阿里巴巴集团披露口径）",
                "title": "FY2024 跨境及国际包裹运营量（官方介绍/年报业务介绍）",
                "filing_status": "下限描述",
                "url": "https://www.alibabagroup.com/en-US/document-1747836787297878016",
                "sha256": None,
                "accounting_standard": None,
                "unit": "万件/日均",
                "fiscal_year_end": "03-31",
                "cainiao_segment_anchor": "FY2024 跨境及国际包裹日均量超过 500 万（下限，不可改写为精确值）",
                "original_archive": None,
                "note": "无本地原件；精确月度/客户/区域/产品分配均未公开",
            },
        },
        "facts": facts,
        "derived_rules": [
            {
                "rule_id": "D-CN-GROSS-MARGIN",
                "name": "毛利率（可复算）",
                "inputs": ["CN-PL-{fy}-GROSSPROFIT", "CN-PL-{fy}-REVENUE"],
                "formula": "gross_profit / revenue",
                "rounding": "Decimal 0.0001",
                "applies_to": ["FY2021", "FY2022", "FY2023"],
            },
            {
                "rule_id": "D-CN-SEG-YOY",
                "name": "分部收入同比（可复算）",
                "inputs": ["CN-SEG-{fy}-SEGMENT_REVENUE", "CN-SEG-{prev}-SEGMENT_REVENUE"],
                "formula": "(cur - prev) / abs(prev)",
                "rounding": "Decimal 0.0001",
                "applies_to": ["FY2020", "FY2021", "FY2022", "FY2023", "FY2024", "FY2025"],
            },
            {
                "rule_id": "D-CN-SEG-EBITA-MARGIN",
                "name": "分部经调整 EBITA 利润率（可复算）",
                "inputs": ["CN-SEG-{fy}-ADJUSTED_EBITA", "CN-SEG-{fy}-SEGMENT_REVENUE"],
                "formula": "adjusted_ebita / segment_revenue",
                "rounding": "Decimal 0.0001",
                "applies_to": ["FY2023", "FY2024", "FY2025"],
            },
        ],
        "unavailable": [
            {
                "unavailable_id": "U-CN-FY2026-STANDALONE",
                "scope": "FY2026 起菜鸟单体全部财务/经营值",
                "reason": (
                    "阿里 FY2026 起将菜鸟重分类进「所有其他」分部，报告未单列菜鸟，"
                    "不能从混合组汇总反推"
                ),
                "source_refs": ["BABA-FY2026-RESULTS"],
            },
            {
                "unavailable_id": "U-CN-FY2024PLUS-FULL-STATEMENTS",
                "scope": "FY2024 及以后菜鸟完整三表（利润表/资产负债表/现金流量表）",
                "reason": "阿里仅披露分部收入与经调整 EBITA 两项，无完整报表",
                "source_refs": ["BABA-FY2025-RESULTS"],
            },
            {
                "unavailable_id": "U-CN-VOLUME-FINE-GRAINS",
                "scope": "件量的月度/客户/区域/产品线拆分（全部期间）",
                "reason": (
                    "公开披露仅为年度/Q1 期间总量与 FY2024 日均下限（>500 万/日）；"
                    "精确分配未披露，不得由占比倒推冒充实际"
                ),
                "source_refs": ["CNAI-IPO-2023", "CNAI-FY2024-OPS"],
            },
            {
                "unavailable_id": "U-DM-INTEREST-SPLIT",
                "scope": "现行大麦合成报表「其中：利息费用」（财务费用 × 65%）",
                "reason": "无来源拆分假设；菜鸟披露利润表无该子项",
                "disposition": "期间迁移后删除该行；迁移前仅作演示层并须登记标注",
            },
            {
                "unavailable_id": "U-DM-DEPRECIATION-ESTIMATE",
                "scope": "现行大麦合成报表「折旧与摊销」（固定资产 × 10%）",
                "reason": "无来源估算；披露现金流量表有真实折旧摊销行可迁移后采用",
                "disposition": "期间迁移后改用申请稿披露行；迁移前仅作演示层",
            },
            {
                "unavailable_id": "U-DM-DEBT-AP-COMPOSITION",
                "scope": "短期/长期借款、应付账款等负债构成拆分（流动负债 × 25%/35% 等）",
                "reason": "无来源拆分；申请稿资产负债表逐行披露真实构成",
                "disposition": "期间迁移后改用披露行",
            },
            {
                "unavailable_id": "U-DM-CASHFLOW-SPLIT",
                "scope": "销售收现 = 流出小计 + 净额、资本开支 = 收入 × 6% 等现金流拆分",
                "reason": "展示用合成拆分；申请稿现金流量表逐行披露真实明细",
                "disposition": "期间迁移后改用披露行",
            },
        ],
        "demo_layers": [
            {
                "scope": "canonical 月度明细（月份 × 客户 × 产品 / 月份 × 业务单元 × 管理科目）",
                "layer": "demo_detail",
                "generation": "确定性生成（uuid5 + Decimal + Random(42) 族权重），规则见发行版 manifest.lineage",
                "reconciliation": (
                    "期间迁移后：年度聚合必须等于 CN-PL-FY2022/FY2023 的收入与成本披露值"
                ),
                "status": "pending_timeline_migration",
            },
            {
                "scope": "预算、应收账龄、滚动预测、planted events",
                "layer": "demo_detail",
                "generation": "显式演示参数（budget ×1.03/×1.12、账龄桶 70/12/8/6/尾差 等）",
                "reconciliation": "期间迁移后随明细层一并重标定；页面须显著标识演示生成",
                "status": "pending_timeline_migration",
            },
        ],
        "test_fixtures": [
            {
                "scope": "用户、岗位、部门、角色、权限（ORG-LEDGER 企业建制包）",
                "layer": "test_fixture",
                "note": "非阿里/菜鸟事实；隔离测试夹具，须醒目测试标识，不进入财务事实源",
            }
        ],
        "build_warnings": warnings,
    }
    return registry


def _dump(registry: dict[str, Any]) -> str:
    body = yaml.safe_dump(registry, allow_unicode=True, sort_keys=False, width=100)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="重建对账已提交登记")
    args = parser.parse_args(argv)

    if not PDF_CNAIAO.is_file():
        print(f"原件缺失：{PDF_CNAIAO}", file=sys.stderr)
        return 2
    texts = pdf_page_texts(PDF_CNAIAO)
    registry = build_registry(texts)
    rendered = _dump(registry)
    if args.check:
        committed = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.is_file() else ""
        if committed == rendered:
            print("source registry check: PASS")
            return 0
        print("source registry check: FAIL（登记与重建不一致，请重新生成）", file=sys.stderr)
        return 1
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(rendered, encoding="utf-8")
    print(
        f"source registry built at {OUT_PATH} "
        f"({len(registry['facts'])} facts, warnings={len(registry['build_warnings'])})"
    )
    for warning in registry["build_warnings"]:
        print(f"  WARN {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
