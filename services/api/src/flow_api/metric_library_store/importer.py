"""指标库 v1 配置 → 数据库导入器（幂等，整版重导）。

按唯一身份 upsert：metric_dictionary_entry 以 (dictionary_id, collection,
metric_code, version)；subject/standard/template/mapping 以自然键。
重导不产生重复行；JSONB 字段整块替换。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricDictionaryEntry,
    StatementLineMapping,
)
from flow_api.metrics.mpm_semantics import assert_mpm_labels_valid

METRIC_FIELDS = {
    "unit", "time_behavior", "caliber", "default_caliber", "default_basis",
    "alternative_calibers", "source_cas", "source_ifrs", "depends_on",
    "decompositions", "aliases", "benchmark", "reconciliation", "migrates_from",
    "provenance", "mpm_review",
}


def _upsert(
    session: Session,
    model: type,
    natural_key: dict[str, Any],
    values: dict[str, Any],
) -> Any:
    row = session.scalar(
        select(model).where(*[getattr(model, k) == v for k, v in natural_key.items()])
    )
    if row is None:
        row = model(**natural_key, **values)
        session.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    return row


# 报表项目 CAS 名称 → 科目编码的显式映射（依据：财会〔2018〕15 号报表格式
# 与 2024 汇编科目体系；合计行项目无单一科目，subject_codes 为空）。
REPORT_ITEM_SUBJECTS: dict[str, list[str]] = {
    "bs.cash": ["1001", "1002"],
    "bs.notes_receivable": ["1121"],
    "bs.ar": ["1122"],
    "bs.inventory": ["1403", "1405"],
    "bs.current_assets": [],
    "bs.fixed_assets": ["1601"],
    "bs.total_assets": [],
    "bs.short_debt": ["2001"],
    "bs.ap": ["2202"],
    "bs.current_liab": [],
    "bs.long_debt": ["2501", "2502"],
    "bs.total_liab": [],
    "bs.equity": [],
    "is.revenue": ["6001", "6051"],
    "is.cogs": ["6401", "6402"],
    "is.selling_exp": ["6601"],
    "is.admin_exp": ["6602"],
    "is.fin_exp": ["6603"],
    # is.rnd_exp 研发费用：暂按「4301 研发支出」归集口径登记；待《应用指南
    # 汇编 2024》原文核对后修订（用户 2026-09-09 确认：常见口径 + 待核标注）。
    "is.rnd_exp": ["4301"],
    "is.interest_exp": [],
    "is.dep_amort": ["1602", "1702"],
}


def import_metric_dictionary(session: Session, config_path: Path) -> dict[str, int]:
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    # MPM 分类不变量（P01/C02）：mpm=true 必须携带已核验结构化判定，加载即拒绝
    assert_mpm_labels_valid(
        [
            SimpleNamespace(
                metric_code=entry["metric_code"],
                mpm=bool(entry.get("mpm", False)),
                mpm_review=entry.get("mpm_review"),
            )
            for collection in ("metrics_general", "metrics_logistics")
            for entry in data[collection]
        ]
    )
    counts = {"metrics": 0}
    status = data.get("status", "effective")
    for collection in ("metrics_general", "metrics_logistics"):
        for entry in data[collection]:
            natural = {
                "dictionary_id": data["dictionary_id"],
                "collection": collection.replace("metrics_", ""),
                "metric_code": entry["metric_code"],
                "version": int(entry.get("version", 1)),
            }
            values = {
                "status": status,
                "name": entry["name"],
                "domain": entry["domain"],
                "definition": entry["definition"],
                "formula_text": entry["formula_text"],
                "formula": entry["formula"],
                "mpm": bool(entry.get("mpm", False)),
            }
            for field in METRIC_FIELDS:
                if field in entry:
                    values[field] = entry[field]
            _upsert(session, MetricDictionaryEntry, natural, values)
            counts["metrics"] += 1
    for item_id, names in data.get("report_items", {}).items():
        _upsert(
            session,
            StatementLineMapping,
            {"item_id": item_id},
            {
                "cas_label": names["cas"],
                "ifrs_label": names.get("ifrs"),
                "subject_codes": REPORT_ITEM_SUBJECTS.get(item_id, []),
            },
        )
        counts["mappings"] = counts.get("mappings", 0) + 1
    session.flush()
    return counts


def import_accounting_foundation(
    session: Session, config_path: Path
) -> dict[str, int]:
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    counts = {"subjects": 0, "standards": 0, "templates": 0}
    for account in data["accounts"]:
        _upsert(
            session,
            AccountingSubject,
            {"code": account["code"]},
            {
                "name": account["name"],
                "category": account["category"],
                "balance_side": account["balance_side"],
                "status": account["status"],
                "standard_ref": account.get("standard_ref"),
                "code_note": account.get("code_note"),
                "source_note": account.get("source_note"),
            },
        )
        counts["subjects"] += 1
    for standard in data.get("standards", []):
        _upsert(
            session,
            AccountingStandard,
            {"standard_id": standard["id"]},
            {
                "name": standard["name"],
                "issuer": standard.get("issuer"),
                "note": standard.get("note"),
            },
        )
        counts["standards"] += 1
    for template in data.get("entry_templates", []):
        _upsert(
            session,
            EntryTemplate,
            {"template_id": template["template_id"]},
            {
                "scenario": template["scenario"],
                "business_context": template.get("business_context"),
                "lines": template["lines"],
                "standard_ref": template.get("standard_ref"),
                "related_metrics": template.get("related_metrics", []),
                "note": template.get("note"),
            },
        )
        counts["templates"] += 1
    session.flush()
    return counts


def resolve_dictionary_file(config_root: Path) -> Path:
    """字典配置解析：优先 v1.1（内部指标库扩充版），不存在时回退 v1。"""
    candidate = config_root / "metric_dictionary_v1_1.yaml"
    return candidate if candidate.is_file() else config_root / "metric_dictionary_v1.yaml"


def import_all(session: Session, config_root: Path) -> dict[str, int]:
    summary: dict[str, int] = {}
    summary.update(
        import_metric_dictionary(session, resolve_dictionary_file(config_root))
    )
    summary.update(
        import_accounting_foundation(
            session, config_root / "accounting_foundation_v1.yaml"
        )
    )
    return summary


__all__ = ["import_accounting_foundation", "import_all", "import_metric_dictionary"]
