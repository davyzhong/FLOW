#!/usr/bin/env python3
"""T09 数字级准确率基准（C 级出口 B2）：L0 入库保真 + L1 页级锚验证。

两级基准合同（docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md）：
- L0：事实库 statement_line_item ↔ 已验证抽取 YAML 逐值比对——管线不丢数、
  不改数、不换符号；
- L1（`--level L1`）：页级答案集（config/statements/answer_set_l1.yaml，
  由 scripts/build_answer_set_l1.py 从源 PDF 文本层定位生成）双向验证：
  ① 每条页锚在当前 PDF 上仍可复现（数值确实出现在该页）；
  ② 答案集值 == 事实库值（值级一致）。
  match_mode=weak（仅数值同页，跨语言兜底）单独计数，不与 strong 混淆。

用法：
  python3 scripts/accuracy_benchmark.py --level L0        # 入库保真
  python3 scripts/accuracy_benchmark.py --level L1        # 页级锚验证
退出码：0 = 通过；1 = 存在差异；2 = 配置/环境错误。
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "services/api" / "src"))

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_ENV_ERROR = 2


def load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


# 与 statements/importer.py COLUMN_ALIASES 同源的列名规范化（基准侧独立复制，
# 避免被测管线自带答案；两表漂移时本脚本 Step 层会暴露差异）
COLUMN_ALIASES = {
    "期末余额": "value_end",
    "期初余额": "value_begin",
    "本期发生额": "value_current",
    "上期发生额": "value_prior",
    "本期金额": "value_current",
    "上期金额": "value_prior",
}


def collect_expected() -> dict:
    """期望值：(source_pdf, statement, item, column) -> Decimal|null。

    以 source_pdf（抽取 YAML 顶部字段）为报告身份——事实库 source_ref 登记
    同一路径（seed 时传入），不受 sample 代号与 stock_code/period_label 命名
    差异影响。
    """
    expected: dict[tuple[str, str, str, str], Decimal | None] = {}
    sources = sorted(glob.glob(str(REPO / "docs/implementation/p5" / "*_statements.yaml")))
    if not sources:
        raise RuntimeError("未找到抽取 YAML（docs/implementation/p5/*_statements.yaml）")
    for source in sources:
        payload = load_yaml(Path(source))
        source_pdf = payload["source_pdf"]
        for statement, rows in payload["statements"].items():
            for row in rows:
                item = row["item"]
                for column, value in row.items():
                    if column == "item":
                        continue
                    normalized = COLUMN_ALIASES.get(column, column)
                    key = (source_pdf, statement, item, normalized)
                    if value is None:
                        expected.setdefault(key, None)
                    else:
                        expected[key] = Decimal(str(value))
    return expected


def collect_actual() -> dict:
    """实际值：事实库 statement_line_item 按 (sample, statement, item, column)。"""
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport

    actual: dict[tuple[str, str, str, str], Decimal | None] = {}
    with get_engine().connect() as conn:
        reports = conn.execute(select(StatementReport.id, StatementReport.source_ref)).all()
        id_source = {r[0]: r[1] for r in reports}
        rows = conn.execute(
            select(
                StatementLineItem.report_id,
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
            ).order_by(StatementLineItem.report_id, StatementLineItem.sort_order)
        ).all()
    column_keys = ("value_end", "value_begin", "value_current", "value_prior")
    for report_id, statement_type, item_name, *values in rows:
        source_ref = id_source.get(report_id)
        if source_ref is None:
            continue
        for column, value in zip(column_keys, values, strict=True):
            key = (source_ref, statement_type, item_name, column)
            if value is None:
                actual.setdefault(key, None)
            else:
                actual[key] = Decimal(str(value))
    return actual


def _display_column(report_kind: str, column: str, sort_order: int) -> str:
    # 直接以 DB 数值列族对齐（value_end/value_begin/value_current/value_prior）；
    # report_kind 不改变列族。
    return column


def compare(expected: dict, actual: dict) -> dict:
    mismatches = []
    only_expected = []
    only_actual = []
    value_checked = 0
    for key, want in expected.items():
        got = actual.get(key)
        if got is None and key not in actual:
            # 期望有、实际完全缺失
            only_expected.append(
                {"key": list(key), "expected": str(want) if want is not None else None}
            )
            continue
        if got != want:
            mismatches.append(
                {
                    "key": list(key),
                    "expected": str(want) if want is not None else None,
                    "actual": str(got) if got is not None else None,
                }
            )
            continue
        value_checked += 1
    for key, value in actual.items():
        if key not in expected and value is not None:
            # 实际侧存在、期望侧无列且值非空 = 真实多出数据；
            # DB 四列族的结构性 NULL 不算多出。
            only_actual.append({"key": list(key), "actual": str(value)})
    total = value_checked + len(mismatches) + len(only_expected)
    return {
        "level": "L0",
        "total_compared": total,
        "value_checked": value_checked,
        "mismatch_count": len(mismatches),
        "missing_count": len(only_expected),
        "extra_count": len(only_actual),
        "mismatches": mismatches[:50],
        "missing": only_expected[:50],
        "extra": only_actual[:50],
    }


_PAREN_NEG = re.compile(r"\((\d+)\)")


def _norm_for_pdf(text: str) -> str:
    """与 build_answer_set_l1.py 的页归一逐字节一致（含括号负数与换行处理）。"""
    cleaned = (
        text.replace("\u00a0", "")
        .replace(",", "")
        .replace("，", "")
        .replace(" ", "")
        .replace("\n", "")
    )
    return _PAREN_NEG.sub(r"-\1", cleaned)


def verify_l1(answer_set_path: Path) -> dict:
    """L1 双向验证：页锚可复现 + 值与事实库一致。"""
    import yaml as pyyaml
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    payload = pyyaml.safe_load(answer_set_path.read_text(encoding="utf-8"))
    entries = payload["entries"]

    # 事实库值索引（值集合）：同名行（如流动/非流动借款）聚合为集合，
    # L1 键级断言 = 答案值 ∈ 该键的值集合。
    db_values: dict[tuple[str, str, str, str, str, str], set[str]] = {}
    with get_engine().connect() as conn:
        reports = conn.execute(
            select(
                StatementReport.id,
                StatementReport.stock_code,
                StatementReport.period_label,
                StatementReport.report_kind,
            )
        ).all()
        id_identity = {r[0]: (r[1], r[2], r[3]) for r in reports}
        rows = conn.execute(
            select(
                StatementLineItem.report_id,
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
            )
        ).all()
    columns = ("value_end", "value_begin", "value_current", "value_prior")
    for report_id, statement_type, item_name, *values in rows:
        identity = id_identity.get(report_id)
        if identity is None:
            continue
        for column, value in zip(columns, values, strict=True):
            if value is None:
                continue
            db_values.setdefault((*identity, statement_type, item_name, column), set()).add(
                str(value)
            )

    # PDF 页文本缓存（每 PDF 解析一次）
    from pypdf import PdfReader

    page_cache: dict[str, list[str]] = {}

    def pages_of(source_pdf: str) -> list[str]:
        if source_pdf not in page_cache:
            reader = PdfReader(str(Path(answer_set_path).parents[1].parent / source_pdf))
            page_cache[source_pdf] = [_norm_for_pdf(p.extract_text() or "") for p in reader.pages]
        return page_cache[source_pdf]

    anchor_fail: list[dict] = []
    value_mismatch: list[dict] = []
    missing_in_db: list[dict] = []
    strong = 0
    weak = 0
    sign_flip = 0
    visual_verified = 0
    for entry in entries:
        match_mode = entry.get("match_mode")
        if match_mode == "visual-verified":
            # 图像页无文本层：不做文本锚复验，但复核证据图 SHA（纵深防御，
            # 构建期已 fail-closed 验过一次）；证据缺失/不一致计入锚失效。
            import hashlib

            evidence_path = (
                Path(answer_set_path).parents[1].parent / entry.get("evidence_image", "")
            )
            digest = (
                hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                if evidence_path.is_file()
                else None
            )
            if digest != entry.get("evidence_sha256"):
                anchor_fail.append(
                    {
                        "source_pdf": entry["source_pdf"],
                        "page": entry["page"],
                        "item": entry["item"],
                        "value": entry["value"],
                        "reason": "visual-verified 证据图缺失或 SHA 不一致",
                    }
                )
            visual_verified += 1
        else:
            # 锚复验按绝对值进行：亏损行允许正数披露（sign-flip 强锚），
            # 其余模式符号已被构建期括号负数归一覆盖。
            value_norm = _norm_for_pdf(str(abs(entry["value"])))
            pages = pages_of(entry["source_pdf"])
            page_index = entry["page"] - 1
            page_text = pages[page_index] if 0 <= page_index < len(pages) else ""
            if value_norm not in page_text:
                anchor_fail.append(
                    {
                        "source_pdf": entry["source_pdf"],
                        "page": entry["page"],
                        "item": entry["item"],
                        "value": entry["value"],
                    }
                )
        if match_mode == "weak":
            weak += 1
        elif match_mode == "strong-sign-flip-loss-row":
            sign_flip += 1
        elif match_mode != "visual-verified":
            strong += 1
        normalized_column = COLUMN_ALIASES.get(entry["column"], entry["column"])
        key = (
            entry["stock_code"],
            entry["period_label"],
            entry["report_kind"],
            entry["statement"],
            entry["item"],
            normalized_column,
        )
        db_candidates = db_values.get(key)
        if db_candidates is None:
            missing_in_db.append({"key": list(key)[:4], "item": entry["item"]})
        elif Decimal(str(entry["value"])) not in {Decimal(v) for v in db_candidates}:
            value_mismatch.append(
                {
                    "key": list(key)[:4],
                    "item": entry["item"],
                    "answer_set": entry["value"],
                    "db": sorted(db_candidates),
                }
            )

    total = len(entries)
    return {
        "level": "L1",
        "entries": total,
        "strong": strong,
        "weak": weak,
        "sign_flip": sign_flip,
        "visual_verified": visual_verified,
        "anchor_fail_count": len(anchor_fail),
        "value_mismatch_count": len(value_mismatch),
        "missing_in_db_count": len(missing_in_db),
        "coverage_from_generator": payload["coverage"],
        "anchor_fail": anchor_fail[:30],
        "value_mismatch": value_mismatch[:30],
    }


def export_review_bundle(out_dir: Path) -> None:
    """逐报告导出「抽取值 + 源页文本」供交叉评审 AI 独立找错。

    故意不包含答案集判定与 L0/L1 结果——评审必须自己找错，
    不能对着实现方的结论打分。
    """
    from pypdf import PdfReader

    out_dir.mkdir(parents=True, exist_ok=True)
    expected = collect_expected()
    by_source: dict[str, dict[tuple[str, str, str], str]] = {}
    for (source_pdf, statement, item, column), value in expected.items():
        values = by_source.setdefault(source_pdf, {})
        values[(statement, item, column)] = str(value) if value is not None else "（空）"

    for source_pdf, values in sorted(by_source.items()):
        pdf_path = REPO / source_pdf
        safe_name = source_pdf.rsplit("/", 1)[-1].replace(".pdf", "")
        page_texts = []
        if pdf_path.is_file():
            reader = PdfReader(str(pdf_path))
            for index, page in enumerate(reader.pages, start=1):
                raw = (page.extract_text() or "").replace("\u00a0", " ")
                page_texts.append(f"### 第 {index} 页\n\n```\n{raw}\n```")
        rows = "\n".join(
            f"| {statement} | {item} | {column} | {value} |"
            for (statement, item, column), value in sorted(values.items())
        )
        doc = (
            f"# 交叉评证据束：{safe_name}\n\n"
            f"## 1. 抽取值清单（实现方声称从本 PDF 抽出）\n\n"
            f"| 报表 | 行项目 | 列 | 值 |\n|---|---|---|---|\n{rows}\n\n"
            f"## 2. 源 PDF 全文（逐页文本层）\n\n" + "\n\n".join(page_texts) + "\n"
        )
        (out_dir / f"{safe_name}.md").write_text(doc, encoding="utf-8")
    print(f"证据束 → {out_dir}（{len(by_source)} 份报告）")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=("L0", "L1"), default="L0")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--export-review-bundle",
        type=Path,
        default=None,
        metavar="DIR",
        help="导出 AI 交叉评证据束（逐报告：抽取值 + 源 PDF 页文本；不含实现方判定）",
    )
    args = parser.parse_args()
    if args.export_review_bundle:
        export_review_bundle(args.export_review_bundle)
        return EXIT_OK
    if args.level == "L1":
        try:
            report = verify_l1(REPO / "config/statements/answer_set_l1.yaml")
        except Exception as error:  # noqa: BLE001
            print(f"env error: {error}", file=sys.stderr)
            return EXIT_ENV_ERROR
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(
                f"L1 页级锚验证：{report['entries']} 条（strong {report['strong']} / "
                f"weak {report['weak']} / sign-flip {report['sign_flip']} / "
                f"visual {report['visual_verified']}），锚失效 {report['anchor_fail_count']}，"
                f"值不一致 {report['value_mismatch_count']}，未入库 {report['missing_in_db_count']}"
            )
        clean = (
            report["anchor_fail_count"] == 0
            and report["value_mismatch_count"] == 0
            and report["missing_in_db_count"] == 0
        )
        return EXIT_OK if clean else EXIT_MISMATCH
    try:
        expected = collect_expected()
        actual = collect_actual()
    except Exception as error:  # noqa: BLE001
        print(f"env error: {error}", file=sys.stderr)
        return EXIT_ENV_ERROR
    report = compare(expected, actual)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"L0 入库保真基准：比对 {report['total_compared']} 值，"
            f"一致 {report['value_checked']}，"
            f"不一致 {report['mismatch_count']}，"
            f"缺失 {report['missing_count']}，"
            f"多出 {report['extra_count']}"
        )
    clean = report["mismatch_count"] == 0 and report["missing_count"] == 0
    return EXIT_OK if clean else EXIT_MISMATCH


if __name__ == "__main__":
    raise SystemExit(main())
