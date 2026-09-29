#!/usr/bin/env python3
"""U4 留出泛化验收 harness。

规程（oracle-register §4 / unified-next-plan U4）：
- 默认仅回归已降级的旧三样本；新留出须经 --samples 显式选择，防止意外提前首跑；
- 原始抽取输出全量留存于 validation/financial_reports/holdout_runs/<date>/；
- 与 oracle/<sample>.yaml 逐行 diff，三级分类：matched / mismatched / not_comparable；
- 首跑原始失败全部保留，不得为通过而调参；结果登记
  docs/implementation/objective-analysis/holdout-results.md。

用法（仓库根目录）：
    services/api/.venv/bin/python scripts/holdout_u4_run.py
    FLOW_HOLDOUT_RUN_ID=<unique-id> services/api/.venv/bin/python scripts/holdout_u4_run.py \
      --samples xiaomi_2026h1 alibaba_fy2027q1
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "services/api/src"))

from flow_api.statements.extraction import extract_statements  # noqa: E402


def holdout_output_dir(repo: Path) -> Path:
    run_id = os.environ.get("FLOW_HOLDOUT_RUN_ID") or datetime.date.today().isoformat()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id):
        raise ValueError("FLOW_HOLDOUT_RUN_ID 仅允许字母、数字、点、下划线和连字符")
    return repo / "validation/financial_reports/holdout_runs" / run_id


SAMPLES = {
    "sf_2026h1": (
        "docs/knowledge-base/02_research/original/p5_samples/sf_002352/SF_2026_H1_report.pdf"
    ),
    "tencent_fy2025": (
        "docs/knowledge-base/02_research/original/p5_samples/"
        "tencent_0700/Tencent_FY2025_annual_report.pdf"
    ),
    "zto_2026q1": (
        "validation/financial_reports/original/zto_2026q1/ZTO_2026_Q1_results_announcement_c.pdf"
    ),
    "xiaomi_2026h1": (
        "validation/financial_reports/original/xiaomi_2026h1/XIAOMI_2026_interim_report_e.pdf"
    ),
    "alibaba_fy2027q1": (
        "validation/financial_reports/original/alibaba_fy2027q1/BABA_FY2027Q1_results_c.pdf"
    ),
    # 2026-09-29 备选候选启用（holdout-lottery-2026-09-25 §3 顺位；oracle 已录，见 manifest）
    "yunda_2026h1": (
        "validation/financial_reports/original/yunda_2026h1/YUNDA_2026_interim_report_c.pdf"
    ),
    "jdl_2026h1": (
        "validation/financial_reports/original/jdl_2026h1/JDL_2026_interim_report_e.pdf"
    ),
}
LEGACY_REGRESSION_SAMPLES = ("sf_2026h1", "tencent_fy2025", "zto_2026q1")


def selected_samples(sample_ids: list[str] | None) -> dict[str, str]:
    selected = LEGACY_REGRESSION_SAMPLES if sample_ids is None else tuple(sample_ids)
    unknown = set(selected) - set(SAMPLES)
    if unknown:
        raise ValueError(f"未知留出样本：{sorted(unknown)}")
    return {sample_id: SAMPLES[sample_id] for sample_id in selected}


_DASH = "－—−‒–"
_ITEM_LABEL_EQUIVALENTS = {
    "收入": ("收入合計",),
    "收入合计": ("收入合計",),
    "收入：增值服务": ("增值服務",),
    "年度盈利（净利润）": ("年度盈利",),
    "经营活动所得现金流量净额": ("經營活動所得現金流量淨額",),
    "Non-IFRS 本公司权益持有人应占盈利": ("非國際財務報告準則本公司權益持有人應佔盈利",),
    "本公司權益持有人應佔": ("本公司權益持有人",),
    "经营活动所得现金": ("經營活動所得現金",),
    "年末的现金及现金等价物": ("年末的現金及現金等價物",),
    "Adjusted（Non-GAAP）净利润": ("調整後淨利潤",),
    "营业成本": ("營業成本",),
    "销售、一般及行政费用": ("銷售、一般及行政費用",),
    "其他经营利润净额": ("其他經營利潤淨額",),
    "总经营费用": ("總經營費用",),
    "经营利润": ("經營利潤",),
    "利息费用": ("利息費用",),
    "金融工具的公允价值变动收益": ("金融工具的公允價值變動收益",),
    "出售股权投资、子公司和其他的收益": ("出售股權投資、子公司和其他的收益",),
    "外币汇兑亏损，税前": ("外幣匯兌虧損，稅前",),
    "扣除所得税及权益法核算的投资收入前的利润": ("扣除所得稅及權益法核算的投資收入前的利潤",),
    "所得税费用": ("所得稅費用",),
    "权益法核算的投资收入": ("權益法核算的投資收入",),
    "净利润": ("淨利潤",),
    "归属于非控制性权益的净利润": ("歸屬於非控制性權益的淨利潤",),
    "归属于中通快递（开曼）有限公司的净利润": ("歸屬於中通快遞（開曼）有限公司的淨利潤",),
    "经营活动产生的现金净额": ("經營活動產生的現金淨額",),
    "经营活动产生的现金流量净额": ("經營活動產生的現金淨額",),
    "投资活动所用的现金净额": ("投資活動所用的現金淨額",),
    "融资活动（所用）／产生的现金净额": ("融資活動（所用）／產生的現金淨額",),
    "汇率变动影响": ("匯率變動對現金、現金等價物及受限制現金的影響",),
    "股权激励费用": ("股權激勵費用",),
    "调整后净利润": ("調整後淨利潤",),
    "息税折摊前收益": ("息稅折攤前收益",),
    "调整后息税折摊前收益": ("調整後息稅折攤前收益",),
}


def norm_name(name: str) -> str:
    s = re.sub(r"\s+", "", name or "")
    s = s.replace("（", "(").replace("）", ")").replace("╱", "/")
    for d in _DASH:
        s = s.replace(d, "-")
    return s


def norm_value(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace(" ", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    s = s.replace("−", "-")
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


def load_rows(extracted: dict) -> list[dict]:
    rows = []
    for stmt, items in (extracted.get("statements") or {}).items():
        for it in items:
            rows.append({"statement": stmt, **it})
    return rows


def find_row(rows: list[dict], item_name: str) -> dict | None:
    """行名匹配：归一化精确 → 互相包含。确定性匹配，不看抽取值。"""
    target = norm_name(item_name)
    aliases = [
        target,
        *re.findall(r"\(([^()]*)\)", target),
        *(norm_name(alias) for alias in _ITEM_LABEL_EQUIVALENTS.get(item_name, ())),
    ]
    aliases = list(
        dict.fromkeys(
            alias
            for value in aliases
            for alias in (value, re.sub(r"/\([^)]*\)", "", value))
            if alias
        )
    )
    normalized_rows = [
        (
            r,
            list(
                dict.fromkeys(
                    (
                        row_name := norm_name(str(r.get("item") or r.get("name") or "")),
                        re.sub(r"/\([^)]*\)", "", row_name),
                    )
                )
            ),
        )
        for r in rows
    ]

    def identical_value(candidates: list[dict]) -> bool:
        values = [
            next(
                (
                    row[key]
                    for key in ("本期发生额", "期末余额", "value_current", "value")
                    if row.get(key) is not None
                ),
                None,
            )
            for row in candidates
        ]
        normalized = [norm_value(value) for value in values]
        return (
            bool(normalized)
            and normalized[0] is not None
            and all(value == normalized[0] for value in normalized)
        )

    for alias in aliases:
        exact = [r for r, row_names in normalized_rows if alias in row_names]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1 and identical_value(exact):
            return exact[0]
    cands = []
    for r, row_names in normalized_rows:
        if any(rn and any(alias in rn or rn in alias for alias in aliases) for rn in row_names):
            cands.append(r)
    if len(cands) == 1:
        return cands[0]
    # 多个候选时不猜：视为未命中（not_comparable），首跑留痕从严
    return None


def canonical_statement(statement: str) -> str:
    name = norm_name(statement)
    if (
        "non-gaap" in name.lower()
        or "非公認會計準則" in name
        or "调节表" in name
        or "調節表" in name
    ):
        return "non_gaap"
    if "綜合全面收益" in name or "合併綜合收益" in name or "合并综合收益" in name:
        return "comprehensive_income"
    if "綜合收益" in name or "综合收益" in name:
        return "income_statement"
    if any(token in name for token in ("现金流量", "現金流量", "现金流", "現金流")):
        return "cash_flow"
    if any(token in name for token in ("资产负债表", "財務狀況表", "财务状况表")):
        return "balance_sheet"
    if any(token in name for token in ("利润表", "損益表", "收益表")):
        return "income_statement"
    return name


def find_row_in_statement(
    rows: list[dict], item_name: str, statement: str | None = None
) -> dict | None:
    if statement is None:
        return find_row(rows, item_name)
    expected = canonical_statement(statement)
    scoped = [
        row for row in rows if canonical_statement(str(row.get("statement") or "")) == expected
    ]
    return find_row(scoped, item_name)


def extracted_current_value(row: dict) -> object:
    """统一抽取结果与 holdout oracle 的本期列；资产负债表取期末，其余取本期。"""
    if row.get("statement") == "合并资产负债表":
        return row.get("期末余额", row.get("value_current", row.get("value")))
    return row.get("本期发生额", row.get("value_current", row.get("value")))


def diff_sample(sample_id: str, extracted: dict, oracle: dict) -> dict:
    rows = load_rows(extracted)
    results = []
    entries = []
    for k in oracle.get("key_items") or []:
        entries.append(
            {
                "tier": "key_item",
                "item": k["item"],
                "value": k["value"],
                "page": k.get("source_page"),
                "statement": k.get("statement") or k.get("location"),
            }
        )
    for s in oracle.get("supplementary_lines") or []:
        entries.append(
            {
                "tier": "supplementary",
                "item": s["item"],
                "value": s["value"],
                "page": s.get("page"),
                "statement": s.get("statement"),
            }
        )
    counts = {"matched": 0, "mismatched": 0, "not_comparable": 0}
    for e in entries:
        row = find_row_in_statement(rows, e["item"], e.get("statement"))
        if row is None:
            cls = "not_comparable"
            detail = "抽取输出中无对应行"
            got = None
        else:
            got = extracted_current_value(row)
            ov, gv = norm_value(e["value"]), norm_value(got)
            if ov is not None and gv is not None and abs(ov - gv) < 1e-6:
                cls = "matched"
                detail = ""
            else:
                cls = "mismatched"
                detail = f"oracle={e['value']} extracted={got}"
        counts[cls] += 1
        results.append({**e, "class": cls, "extracted_value": got, "detail": detail})
    total = len(entries)
    return {"counts": counts, "total": total, "rows_extracted": len(rows), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="运行旧样本回归或显式指定的冻结留出")
    parser.add_argument(
        "--samples",
        nargs="+",
        choices=tuple(SAMPLES),
        default=list(LEGACY_REGRESSION_SAMPLES),
        help="样本 ID；不指定时只运行已降级的旧三样本回归",
    )
    args = parser.parse_args()
    out_dir = holdout_output_dir(REPO)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for sample_id, pdf_rel in selected_samples(args.samples).items():
        pdf = REPO / pdf_rel
        content = pdf.read_bytes()
        try:
            result = extract_statements(content)  # 自动适配器选择 = 系统现状
            extracted = {
                "sample": sample_id,
                "adapter_id": result.adapter_id,
                "unit": result.unit_note,
                "page_count": result.page_count,
                "source_sha256": result.source_sha256,
                "statements": result.statements,
                "checks": [
                    {
                        "label": c.label,
                        "left": str(c.left),
                        "right": str(c.right),
                        "status": c.status,
                    }
                    for c in result.checks
                ],
                "warnings": list(result.warnings),
            }
        except Exception as exc:  # 首跑失败全量留痕
            extracted = {
                "sample": sample_id,
                "error": f"{type(exc).__name__}: {exc}",
                "statements": {},
            }
        (out_dir / f"{sample_id}_extracted.yaml").write_text(
            yaml.safe_dump(extracted, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        oracle = yaml.safe_load(
            (REPO / f"validation/financial_reports/oracle/{sample_id}.yaml").read_text(
                encoding="utf-8"
            )
        )
        diff = diff_sample(sample_id, extracted, oracle)
        (out_dir / f"{sample_id}_diff.json").write_text(
            json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary[sample_id] = {
            "adapter": extracted.get("adapter_id"),
            "error": extracted.get("error"),
            **diff["counts"],
            "total": diff["total"],
            "rows_extracted": diff["rows_extracted"],
        }
        print(
            f"[{sample_id}] adapter={extracted.get('adapter_id')} "
            f"rows={diff['rows_extracted']} "
            f"matched={diff['counts']['matched']} "
            f"mismatched={diff['counts']['mismatched']} "
            f"not_comparable={diff['counts']['not_comparable']} / {diff['total']}"
            + (f"  ERROR={extracted['error']}" if extracted.get("error") else "")
        )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n输出目录: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
