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
    OUT.write_text(HTML.replace("__DATA__", blob), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"written: {OUT} ({size_kb:.0f} KB)")
    print(
        "sections: "
        f"通用指标 {len(metric_dict.get('metrics_general') or [])} · "
        f"物流指标 {len(metric_dict.get('metrics_logistics') or [])} · "
        f"会计科目 {len(accounting.get('accounts') or [])} · "
        f"覆盖矩阵 {len(coverage.get('metrics') or [])}×{len(coverage.get('snapshots') or [])} · "
        f"财报 {len(reports)} 份 · 事实 {len(facts_doc['facts'])} 条"
    )


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FLOW 静态资料库 · 指标 / 会计 / 真实财报</title>
<style>
  :root {
    --ink: #1c2634; --muted: #66788f; --line: #e2e8f0; --bg: #f6f8fb;
    --card: #ffffff; --accent: #2563eb; --accent-soft: #eaf1fe; --good: #18794e;
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
  th { background: #f1f5f9; color: #475569; font-weight: 600; white-space: nowrap; }
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
  const cards = [
    [(d.metrics_general || []).length, "通用指标"],
    [(d.metrics_logistics || []).length, "物流行业指标"],
    [(d.relations || []).length, "勾稽 / 分解关系"],
    [Object.keys(d.report_items || {}).length, "CAS↔IFRS 映射"],
    [(a.accounts || []).length, "会计科目"],
    [(a.entry_templates || []).length, "分录模板"],
    [c.snapshots.length, "财报快照（5 家公司）"],
    [DATA.facts.length, "反向解析事实"],
    [DATA.reports.length, "反向解析财报"],
  ];
  return `
    <h1>FLOW 静态资料库</h1>
    <p class="sub">生成时间 ${esc(DATA.generated_at)} · 全部数据来自仓库内版本化 YAML
      （config/metrics/ 与 docs/implementation/p5/），本页面零服务器、零数据库、可离线。</p>
    <div class="cards">${cards.map(([n, l]) =>
      `<div class="card"><b>${n}</b><span>${l}</span></div>`).join("")}
    </div>
    <h2>数据集版本</h2>
    <table><thead><tr><th>数据集</th><th>ID</th><th>状态</th><th>决策</th></tr></thead><tbody>
      <tr><td>指标字典</td><td><code>${esc(d.dictionary_id)}</code></td><td>${esc(d.status)}</td><td>${esc(d.decision_ref)}</td></tr>
      <tr><td>会计基础</td><td><code>${esc(a.dataset_id)}</code></td><td>${esc(a.status)}</td><td>${esc(a.decision_ref)}</td></tr>
      <tr><td>经营指标</td><td><code>${esc(DATA.operations.dictionary_id)}</code></td><td>${esc(DATA.operations.status)}</td><td>${esc(DATA.operations.decision_ref)}</td></tr>
      <tr><td>覆盖矩阵</td><td><code>${esc(c.dataset_id)}</code></td><td>生成物</td><td>${esc(c.generator)}</td></tr>
      <tr><td>事实库</td><td><code>${esc(DATA.facts_meta.dataset_id || "flow.p5_statement_facts.v1")}</code></td><td>生成物</td><td>p5_build_fact_store.py</td></tr>
    </tbody></table>
    <h2>使用方式</h2>
    <ul class="notes">
      <li>左侧菜单切换内容区；所有列表支持页内搜索。</li>
      <li>重新生成：<code>python3 scripts/build_static_library_site.py</code>。</li>
      <li>在线版本（需完整服务栈）：<code>/metric-library</code> 与 <code>/statements</code>。</li>
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
  return `<h1>真实财报指标覆盖矩阵</h1>
    <p class="sub"><code>${esc(c.dataset_id)}</code> · ${c.metrics.length} 个通用指标 ×
      ${c.snapshots.length} 个公司期间快照 · 由 ${esc(c.generator)} 生成</p>
    <ul class="notes">${(c.caliber_notes || []).map((n) => `<li>${esc(n)}</li>`).join("")}</ul>
    <div class="scroll"><table>
      <thead><tr><th>指标</th>${c.snapshots.map((s) =>
        `<th class="num">${esc(COMPANY_SHORT[s.company] || s.company)}<br>
          <span class="muted">${esc(s.period)}</span><br>
          <span class="chip ${s.computable === s.total ? "green" : "gray"}">${s.computable}/${s.total}</span></th>`).join("")}
      </tr></thead>
      <tbody>${c.metrics.map((m) => `<tr>
        <td><code>${esc(m.metric_code)}</code> ${esc(m.name)}${m.unit ? `（${esc(m.unit)}）` : ""}</td>
        ${c.snapshots.map((s) => {
          const cell = (m.cells || {})[key(s)];
          if (!cell || cell.display === null || cell.display === undefined) {
            return `<td class="num cov-miss" title="${esc(cell?.missing || "")}">${cell?.missing ? "缺 " + esc(cell.missing) : "—"}</td>`;
          }
          return `<td class="num">${esc(cell.display)}</td>`;
        }).join("")}
      </tr>`).join("")}</tbody>
    </table></div>
    <p class="muted">逐格取数说明见 docs/implementation/p5/metric_coverage_matrix.md；
      口径映射 docs/implementation/p5/item_alias_map_v1.yaml。</p>`;
}

let reportState = { company: null, period: null };
function renderReports() {
  const companies = [...new Map(DATA.reports.map((r) => [r.company, r.company_name]))];
  reportState.company = reportState.company || companies[0][0];
  const periods = DATA.reports.filter((r) => r.company === reportState.company).map((r) => r.period);
  reportState.period = periods.includes(reportState.period) ? reportState.period : periods[0];
  const report = DATA.reports.find((r) =>
    r.company === reportState.company && r.period === reportState.period);
  return `<h1>财报浏览器（P5 反向解析）</h1>
    <p class="sub">${DATA.reports.length} 份财报的抽取原文表格，单位以各份披露为准。</p>
    <div class="toolbar">
      <select onchange="reportState.company=this.value;show('reports')">
        ${companies.map(([id, name]) => `<option value="${id}"
          ${id === reportState.company ? "selected" : ""}>${esc(name)}</option>`).join("")}
      </select>
      <select onchange="reportState.period=this.value;show('reports')">
        ${periods.map((p) => `<option ${p === reportState.period ? "selected" : ""}>${esc(p)}</option>`).join("")}
      </select>
      <span class="muted">单位：${esc(report.unit)} · 来源：${esc(report.source_pdf)}</span>
    </div>
    ${report.tables.map((t) => `<h2>${esc(t.name)}（${t.rows.length} 行）</h2>
      <div class="scroll"><table>
        <thead><tr><th>项目</th>${t.columns.map((c) => `<th class="num">${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${t.rows.map((r) => `<tr><td>${esc(r.item)}</td>
          ${t.columns.map((c) => `<td class="num">${fmt(r[c])}</td>`).join("")}</tr>`).join("")}
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
document.getElementById("gen").textContent = "生成于 " + DATA.generated_at.slice(0, 16).replace("T", " ");
show(location.hash.slice(1) || "overview");
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
