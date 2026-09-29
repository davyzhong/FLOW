"""应用公开财报版本化行身份修订；只改副本标签，绝不改原始档案。"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORRECTION_PATH = ROOT / "validation/financial_reports/corrections/public-row-identity-map-v1.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_corrections(path: Path) -> list[dict[str, str]]:
    expected_header = [
        "sample",
        "report",
        "source_pdf",
        "source_pdf_sha256",
        "statement",
        "source_item",
        "source_text_label",
        "source_values_json",
        "corrected_item",
        "source_page_physical",
        "candidate_cells",
        "candidate_groups",
        "disposition",
    ]
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != expected_header:
            raise ValueError(f"行身份修订表头不符：{path}")
        rows = list(reader)
    if len(rows) != 40:
        raise ValueError(f"行身份修订表应有40条来源行定义，实际{len(rows)}条")
    return rows


def apply_public_row_identity_corrections(
    payload: dict[str, Any],
    *,
    corrections_path: Path | None = None,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """校验来源与原值后，在副本上为逐格裁决的行名补上语义范围。"""
    if not isinstance(payload, dict):
        raise TypeError("财报payload必须是对象")
    sample = payload.get("sample")
    source_pdf = payload.get("source_pdf")
    statements = payload.get("statements")
    if not isinstance(sample, str) or not isinstance(source_pdf, str) or not isinstance(statements, dict):
        raise TypeError("财报payload缺少sample、source_pdf或statements身份字段")

    correction_rows = _load_corrections(corrections_path or CORRECTION_PATH)
    applicable = [row for row in correction_rows if row["sample"] == sample]
    if not applicable:
        return copy.deepcopy(payload)

    output = copy.deepcopy(payload)
    for correction in applicable:
        if correction["source_pdf"] != source_pdf:
            raise ValueError(f"行身份修订报告身份不匹配：{sample}/{source_pdf}")
        source_path = repository_root / source_pdf
        if not source_path.is_file() or _sha256(source_path) != correction["source_pdf_sha256"]:
            raise ValueError(f"行身份修订原件SHA校验失败：{source_pdf}")
        try:
            expected_values = json.loads(correction["source_values_json"])
        except json.JSONDecodeError as error:
            raise ValueError(f"行身份修订值列不是合法JSON：{sample}/{correction['source_item']}") from error
        rows = output["statements"].get(correction["statement"])
        if not isinstance(rows, list):
            raise TypeError(f"行身份修订报表不存在：{sample}/{correction['statement']}")
        matches = [
            row
            for row in rows
            if row.get("item") == correction["source_item"]
            and all(
                key in row and str(row[key]) == str(value)
                for key, value in expected_values.items()
            )
        ]
        if len(matches) != 1:
            raise ValueError(
                "未能唯一匹配来源行："
                f"{sample}/{correction['statement']}/{correction['source_item']}"
                f"（匹配数{len(matches)}）"
            )
        matched = matches[0]
        matched["item"] = correction["corrected_item"]
        matched["source_text_label"] = correction["source_text_label"]
        physical_page = correction["source_page_physical"]
        if physical_page.isdecimal():
            matched["page"] = int(physical_page)
    return output


__all__ = ["apply_public_row_identity_corrections"]
