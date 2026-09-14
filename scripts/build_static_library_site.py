#!/usr/bin/env python3
"""生成 FLOW 静态资料库站点（docs/library/index.html）。

把项目内的版本化静态数据集（指标字典、会计基础、经营指标、P5 覆盖矩阵、
反向解析财报与事实库）打包成一个**零依赖**的单文件 HTML：
不依赖服务器 / 数据库 / 网络，双击 file:// 即可浏览；左侧菜单、右侧内容。

用法：
    python3 scripts/build_static_library_site.py
    # 输出 docs/library/index.html

数据集变更后重新运行本脚本即可；输出文件随仓库提交，供离线查阅。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "metrics"
P5 = ROOT / "docs" / "implementation" / "p5"
OUT = ROOT / "docs" / "library" / "index.html"

COMPANY_NAMES = {
    "alibaba": "阿里巴巴（9988.HK）",
    "cainiao": "菜鸟",
    "jdl": "京东物流（2618.HK）",
    "sf": "顺丰控股（002352.SZ）",
    "tencent": "腾讯控股（0700.HK）",
}

STATEMENT_FILES = sorted(
    p for p in P5.glob("*_statements.yaml")
)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def period_of(stem: str) -> str:
    # alibaba_2026fy_statements → FY2026；sf_2026q1_statements → 2026Q1
    token = stem.split("_")[1]
    if token.endswith("fy"):
        return f"FY{token[:-2]}"
    return token.upper()


def company_of(stem: str) -> str:
    return stem.split("_")[0]


def build_reports() -> list[dict]:
    reports = []
    for path in STATEMENT_FILES:
        data = load_yaml(path)
        statements = data.get("statements") or {}
        tables = []
        for name, rows in statements.items():
            if not isinstance(rows, list):
                continue
            columns: list[str] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for key in row:
                    if key != "item" and key not in columns:
                        columns.append(key)
            tables.append({"name": name, "columns": columns, "rows": rows})
        reports.append(
            {
                "company": company_of(path.stem),
                "company_name": COMPANY_NAMES.get(company_of(path.stem), company_of(path.stem)),
                "period": period_of(path.stem),
                "unit": data.get("unit", ""),
                "source_pdf": data.get("source_pdf", ""),
                "tables": tables,
            }
        )
    order = {"sf": 0, "tencent": 1, "jdl": 2, "cainiao": 3, "alibaba": 4}
    reports.sort(key=lambda r: (order.get(r["company"], 9), r["period"]))
    return reports


def main() -> None:
    metric_dict = load_yaml(CONFIG / "metric_dictionary_v1_1.yaml")
    accounting = load_yaml(CONFIG / "accounting_foundation_v1.yaml")
    operations = load_yaml(CONFIG / "operations_dictionary_v1.yaml")
    coverage = load_yaml(CONFIG / "p5_metric_coverage_v1.yaml")
    facts_doc = load_yaml(P5 / "statement_facts.yaml")
    reports = build_reports()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metric_dictionary": metric_dict,
        "accounting": accounting,
        "operations": operations,
        "coverage": coverage,
        "facts": facts_doc["facts"],
        "facts_meta": facts_doc["meta"],
        "reports": reports,
    }
    blob = json.dumps(payload, ensure_ascii=False, default=str).replace("</", "<\\/")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = HTML.replace("__DATA__", blob)
    OUT.write_text(html, encoding="utf-8")
    # Widget 版：同一内容与交互，追加 Kimi 设计令牌覆盖层（透明背景、看板内自适应），
    # 供 Dashboard Widget 的 index.html 使用。
    widget_out = OUT.parent / "widget.html"
    widget_out.write_text(html.replace("</style>", WIDGET_OVERRIDES + "\n</style>"), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"written: {OUT} ({size_kb:.0f} KB)")
    print(f"written: {widget_out} (widget variant)")
    print(
        "sections: "
        f"通用指标 {len(metric_dict.get('metrics_general') or [])} · "
        f"物流指标 {len(metric_dict.get('metrics_logistics') or [])} · "
        f"会计科目 {len(accounting.get('accounts') or [])} · "
        f"覆盖矩阵 {len(coverage.get('metrics') or [])}×{len(coverage.get('snapshots') or [])} · "
        f"财报 {len(reports)} 份 · 事实 {len(facts_doc['facts'])} 条"
    )


WIDGET_OVERRIDES = """
/* ---- Dashboard Widget 变体：Kimi 设计令牌覆盖层（追加于末尾，级联生效） ---- */
body { background: transparent; color: var(--kimi-color-text-primary, #1c2634);
  font-family: var(--kimi-font-sans, sans-serif); }
nav { background: transparent; color: var(--kimi-color-text-secondary, #66788f);
  border-right: 1px solid var(--kimi-color-border, #e2e8f0); }
nav .brand { border-bottom-color: var(--kimi-color-border, #e2e8f0); }
nav .brand b { color: var(--kimi-color-text-primary, #1c2634); }
nav .brand span { color: var(--kimi-color-text-tertiary, #66788f); }
nav a { color: var(--kimi-color-text-secondary, #66788f); }
nav a:hover { background: var(--kimi-color-surface-muted, #f1f5f9); }
nav a.active { background: var(--kimi-color-surface-muted, #f1f5f9);
  color: var(--kimi-color-text-primary, #1c2634);
  border-left-color: var(--kimi-color-text-primary, #1c2634); }
nav .group { color: var(--kimi-color-text-quaternary, #94a3b8); }
.card, .metric, details { background: transparent;
  border-color: var(--kimi-color-border, #e2e8f0); }
.card b { font-weight: 500; }
table { background: transparent; border-color: var(--kimi-color-border, #e2e8f0); }
th, td { border-bottom-color: var(--kimi-color-border, #e2e8f0); }
th { background: var(--kimi-color-surface-muted, #f1f5f9);
  color: var(--kimi-color-text-secondary, #475569); font-weight: 500; }
code { background: var(--kimi-color-surface-muted, #eef2f7);
  font-family: var(--kimi-font-mono, monospace); }
.chip { background: var(--kimi-color-surface-muted, #eaf1fe);
  color: var(--kimi-color-text-secondary, #2563eb); }
.chip.green { background: color-mix(in srgb, var(--kimi-color-positive, #18794e) 14%, transparent);
  color: var(--kimi-color-positive, #18794e); }
.chip.gray { background: var(--kimi-color-surface-muted, #eef2f7);
  color: var(--kimi-color-text-tertiary, #66788f); }
input[type=search], select { background: transparent;
  border-color: var(--kimi-color-border, #e2e8f0);
  color: var(--kimi-color-text-primary, #1c2634); font: inherit; }
.sub, .muted, .metric .caliber, ul.notes, .cov-miss { color: var(--kimi-color-text-tertiary, #8a97a8); }
.metric dt { color: var(--kimi-color-text-tertiary, #66788f); }
.scroll { border-color: var(--kimi-color-border, #e2e8f0); }
.ml-coverage__metric, .ml-coverage__table tbody .ml-coverage__metric { background: transparent; }
/* v2 报告风变量的看板映射：结构色走令牌，状态色（红/绿/黄）保留语义 */
:root {
  --th-bg: var(--kimi-color-surface-muted, #f1f5f9);
  --th-ink: var(--kimi-color-text-primary, #1c2634);
  --zebra: var(--kimi-color-surface-muted, #f6f8fb);
  --navy: var(--kimi-color-text-primary, #16324f);
  --navy-2: var(--kimi-color-text-secondary, #1f4e79);
}
.kpi, .verdict { background: transparent; border-color: var(--kimi-color-border, #e2e8f0); }
.kpi .value { color: var(--kimi-color-text-primary, #16324f); }
.hero h1 { color: var(--kimi-color-text-primary, #16324f); }
h2.band { color: var(--kimi-color-text-primary, #16324f);
  border-left-color: var(--kimi-color-text-primary, #16324f); }
td.cov-hit { background: transparent; color: var(--kimi-color-text-primary, #16324f); }
tbody tr:nth-child(even) td.cov-hit { background: var(--kimi-color-surface-muted, #f6f8fb); }
.grade.b { background: var(--kimi-color-surface-muted, #e8f0f7);
  color: var(--kimi-color-text-secondary, #1f4e79); }
.grade.c { background: var(--kimi-color-surface-muted, #e2e8f0);
  color: var(--kimi-color-text-tertiary, #66788f); }
/* 看板表面：宿主给定视口，左侧导航吸顶、右侧内容滚动 */
.on-canvas .layout { height: 100vh; min-height: 0; }
.on-canvas main { max-height: 100vh; overflow-y: auto; }
"""


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FLOW 静态资料库 · 指标 / 会计 / 真实财报</title>
<style>
  :root {
    --ink: #1c2634; --muted: #66788f; --line: #e2e8f0; --bg: #f4f6f9;
    --card: #ffffff; --accent: #2563eb; --accent-soft: #eaf1fe; --good: #18794e;
    /* v2 商务报告风（借鉴经营分析 PPT）：深藏青 + 中国红 + 状态三色 */
    --navy: #16324f; --navy-2: #1f4e79; --red: #c0392b; --red-soft: #fbeae8;
    --ok: #1a7f4b; --ok-soft: #e5f5ec; --warn: #b7791f; --warn-soft: #fdf3e3;
    --bad: #c0392b; --bad-soft: #fbeae8;
    --th-bg: var(--navy); --th-ink: #ffffff; --zebra: #f6f8fb;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.65 -apple-system, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }
  .layout { display: flex; min-height: 100vh; }
  nav { width: 232px; flex: none; background: #101c2e; color: #cbd5e1;
    padding: 20px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
  nav .brand { padding: 0 20px 16px; border-bottom: 1px solid #24344d; margin-bottom: 10px; }
  nav .brand b { color: #fff; font-size: 16px; display: block; }
  nav .brand span { font-size: 11.5px; color: #7f93ad; }
  nav a { display: block; padding: 8px 20px; color: #cbd5e1; text-decoration: none;
    font-size: 13.5px; border-left: 3px solid transparent; cursor: pointer; }
  nav a:hover { background: #1a2a42; }
  nav a.active { background: #1a2a42; color: #fff; border-left-color: var(--accent); }
  nav .group { padding: 14px 20px 4px; font-size: 11px; color: #64748b; letter-spacing: .08em; }
  main { flex: 1; min-width: 0; padding: 28px 34px 60px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 16px; margin: 26px 0 10px; }
  .sub { color: var(--muted); font-size: 12.5px; margin: 0 0 18px; }
  section { display: none; }
  section.show { display: block; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px; margin: 16px 0; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }
  .card b { font-size: 24px; display: block; }
  .card span { color: var(--muted); font-size: 12.5px; }
  table { width: 100%; border-collapse: collapse; background: var(--card);
    border: 1px solid var(--line); font-size: 13px; }
  th, td { padding: 6px 12px; border-bottom: 1px solid var(--line); text-align: left;
    vertical-align: top; }
  th { background: var(--th-bg); color: var(--th-ink); font-weight: 500; white-space: nowrap; }
  tbody tr:nth-child(even) td, tbody tr:nth-child(even) th[scope=row] { background: var(--zebra); }
  td.neg { color: var(--red); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  code { background: #eef2f7; border-radius: 4px; padding: 1px 5px; font-size: 12px; }
  .chip { display: inline-block; background: var(--accent-soft); color: var(--accent);
    border-radius: 999px; padding: 0 8px; font-size: 11.5px; margin-right: 4px; }
  .chip.gray { background: #eef2f7; color: var(--muted); }
  .chip.green { background: #e5f5ec; color: var(--good); }
  .toolbar { display: flex; gap: 10px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
  input[type=search], select { padding: 6px 10px; border: 1px solid var(--line);
    border-radius: 8px; font-size: 13px; background: #fff; }
  input[type=search] { width: 260px; }
  .metric { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 14px 18px; margin-bottom: 12px; }
  .metric h3 { margin: 0 0 4px; font-size: 15px; }
  .metric h3 code { margin-left: 8px; }
  .metric .def { margin: 6px 0; }
  .metric dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 4px 20px; margin: 8px 0; font-size: 12.8px; }
  .metric dt { color: var(--muted); display: inline; }
  .metric dd { display: inline; margin-left: 6px; }
  .metric .caliber { font-size: 12.5px; color: var(--muted); margin: 4px 0 0; }
  .scroll { overflow-x: auto; }
  .cov-miss { color: #a3b0c2; font-size: 12px; }
  .muted { color: var(--muted); font-size: 12.5px; }
  ul.notes { padding-left: 18px; color: var(--muted); font-size: 12.5px; }
  details { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 10px 16px; margin-bottom: 8px; }
  details summary { cursor: pointer; font-size: 13.5px; }
  .pill { float: right; color: var(--muted); font-size: 12px; }

  /* ===== v2 商务报告风组件（借鉴经营分析 PPT） ===== */
  /* 页眉：顶部红线 + 超大标题（黑+红强调词）+ 副标题 */
  .hero { border-top: 4px solid var(--red); padding-top: 14px; margin-bottom: 20px; }
  .hero .kicker { color: var(--muted); font-size: 12px; letter-spacing: .35em; margin-bottom: 6px; }
  .hero h1 { font-size: 34px; line-height: 1.2; font-weight: 600; color: var(--navy); margin: 0 0 6px; }
  .hero h1 em { color: var(--red); font-style: normal; }
  .hero .lede { color: var(--muted); font-size: 14px; margin: 0; }
  /* KPI 卡带：图标圆章 + 大数字 + 同比/较上期变动 */
  .kpis { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px; margin: 14px 0 18px; }
  .kpi { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 14px 16px 12px; display: flex; gap: 12px; align-items: flex-start; }
  .kpi .seal { flex: none; width: 40px; height: 40px; border-radius: 50%;
    background: var(--navy); color: #fff; display: grid; place-items: center;
    font-size: 17px; font-weight: 500; }
  .kpi.red .seal { background: var(--red); }
  .kpi .name { font-size: 12.5px; color: var(--muted); }
  .kpi .value { font-size: 25px; font-weight: 500; color: var(--navy); line-height: 1.15;
    font-variant-numeric: tabular-nums; }
  .kpi .value small { font-size: 13px; color: var(--muted); font-weight: 400; }
  .kpi .foot { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .delta-up { color: var(--red); font-weight: 500; }
  .delta-down { color: var(--ok); font-weight: 500; }
  .delta-flat { color: var(--muted); }
  /* 结论条：红竖线 + 加粗判断 */
  .verdict { border-left: 4px solid var(--red); background: var(--card);
    border-radius: 0 8px 8px 0; padding: 10px 16px; margin: 14px 0;
    font-size: 13.5px; color: var(--ink); }
  .verdict b { color: var(--navy); }
  /* 覆盖率进度条（列头用） */
  .covbar { width: 84px; height: 6px; border-radius: 999px; background: var(--line);
    overflow: hidden; margin: 3px auto 0; }
  .covbar i { display: block; height: 100%; border-radius: 999px; }
  .covbar.hi i { background: var(--ok); } .covbar.mid i { background: var(--warn); }
  .covbar.lo i { background: var(--bad); }
  .covpct { font-size: 11.5px; font-weight: 500; }
  .covpct.hi { color: var(--ok); } .covpct.mid { color: var(--warn); } .covpct.lo { color: var(--bad); }
  /* 覆盖矩阵单元格热力：可计算=白底深字；缺口=浅灰底淡字 */
  td.cov-hit { background: #fff; color: var(--navy); font-weight: 500; }
  tbody tr:nth-child(even) td.cov-hit { background: var(--zebra); }
  td.cov-miss2 { background: var(--red-soft); color: #b89a96; font-size: 11.5px; }
  tbody tr:nth-child(even) td.cov-miss2 { background: #f7e9e7; }
  /* 覆盖等级字母（借鉴评价矩阵 A+/A/B+） */
  .grade { display: inline-block; min-width: 30px; text-align: center; font-weight: 600;
    border-radius: 6px; padding: 1px 6px; font-size: 12px; }
  .grade.a { color: var(--red); background: var(--red-soft); }
  .grade.b { color: var(--navy-2); background: #e8f0f7; }
  .grade.c { color: var(--muted); background: var(--line); }
  /* 状态胶囊：安全/关注/预警 */
  .status { display: inline-block; border-radius: 999px; padding: 1px 10px;
    font-size: 12px; font-weight: 500; }
  .status.ok { background: var(--ok-soft); color: var(--ok); }
  .status.warn { background: var(--warn-soft); color: var(--warn); }
  .status.bad { background: var(--bad-soft); color: var(--bad); }
  /* 分区标题：左侧 navy 竖条 */
  h2.band { border-left: 5px solid var(--navy); padding-left: 10px; font-size: 15.5px;
    color: var(--navy); margin: 26px 0 10px; }
</style>
</head>
<body>
<div class="layout">
  <nav id="nav">
    <div class="brand"><b>FLOW 静态资料库</b><span id="gen"></span></div>
  </nav>
  <main id="main"></main>
</div>
<script id="flow-data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("flow-data").textContent);
const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (v) => {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") return v.toLocaleString("zh-CN");
  return esc(v);
};
const COMPANY_SHORT = { alibaba_9988: "阿里巴巴", cainiao: "菜鸟",
  jd_logistics_2618: "京东物流", sf_002352: "顺丰控股", tencent_0700: "腾讯控股" };

/* ===== v2 报告风 helper：事实取数 / 亿元换算 / 同比徽标 / KPI 卡 ===== */
const FACT_MAP = new Map(DATA.facts.map((f) => [`${f.company}|${f.period}|${f.item_id}|${f.role}`, f]));
function fact(company, period, itemId, role) {
  return FACT_MAP.get(`${company}|${period}|${itemId}|${role}`) || null;
}
function toYi(f) {  // 披露单位 → 亿元
  if (!f || f.value === null || f.value === undefined) return null;
  const v = Number(f.value);
  return f.unit === "千元" ? v / 1e5 : f.unit === "百万元" ? v / 100 : v / 1e8;
}
const yiFmt = (v) => v === null ? null : v.toLocaleString("zh-CN", { maximumFractionDigits: 1 });
function deltaBadge(cur, prev, suffix = "%") {  // 同比/环比徽标：升红▲ 降绿▼
  if (cur === null || prev === null || !prev) return '<span class="delta-flat">—</span>';
  if (suffix === "pct") {  // 比率类指标：变动按百分点差，不按相对幅度
    const d = cur - prev;
    const cls = d > 0.005 ? "delta-up" : d < -0.005 ? "delta-down" : "delta-flat";
    const arrow = d > 0.005 ? "▲" : d < -0.005 ? "▼" : "";
    return `<span class="${cls}">${d > 0 ? "+" : ""}${d.toFixed(1)}pct ${arrow}</span>`;
  }
  const pct = ((cur - prev) / Math.abs(prev)) * 100;
  // 基数异常（如反向解析把季度数对上年度数）时同比无意义，按财报惯例标注 n.m.
  if (Math.abs(pct) > 500)
    return '<span class="delta-flat" title="基数差异过大，同比不具可比性">n.m.</span>';
  const cls = pct > 0.05 ? "delta-up" : pct < -0.05 ? "delta-down" : "delta-flat";
  const arrow = pct > 0.05 ? "▲" : pct < -0.05 ? "▼" : "";
  const sign = pct > 0 ? "+" : "";
  return `<span class="${cls}">${sign}${pct.toFixed(1)}${suffix} ${arrow}</span>`;
}
function kpiCard(name, valueHtml, footHtml, red = false) {
  return `<div class="kpi${red ? " red" : ""}">
    <div class="seal">${esc(name.slice(0, 1))}</div>
    <div><div class="name">${esc(name)}</div>
    <div class="value">${valueHtml}</div>
    <div class="foot">${footHtml || ""}</div></div></div>`;
}
function kpiMoney(company, period, name, ids, red = false) {  // ids: [候选 item_id]
  let cur = null, prev = null, used = null;
  for (const id of ids) {
    cur = toYi(fact(company, period, id, "cur")) ?? toYi(fact(company, period, id, "end"));
    prev = toYi(fact(company, period, id, "prev_yoy")) ?? toYi(fact(company, period, id, "open"));
    if (cur !== null) { used = id; break; }
  }
  if (cur === null) return "";
  return kpiCard(name, `${yiFmt(cur)}<small> 亿元</small>`,
    `同比 ${deltaBadge(cur, prev)}`, red);
}
function hero(titleA, titleB, lede) {
  return `<div class="hero">
    <div class="kicker">数据驱动决策 ｜ 财务创造价值</div>
    <h1>${esc(titleA)}<em>${esc(titleB)}</em></h1>
    <p class="lede">${esc(lede)}</p></div>`;
}
function covGrade(ratio) {  // 行/列覆盖率 → 字母等级（借鉴评价矩阵）
  if (ratio >= 0.85) return ["A+", "a"];
  if (ratio >= 0.65) return ["A", "a"];
  if (ratio >= 0.45) return ["B+", "b"];
  if (ratio >= 0.25) return ["B", "b"];
  return ["C", "c"];
}

const SECTIONS = [
  { group: "总览" },
  { id: "overview", label: "数据集总览", render: renderOverview },
  { group: "指标库" },
  { id: "general", label: "通用指标", render: () => renderMetrics("metrics_general", "通用指标") },
  { id: "logistics", label: "物流行业指标", render: () => renderMetrics("metrics_logistics", "物流行业指标") },
  { id: "relations", label: "勾稽与分解关系", render: renderRelations },
  { id: "mapping", label: "取数映射 CAS↔IFRS", render: renderMapping },
  { group: "会计基础" },
  { id: "accounts", label: "会计科目", render: renderAccounts },
  { id: "standards", label: "准则与分录模板", render: renderStandards },
  { group: "真实财报（P5 反向解析）" },
  { id: "coverage", label: "指标覆盖矩阵", render: renderCoverage },
  { id: "reports", label: "财报浏览器", render: renderReports },
  { id: "facts", label: "事实库", render: renderFacts },
  { group: "其他字典" },
  { id: "operations", label: "经营指标字典", render: renderOperations },
];

function nav() {
  const el = document.getElementById("nav");
  let html = el.querySelector(".brand").outerHTML;
  for (const s of SECTIONS) {
    if (s.group) { html += `<div class="group">${esc(s.group)}</div>`; continue; }
    html += `<a data-id="${s.id}">${esc(s.label)}</a>`;
  }
  el.innerHTML = html;
  el.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => show(a.dataset.id)));
}
function show(id) {
  document.querySelectorAll("nav a").forEach((a) =>
    a.classList.toggle("active", a.dataset.id === id));
  const main = document.getElementById("main");
  const sec = SECTIONS.find((s) => s.id === id);
  main.innerHTML = `<section class="show">${sec.render()}</section>`;
  sec.after?.();
  location.hash = id;
}

function renderOverview() {
  const d = DATA.metric_dictionary, a = DATA.accounting, c = DATA.coverage;
  const totalComputable = c.snapshots.reduce((s, x) => s + x.computable, 0);
  const totalCells = c.snapshots.reduce((s, x) => s + x.total, 0);
  const avgCov = Math.round((totalComputable / totalCells) * 100);
  const kpis = [
    kpiCard("通用指标", (d.metrics_general || []).length, "指标字典 v1.1 · D047"),
    kpiCard("物流行业指标", (d.metrics_logistics || []).length, "物流口径专属"),
    kpiCard("会计科目", (a.accounts || []).length, `${(a.entry_templates || []).length} 套分录模板`),
    kpiCard("反向解析财报", DATA.reports.length, "5 家公司 · 4 个市场样本", true),
    kpiCard("标准化事实", DATA.facts.length, "科目级 · 可溯源原文"),
    kpiCard("指标覆盖均值", avgCov + '<small>%</small>', `${c.snapshots.length} 个公司期间快照`, true),
  ];
  return `
    ${hero("FLOW 静态资料库 · ", "指标体系与真实财报", "指标字典、会计基础与 5 家真实财报反向解析成果的总览；全部数据来自仓库内版本化 YAML，零服务器、零数据库、可离线。")}
    <div class="kpis">${kpis.join("")}</div>
    <div class="verdict"><b>核心判断：</b>指标库与会计基础已完成版本化沉淀（D040/D047），真实财报侧已打通「抽取 → 勾稽 → 事实库 → 覆盖矩阵」全链路；当前瓶颈在 IFRS 样本的资产负债明细行披露密度，覆盖缺口均显式标注、不推测填补。</div>
    <h2 class="band">数据集版本登记</h2>
    <table><thead><tr><th>数据集</th><th>ID</th><th>状态</th><th>决策 / 生成器</th></tr></thead><tbody>
      <tr><td>指标字典</td><td><code>${esc(d.dictionary_id)}</code></td><td><span class="status ok">${esc(d.status)}</span></td><td>${esc(d.decision_ref)}</td></tr>
      <tr><td>会计基础</td><td><code>${esc(a.dataset_id)}</code></td><td><span class="status ok">${esc(a.status)}</span></td><td>${esc(a.decision_ref)}</td></tr>
      <tr><td>经营指标</td><td><code>${esc(DATA.operations.dictionary_id)}</code></td><td><span class="status ok">${esc(DATA.operations.status)}</span></td><td>${esc(DATA.operations.decision_ref)}</td></tr>
      <tr><td>覆盖矩阵</td><td><code>${esc(c.dataset_id)}</code></td><td><span class="status warn">生成物</span></td><td><code>${esc(c.generator)}</code></td></tr>
      <tr><td>事实库</td><td><code>${esc(DATA.facts_meta.dataset_id || "flow.p5_statement_facts.v1")}</code></td><td><span class="status warn">生成物</span></td><td><code>p5_build_fact_store.py</code></td></tr>
    </tbody></table>
    <h2 class="band">使用方式</h2>
    <ul class="notes">
      <li>左侧菜单切换内容区；指标、映射、科目、事实列表均支持页内搜索。</li>
      <li>数据集更新后重新生成：<code>python3 scripts/build_static_library_site.py</code>（同时产出看板 Widget 变体 widget.html）。</li>
      <li>在线版本（需完整服务栈）：<code>/metric-library</code> 的「真实财报覆盖」tab 与 <code>/statements</code> 报表分析页。</li>
      <li>生成时间：${esc(DATA.generated_at)}</li>
    </ul>`;
}

function metricCard(m) {
  const chips = [
    m.tier === "core" ? '<span class="chip">常用</span>' : '<span class="chip gray">专业</span>',
    m.mpm ? '<span class="chip green">MPM</span>' : "",
  ].join("");
  const row = (label, value) => value ? `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>` : "";
  return `<article class="metric" data-q="${esc((m.metric_code + " " + m.name + " " +
      (m.formula_text || "")).toLowerCase())}">
    <h3>${esc(m.name)}<code>${esc(m.metric_code)}</code>${chips}</h3>
    <p class="def">${esc(m.definition || "")}</p>
    <dl>
      ${row("公式", (m.formula_text || "") + (m.unit ? `（${m.unit}）` : ""))}
      ${row("CAS 取数", (m.source_cas || []).join("、"))}
      ${row("IFRS 对照", m.source_ifrs)}
      ${row("时间行为", m.time_behavior)}
      ${row("参考基准", m.benchmark)}
      ${row("依赖", (m.depends_on || []).join("、"))}
      ${row("分析维度", (m.analysis_dimensions || []).join(" · "))}
      ${row("来源", m.provenance)}
    </dl>
    ${m.caliber ? `<p class="caliber">口径：${esc(m.caliber)}</p>` : ""}
  </article>`;
}

function renderMetrics(key, title) {
  const list = DATA.metric_dictionary[key] || [];
  return `<h1>${title}</h1>
    <p class="sub">${esc(DATA.metric_dictionary.dictionary_id)} · 共 ${list.length} 个指标</p>
    <div class="toolbar"><input type="search" placeholder="搜索编码 / 名称 / 公式…"
      oninput="filterCards(this)"><span class="muted" data-count></span></div>
    <div class="list">${list.map(metricCard).join("")}</div>`;
}

function filterCards(input) {
  const q = input.value.trim().toLowerCase();
  const list = input.closest("section").querySelectorAll(".metric");
  let n = 0;
  list.forEach((el) => {
    const hit = !q || el.dataset.q.includes(q);
    el.style.display = hit ? "" : "none";
    if (hit) n++;
  });
  const counter = input.closest(".toolbar").querySelector("[data-count]");
  if (counter) counter.textContent = `${n} / ${list.length}`;
}

function renderRelations() {
  const rels = DATA.metric_dictionary.relations || [];
  return `<h1>勾稽与分解关系</h1><p class="sub">共 ${rels.length} 条</p>
    <table><thead><tr><th>关系</th><th>名称</th><th>表达式</th><th>说明</th><th>来源</th></tr></thead>
    <tbody>${rels.map((r) => `<tr><td><code>${esc(r.relation)}</code></td><td>${esc(r.name)}</td>
      <td>${esc(r.expression)}</td><td>${esc(r.note)}</td><td class="muted">${esc(r.provenance || "")}</td></tr>`).join("")}
    </tbody></table>`;
}

function renderMapping() {
  const items = DATA.metric_dictionary.report_items || {};
  const rows = Object.entries(items);
  return `<h1>取数映射（CAS↔IFRS）</h1><p class="sub">共 ${rows.length} 项报表项目映射</p>
    <div class="toolbar"><input type="search" placeholder="搜索项目 / CAS / IFRS…"
      oninput="filterRows(this)"></div>
    <table><thead><tr><th>报表项目</th><th>CAS 行项目</th><th>IFRS 对照</th></tr></thead>
    <tbody>${rows.map(([id, v]) => `<tr><td><code>${esc(id)}</code></td>
      <td>${esc(v.cas || "")}</td><td>${esc(v.ifrs || "")}</td></tr>`).join("")}
    </tbody></table>`;
}

function filterRows(input) {
  const q = input.value.trim().toLowerCase();
  input.closest("section").querySelectorAll("tbody tr").forEach((tr) => {
    tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? "" : "none";
  });
}

function renderAccounts() {
  const a = DATA.accounting;
  const list = a.accounts || [];
  return `<h1>会计科目</h1>
    <p class="sub">${esc(a.dataset_id)} · ${list.length} 个科目 ·
      准则范围 ${(a.standards_scope || []).join(" / ")}</p>
    <div class="toolbar"><input type="search" placeholder="搜索编号 / 名称…" oninput="filterRows(this)"></div>
    <table><thead><tr><th>编号</th><th>名称</th><th>类别</th><th>余额方向</th><th>状态</th></tr></thead>
    <tbody>${list.map((x) => `<tr><td><code>${esc(x.code)}</code></td><td>${esc(x.name)}</td>
      <td>${esc(x.category)}</td><td>${esc(x.balance_side)}</td><td>${esc(x.status)}</td></tr>`).join("")}
    </tbody></table>
    ${(a.known_gaps || []).length ? `<h2>已知缺口</h2><ul class="notes">${a.known_gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>` : ""}`;
}

function renderStandards() {
  const a = DATA.accounting;
  return `<h1>准则登记册</h1>
    <table><thead><tr><th>编号</th><th>名称</th><th>发布方</th><th>备注</th></tr></thead>
    <tbody>${(a.standards || []).map((s) => `<tr><td><code>${esc(s.id)}</code></td>
      <td>${esc(s.name)}</td><td>${esc(s.issuer || "")}</td><td class="muted">${esc(s.note || "")}</td></tr>`).join("")}
    </tbody></table>
    <h2>分录模板（${(a.entry_templates || []).length}）</h2>
    ${(a.entry_templates || []).map((t) => `<details>
      <summary><b>${esc(t.scenario)}</b> <code>${esc(t.template_id)}</code>
        <span class="pill">${esc(t.standard_ref || "")}</span></summary>
      ${t.business_context ? `<p class="muted">${esc(t.business_context)}</p>` : ""}
      <table><thead><tr><th>方向</th><th>科目</th><th>金额规则</th></tr></thead>
      <tbody>${(t.lines || []).map((l) => `<tr><td>${esc(l.direction)}</td>
        <td>${esc(l.account)}</td><td>${esc(l.amount_rule)}</td></tr>`).join("")}</tbody></table>
      <p class="muted">关联指标：${(t.related_metrics || []).join("、") || "—"}</p>
    </details>`).join("")}`;
}

function renderCoverage() {
  const c = DATA.coverage;
  const key = (s) => `${s.company} ${s.period}`;
  const pctOf = (s) => s.computable / s.total;
  const clsOf = (p) => p >= 0.65 ? "hi" : p >= 0.35 ? "mid" : "lo";
  const best = c.snapshots.reduce((a, b) => (pctOf(b) > pctOf(a) ? b : a));
  const totalComputable = c.snapshots.reduce((s, x) => s + x.computable, 0);
  const totalCells = c.snapshots.reduce((s, x) => s + x.total, 0);
  const missCells = totalCells - totalComputable;
  const kpis = [
    kpiCard("覆盖快照", c.snapshots.length, "5 家公司 · 15 个期间"),
    kpiCard("通用指标", c.metrics.length, "指标库 v0 评审集"),
    kpiCard("覆盖均值", Math.round((totalComputable / totalCells) * 100) + '<small>%</small>',
      `${totalComputable} / ${totalCells} 格可计算`, true),
    kpiCard("最佳快照", `${best.computable}<small>/${best.total}</small>`,
      `${COMPANY_SHORT[best.company] || best.company} ${best.period}`),
    kpiCard("缺口格", missCells, "逐格标注首个缺失科目", true),
  ];
  return `${hero("真实财报 · ", "指标覆盖矩阵", `${c.metrics.length} 个通用指标 × ${c.snapshots.length} 个公司期间快照；数值来自 P5 反向解析事实库，缺口显式标注，不推测填补。`)}
    <div class="kpis">${kpis.join("")}</div>
    <ul class="notes">${(c.caliber_notes || []).map((n) => `<li>${esc(n)}</li>`).join("")}</ul>
    <div class="scroll"><table>
      <thead><tr><th>指标</th>${c.snapshots.map((s) => {
        const p = pctOf(s), cls = clsOf(p);
        return `<th class="num">${esc(COMPANY_SHORT[s.company] || s.company)}
          <span class="muted" style="font-weight:400">${esc(s.period)}</span><br>
          <span class="covpct ${cls}">${s.computable}/${s.total} · ${Math.round(p * 100)}%</span>
          <span class="covbar ${cls}"><i style="width:${Math.round(p * 100)}%"></i></span></th>`;
      }).join("")}<th class="num">行覆盖<br>等级</th></tr></thead>
      <tbody>${c.metrics.map((m) => {
        const hits = c.snapshots.filter((s) => {
          const cell = (m.cells || {})[key(s)];
          return cell && cell.display !== null && cell.display !== undefined;
        }).length;
        const [g, gc] = covGrade(hits / c.snapshots.length);
        return `<tr>
        <td><code>${esc(m.metric_code)}</code> ${esc(m.name)}${m.unit ? `（${esc(m.unit)}）` : ""}</td>
        ${c.snapshots.map((s) => {
          const cell = (m.cells || {})[key(s)];
          if (!cell || cell.display === null || cell.display === undefined) {
            return `<td class="num cov-miss2" title="缺口：${esc(cell?.missing || "未映射")}">${cell?.missing ? "缺 " + esc(cell.missing) : "—"}</td>`;
          }
          return `<td class="num cov-hit">${esc(cell.display)}</td>`;
        }).join("")}
        <td class="num"><span class="grade ${gc}" title="${hits}/${c.snapshots.length} 快照可计算">${g}</span></td>
      </tr>`; }).join("")}</tbody>
    </table></div>
    <div class="verdict"><b>覆盖判断：</b>顺丰 2026Q1（CAS 全表披露）可计算 35/40 居首；京东物流 FY2025 达 29/40；
      阿里系样本受 IFRS 摘要式披露限制在 22/40 左右，缺口集中于存货、应收应付等资产负债明细行；
      腾讯单季业绩公告口径最薄（7/40），仅适合做盈利链指标。</div>
    <p class="muted">逐格取数说明见 docs/implementation/p5/metric_coverage_matrix.md；
      口径映射 docs/implementation/p5/item_alias_map_v1.yaml；悬停缺口格查看首个缺失科目。</p>`;
}

let reportState = { company: null, period: null };
// 财报文件键 → 事实库键（公司 + 期间标签映射；腾讯事实库期间为 2Q2026）
const FACT_KEY = {
  alibaba: ["alibaba_9988", (p) => p], cainiao: ["cainiao", (p) => p],
  jdl: ["jd_logistics_2618", (p) => p], sf: ["sf_002352", (p) => p],
  tencent: ["tencent_0700", (p) => (p === "2026Q2" ? "2Q2026" : p)],
};
function reportKpis(company, period) {
  const [fc, fp] = FACT_KEY[company] || [company, (p) => p];
  const per = fp(period);
  const cards = [
    kpiMoney(fc, per, "营业收入", ["is.revenue"], true),
    kpiMoney(fc, per, "归母净利润", ["is.attr_net_profit", "is.net_profit"], true),
    kpiMoney(fc, per, "经营现金流", ["cf.ocf"]),
    kpiMoney(fc, per, "总资产", ["bs.total_assets"]),
  ];
  // 资产负债率（期末）：负债总额 / 资产总额
  const ta = toYi(fact(fc, per, "bs.total_assets", "end"));
  const tl = toYi(fact(fc, per, "bs.total_liab", "end"));
  const ta0 = toYi(fact(fc, per, "bs.total_assets", "open"));
  const tl0 = toYi(fact(fc, per, "bs.total_liab", "open"));
  if (ta && tl) {
    const cur = (tl / ta) * 100;
    const prev = ta0 && tl0 ? (tl0 / ta0) * 100 : null;
    cards.push(kpiCard("资产负债率", cur.toFixed(1) + "<small>%</small>",
      `较期初 ${deltaBadge(cur, prev, "pct")}`));
  }
  const rev = toYi(fact(fc, per, "is.revenue", "cur"));
  const gp = toYi(fact(fc, per, "is.gross_profit", "cur"));
  const rev0 = toYi(fact(fc, per, "is.revenue", "prev_yoy"));
  const gp0 = toYi(fact(fc, per, "is.gross_profit", "prev_yoy"));
  if (rev && gp) {
    const cur = (gp / rev) * 100;
    const prev = rev0 && gp0 ? (gp0 / rev0) * 100 : null;
    cards.push(kpiCard("毛利率", cur.toFixed(1) + "<small>%</small>",
      `同比 ${deltaBadge(cur, prev, "pct")}`));
  }
  return cards.join("");
}
function reportVerdict(company, period) {
  const [fc, fp] = FACT_KEY[company] || [company, (p) => p];
  const per = fp(period);
  const rev = toYi(fact(fc, per, "is.revenue", "cur"));
  const rev0 = toYi(fact(fc, per, "is.revenue", "prev_yoy"));
  const np = toYi(fact(fc, per, "is.attr_net_profit", "cur")) ?? toYi(fact(fc, per, "is.net_profit", "cur"));
  const bits = [];
  if (rev !== null && rev0) {
    const pct = ((rev - rev0) / rev0) * 100;
    if (Math.abs(pct) <= 500) bits.push(`营业收入 ${yiFmt(rev)} 亿元，同比 ${pct >= 0 ? "增长" : "下降"} ${Math.abs(pct).toFixed(1)}%`);
    else bits.push(`营业收入 ${yiFmt(rev)} 亿元（同比基数异常，从略）`);
  } else if (rev !== null) bits.push(`营业收入 ${yiFmt(rev)} 亿元`);
  if (rev && np !== null) bits.push(`净利率 ${((np / rev) * 100).toFixed(1)}%`);
  if (!bits.length) return "";
  return `<div class="verdict"><b>本期速览：</b>${bits.join("；")}。数值由事实库标准科目计算，披露单位已换算为亿元。</div>`;
}
function renderReports() {
  const companies = [...new Map(DATA.reports.map((r) => [r.company, r.company_name]))];
  reportState.company = reportState.company || companies[0][0];
  const periods = DATA.reports.filter((r) => r.company === reportState.company).map((r) => r.period);
  reportState.period = periods.includes(reportState.period) ? reportState.period : periods[0];
  const report = DATA.reports.find((r) =>
    r.company === reportState.company && r.period === reportState.period);
  return `${hero("财报浏览器 · ", "反向解析原文", `${DATA.reports.length} 份财报的抽取原文表格；顶部 KPI 卡带由事实库标准科目计算，同比/较期初变动自动标注。`)}
    <div class="toolbar">
      <select onchange="reportState.company=this.value;show('reports')">
        ${companies.map(([id, name]) => `<option value="${id}"
          ${id === reportState.company ? "selected" : ""}>${esc(name)}</option>`).join("")}
      </select>
      <select onchange="reportState.period=this.value;show('reports')">
        ${periods.map((p) => `<option ${p === reportState.period ? "selected" : ""}>${esc(p)}</option>`).join("")}
      </select>
      <span class="muted">披露单位：${esc(report.unit)} · 来源：${esc(report.source_pdf)}</span>
    </div>
    <div class="kpis">${reportKpis(reportState.company, reportState.period)}</div>
    ${reportVerdict(reportState.company, reportState.period)}
    ${report.tables.map((t) => `<h2 class="band">${esc(t.name)}（${t.rows.length} 行）</h2>
      <div class="scroll"><table>
        <thead><tr><th>项目</th>${t.columns.map((c) => `<th class="num">${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${t.rows.map((r) => `<tr><td>${esc(r.item)}</td>
          ${t.columns.map((c) => {
            const v = r[c];
            const neg = typeof v === "number" && v < 0;
            return `<td class="num${neg ? " neg" : ""}">${fmt(v)}</td>`;
          }).join("")}</tr>`).join("")}
        </tbody></table></div>`).join("")}`;
}

let factState = { company: "", statement: "" };
function renderFacts() {
  const companies = [...new Set(DATA.facts.map((f) => f.company))];
  const statements = [...new Set(DATA.facts.map((f) => f.statement))];
  const rows = DATA.facts.filter((f) =>
    (!factState.company || f.company === factState.company) &&
    (!factState.statement || f.statement === factState.statement));
  return `<h1>事实库</h1>
    <p class="sub">标准化科目事实（item_id · role · value），共 ${DATA.facts.length} 条，当前 ${rows.length} 条。</p>
    <div class="toolbar">
      <select onchange="factState.company=this.value;show('facts')">
        <option value="">全部公司</option>
        ${companies.map((c) => `<option value="${c}" ${c === factState.company ? "selected" : ""}>
          ${esc(COMPANY_SHORT[c] || c)}</option>`).join("")}
      </select>
      <select onchange="factState.statement=this.value;show('facts')">
        <option value="">全部报表</option>
        ${statements.map((s) => `<option ${s === factState.statement ? "selected" : ""}>${esc(s)}</option>`).join("")}
      </select>
      <input type="search" placeholder="搜索 item_id / 映射行名…" oninput="filterRows(this)">
    </div>
    <div class="scroll"><table>
      <thead><tr><th>公司</th><th>期间</th><th>报表</th><th>科目</th><th>角色</th>
        <th class="num">值</th><th>单位</th><th>映射行名</th></tr></thead>
      <tbody>${rows.map((f) => `<tr>
        <td>${esc(COMPANY_SHORT[f.company] || f.company)}</td><td>${esc(f.period)}</td>
        <td>${esc(f.statement)}</td><td><code>${esc(f.item_id)}</code></td><td>${esc(f.role)}</td>
        <td class="num">${fmt(f.value)}</td><td>${esc(f.unit)}</td>
        <td class="muted">${esc(f.mapping || "")}</td></tr>`).join("")}
      </tbody></table></div>`;
}

function renderOperations() {
  const o = DATA.operations;
  const blocks = [];
  for (const [k, v] of Object.entries(o.domains || {})) {
    const metrics = (v && v.metrics) || [];
    blocks.push(`<h2>${esc(v.name || k)}（${metrics.length}）</h2>
      ${metrics.map((m) => `<article class="metric">
        <h3>${esc(m.name || m.metric_code)}<code>${esc(m.metric_code)}</code></h3>
        <p class="def">${esc(m.formula_text || m.definition || "")}</p>
        ${m.provenance ? `<p class="caliber">来源：${esc(m.provenance)}</p>` : ""}
      </article>`).join("")}`);
  }
  const dims = (o.dimensions || []).map((d) => `<tr><td>${esc(d.name)}</td>
    <td>${esc(d.values)}</td><td class="muted">${esc(d.note || "")}</td></tr>`).join("");
  return `<h1>经营指标字典</h1>
    <p class="sub"><code>${esc(o.dictionary_id)}</code> · ${esc(o.status)} · ${esc(o.decision_ref)} ·
      面向：${esc(o.audience || "")}</p>
    ${blocks.join("")}
    ${dims ? `<h2>分析维度</h2><table><thead><tr><th>维度</th><th>取值</th><th>说明</th></tr></thead>
      <tbody>${dims}</tbody></table>` : ""}
    ${(o.known_gaps || []).length ? `<h2>已知缺口</h2><ul class="notes">${o.known_gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>` : ""}`;
}

nav();
if (window.DaimonCanvas) document.documentElement.classList.add("on-canvas");
document.getElementById("gen").textContent = "生成于 " + DATA.generated_at.slice(0, 16).replace("T", " ");
show(location.hash.slice(1) || "overview");
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
