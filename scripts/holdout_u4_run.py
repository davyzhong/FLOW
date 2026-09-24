#!/usr/bin/env python3
"""U4 留出泛化验收首跑 harness（2026-09-25）。

规程（oracle-register §4 / unified-next-plan U4）：
- 对三份冻结留出样本（tencent_fy2025 / sf_2026h1 / zto_2026q1）运行**当前未修改**
  的抽取管线（extract_statements 自动适配器选择，即系统现状）；
- 原始抽取输出全量留存于 validation/financial_reports/holdout_runs/<date>/；
- 与 oracle/<sample>.yaml 逐行 diff，三级分类：matched / mismatched / not_comparable；
- 首跑原始失败全部保留，不得为通过而调参；结果登记
  docs/implementation/objective-analysis/holdout-results.md。

用法（仓库根目录）：
    services/api/.venv/bin/python scripts/holdout_u4_run.py
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "services/api/src"))

from flow_api.statements.extraction import extract_statements  # noqa: E402

SAMPLES = {
    "sf_2026h1": "docs/knowledge-base/02_research/original/p5_samples/sf_002352/SF_2026_H1_report.pdf",
    "tencent_fy2025": "docs/knowledge-base/02_research/original/p5_samples/tencent_0700/Tencent_FY2025_annual_report.pdf",
    "zto_2026q1": "validation/financial_reports/original/zto_2026q1/ZTO_2026_Q1_results_announcement_c.pdf",
}

_DASH = "－—−‒–"


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
    for r in rows:
        if norm_name(str(r.get("item") or r.get("name") or "")) == target:
            return r
    cands = []
    for r in rows:
        rn = norm_name(str(r.get("item") or r.get("name") or ""))
        if rn and target and (target in rn or rn in target):
            cands.append(r)
    if len(cands) == 1:
        return cands[0]
    # 多个候选时不猜：视为未命中（not_comparable），首跑留痕从严
    return None


def diff_sample(sample_id: str, extracted: dict, oracle: dict) -> dict:
    rows = load_rows(extracted)
    results = []
    entries = []
    for k in oracle.get("key_items") or []:
        entries.append({"tier": "key_item", "item": k["item"], "value": k["value"],
                        "page": k.get("source_page")})
    for s in oracle.get("supplementary_lines") or []:
        entries.append({"tier": "supplementary", "item": s["item"], "value": s["value"],
                        "page": s.get("page")})
    counts = {"matched": 0, "mismatched": 0, "not_comparable": 0}
    for e in entries:
        row = find_row(rows, e["item"])
        if row is None:
            cls = "not_comparable"
            detail = "抽取输出中无对应行"
            got = None
        else:
            got = row.get("value_current", row.get("value"))
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
    return {"counts": counts, "total": total, "rows_extracted": len(rows),
            "results": results}


def main() -> int:
    run_date = datetime.date.today().isoformat()
    out_dir = REPO / "validation/financial_reports/holdout_runs" / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for sample_id, pdf_rel in SAMPLES.items():
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
                "checks": [{"label": c.label, "left": str(c.left), "right": str(c.right),
                            "status": c.status} for c in result.checks],
                "warnings": list(result.warnings),
            }
        except Exception as exc:  # 首跑失败全量留痕
            extracted = {"sample": sample_id, "error": f"{type(exc).__name__}: {exc}",
                         "statements": {}}
        (out_dir / f"{sample_id}_extracted.yaml").write_text(
            yaml.safe_dump(extracted, allow_unicode=True, sort_keys=False), encoding="utf-8")

        oracle = yaml.safe_load(
            (REPO / f"validation/financial_reports/oracle/{sample_id}.yaml").read_text(encoding="utf-8"))
        diff = diff_sample(sample_id, extracted, oracle)
        (out_dir / f"{sample_id}_diff.json").write_text(
            json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
        summary[sample_id] = {
            "adapter": extracted.get("adapter_id"),
            "error": extracted.get("error"),
            **diff["counts"], "total": diff["total"],
            "rows_extracted": diff["rows_extracted"],
        }
        print(f"[{sample_id}] adapter={extracted.get('adapter_id')} "
              f"rows={diff['rows_extracted']} "
              f"matched={diff['counts']['matched']} "
              f"mismatched={diff['counts']['mismatched']} "
              f"not_comparable={diff['counts']['not_comparable']} / {diff['total']}"
              + (f"  ERROR={extracted['error']}" if extracted.get("error") else ""))
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n输出目录: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
