#!/usr/bin/env python3
"""T09-L1：从源 PDF 定位抽取值的页码，生成页级答案集（answer_set_l1.yaml）。

对每条「抽取 YAML 中非空值」在源 PDF 文本层定位页码（行名 + 全部数值同页
同时出现，千分位/括号负数归一后匹配）；输出带页锚的答案集 + 覆盖率报告。
未定位条目显式列出（unlocated），不得静默丢弃——C 级出口要求覆盖率达标。

用法：python3 scripts/build_answer_set_l1.py [--out PATH] [--json]
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES_GLOB = "docs/implementation/p5/*_statements.yaml"
OUT_DEFAULT = REPO / "config/statements/answer_set_l1.yaml"


def _norm(text: str) -> str:
    """数值归一：去千分位/空白；括号负数 → -N。"""
    cleaned = text.replace(",", "").replace("，", "").replace(" ", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return cleaned


_PAREN_NEG = re.compile(r"\((\d+)\)")


def _page_haystack(text: str) -> str:
    """整页归一：NUL 空白去、千分位去、括号负数 → -N（行内 `(282,367)` = -282367）。"""
    cleaned = (
        text.replace("\u00a0", "")
        .replace(",", "")
        .replace("，", "")
        .replace(" ", "")
        .replace("\n", "")
    )
    return _PAREN_NEG.sub(r"-\1", cleaned)


def extract_pages(pdf_path: Path) -> list[str]:
    """每页归一化文本，只解析一次（年报数百页，逐行重解析不可接受）。"""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return [_page_haystack(page.extract_text() or "") for page in reader.pages]


def locate(pages: list[str], item: str, values: list[int]) -> tuple[int, str] | None:
    """定位页码 + 匹配模式。

    strong：行名（含变体）与全部数值同页；weak：仅全部数值同页（跨语言
    报表兜底，如菜鸟英文招股书——数值对出现已是较强信号，仍显式降级标注）。
    strong-sign-flip-loss-row：亏损类行在部分披露中以正数印出亏损额
    （如「歸屬於非控制性權益的淨損失 9,083」），抽取层按会计符号记为负数；
    仅当行名变体与全部数值绝对值同页时才允许翻转，且只产生强锚——
    弱锚（无行名）一律不得翻转，避免无关数字子串误锚。
    """
    value_norms = [_norm(str(v)) for v in values]
    item_candidates = {_norm(item)}
    stripped = re.sub(r"^(其中|其中:|其中：)\s*", "", item)
    item_candidates.add(_norm(stripped))
    item_candidates.add(_norm(item.replace("：", ":")))
    # 行名后缀变体（如「歸屬於非控制性權益損益」vs PDF「…的淨損失」）：
    # 长归一名取多档前缀候选（8/12 字）——仍要求全部数值同页
    base = _norm(stripped)
    for cut in (8, 12):
        if len(base) > cut:
            item_candidates.add(base[:cut])
    # 两遍扫描：strong（行名+数值）优先于 weak（仅数值）——摘要/比较期段常
    # 提前出现同值行，弱锚不得抢占强锚。
    weak_page: int | None = None
    for index, text in enumerate(pages):
        if not text:
            continue
        if not all(v in text for v in value_norms):
            continue
        if any(c and c in text for c in item_candidates):
            return index + 1, "strong"
        if weak_page is None:
            weak_page = index + 1
    if weak_page is not None:
        return weak_page, "weak"
    # 第三遍：亏损行正数披露的符号翻转（仅强锚，仅当存在负数抽取值）
    if any(v < 0 for v in values):
        abs_norms = [_norm(str(abs(v))) for v in values]
        for index, text in enumerate(pages):
            if not text:
                continue
            if not all(v in text for v in abs_norms):
                continue
            if any(c and c in text for c in item_candidates):
                return index + 1, "strong-sign-flip-loss-row"
    return None


def load_visual_overrides(repo: Path) -> dict[tuple[str, str, str], dict]:
    """加载图像页目视核验登记（无文本层 PDF 的显式锚点证据）。

    文件：config/statements/l1_visual_verified.yaml；键为
    (source_pdf, statement, item)。每条必须携带完整证据字段，
    缺字段即抛错（fail-closed），不允许静默生成无证据锚点。
    文件不存在时返回空表（多数仓库状态无需覆盖）。
    """
    import hashlib

    import yaml

    path = repo / "config/statements/l1_visual_verified.yaml"
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    overrides: dict[tuple[str, str, str], dict] = {}
    required = (
        "statement",
        "item",
        "page_seq",
        "printed_page",
        "evidence_image",
        "evidence_sha256",
        "verified_by",
        "verified_at",
        "basis",
    )
    for row in raw.get("overrides", []):
        missing = [f for f in required if f not in row]
        if missing:
            raise ValueError(f"visual override 缺字段 {missing}: {row!r}")
        evidence_path = repo / row["evidence_image"]
        if not evidence_path.is_file():
            raise ValueError(f"visual override 证据图缺失: {row['evidence_image']}")
        digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        if digest != row["evidence_sha256"]:
            raise ValueError(f"visual override 证据图 SHA 不一致: {row['evidence_image']}")
        key = (row["source_pdf"], row["statement"], row["item"])
        overrides[key] = row
    return overrides


def build(out: Path, repo: Path = REPO) -> dict:
    import yaml

    entries: list[dict] = []
    unlocated: list[dict] = []
    total_values = 0
    located_values = 0

    mapping_rows = yaml.safe_load(
        (repo / "config/statements/answer_set_sources.yaml").read_text(encoding="utf-8")
    )["reports"]
    sample_to_ref = {m["sample"]: m for m in mapping_rows}
    visual_overrides = load_visual_overrides(repo)

    for source in sorted(glob.glob(str(repo / SOURCES_GLOB))):
        payload = yaml.safe_load(Path(source).read_text(encoding="utf-8"))
        source_pdf = payload["source_pdf"]
        sample = payload["sample"]
        ref = sample_to_ref.get(sample)
        if ref is None:
            unlocated.append(
                {"source_pdf": source_pdf, "error": f"answer_set_sources.yaml 缺 sample {sample}"}
            )
            continue
        pdf_path = repo / source_pdf
        if not pdf_path.is_file():
            unlocated.append({"source_pdf": source_pdf, "error": "PDF 缺失"})
            continue
        pages = extract_pages(pdf_path)
        for statement, rows in payload["statements"].items():
            for row in rows:
                item = row["item"]
                present = {
                    column: value
                    for column, value in row.items()
                    if column != "item" and value is not None
                }
                if not present:
                    continue
                total_values += len(present)
                located = locate(pages, item, list(present.values()))
                override = None
                if located is None:
                    override = visual_overrides.get((source_pdf, statement, item))
                if located is None and override is None:
                    unlocated.append(
                        {
                            "source_pdf": source_pdf,
                            "statement": statement,
                            "item": item,
                            "columns": sorted(present),
                        }
                    )
                    continue
                if located is not None:
                    page, match_mode = located
                    evidence = {}
                else:
                    # 图像页目视核验锚点：页码与证据全部来自登记文件，
                    # 构建器已逐条验证证据图存在且 SHA 一致（fail-closed）。
                    page, match_mode = override["page_seq"], "visual-verified"
                    evidence = {
                        "printed_page": override["printed_page"],
                        "evidence_image": override["evidence_image"],
                        "evidence_sha256": override["evidence_sha256"],
                        "verified_by": override["verified_by"],
                        "verified_at": override["verified_at"],
                        "basis": override["basis"],
                    }
                located_values += len(present)
                for column, value in present.items():
                    entries.append(
                        {
                            "source_pdf": source_pdf,
                            "stock_code": ref["stock_code"],
                            "period_label": ref["period_label"],
                            "report_kind": ref["report_kind"],
                            "page": page,
                            "match_mode": match_mode,
                            **evidence,
                            "statement": statement,
                            "item": item,
                            "column": column,
                            "value": value if isinstance(value, int) else float(value),
                        }
                    )

    payload = {
        "schema": "flow.answer_set.l1",
        "generated_from": "docs/implementation/p5 抽取 YAML（P5 期已人工核验）",
        "location_method": (
            "pypdf 文本层；match_mode=strong（行名+数值同页）"
            "/weak（仅数值同页，跨语言兜底）"
            "/strong-sign-flip-loss-row（亏损行正数披露，行名+绝对值同页强锚）"
            "/visual-verified（图像页无文本层，证据登记见 "
            "config/statements/l1_visual_verified.yaml）"
        ),
        "coverage": {
            "values_total": total_values,
            "values_located": located_values,
            "ratio": round(located_values / total_values, 4) if total_values else 0.0,
            "unlocated_rows": len(unlocated),
        },
        "entries": entries,
        "unlocated": unlocated,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# T09-L1 页级答案集（生成物；重生成见 scripts/build_answer_set_l1.py）\n"
        + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build(args.out)
    if args.json:
        print(json.dumps(payload["coverage"], ensure_ascii=False, indent=2))
    else:
        coverage = payload["coverage"]
        print(
            f"L1 答案集：{coverage['values_located']}/{coverage['values_total']}"
            f" 值带页锚（覆盖率 {coverage['ratio']:.1%}），"
            f"未定位行 {coverage['unlocated_rows']} → {args.out}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
