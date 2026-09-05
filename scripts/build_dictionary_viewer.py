#!/usr/bin/env python3
"""从指标库与会计基础 YAML 数据集生成自包含的字典浏览器 HTML。

用法：python3 scripts/build_dictionary_viewer.py
输入：docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml
      docs/knowledge-base/02_research/synthesis/会计基础数据集_v0_草案.yaml
输出：docs/knowledge-base/02_research/synthesis/字典浏览器_v0.html
每次数据集演进后重新运行本脚本即可看到最新进展。
"""
import json
import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SYN = ROOT / "docs/knowledge-base/02_research/synthesis"
OUT = SYN / "字典浏览器_v0.html"


def load():
    metrics = yaml.safe_load((SYN / "指标库初始数据集_v0_草案.yaml").read_text())
    accounting = yaml.safe_load((SYN / "会计基础数据集_v0_草案.yaml").read_text())
    return metrics, accounting


def main():
    metrics, accounting = load()
    payload = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "metrics_general": metrics["metrics_general"],
        "metrics_logistics": metrics["metrics_logistics"],
        "relations": metrics["relations"],
        "report_items": metrics["report_items"],
        "domains": metrics["domains"],
        "accounts": accounting["accounts"],
        "standards": accounting["standards"],
        "entry_templates": accounting["entry_templates"],
        "known_gaps": accounting.get("known_gaps", []),
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    html = TEMPLATE.replace("__DATA__", data_json)
    OUT.write_text(html)
    g = len(payload["metrics_general"])
    l = len(payload["metrics_logistics"])
    a = len(payload["accounts"])
    e = len(payload["entry_templates"])
    print(f"viewer written: {OUT}")
    print(f"stats: metrics={g}+{l}, accounts={a}, entries={e}, relations={len(payload['relations'])}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FLOW 字典浏览器 v0 — 指标库 · 会计基础数据</title>
<style>
  :root { --bg:#f5f6f8; --panel:#fff; --ink:#1a2332; --muted:#5b6673; --line:#e3e7ec; --accent:#1f5eff; --tag:#eef2ff; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); }
  header { background:#101828; color:#fff; padding:18px 28px; }
  header h1 { margin:0 0 4px; font-size:19px; font-weight:600; }
  header .sub { color:#9aa4b2; font-size:12.5px; }
  .stats { display:flex; gap:14px; flex-wrap:wrap; padding:16px 28px 0; }
  .stat { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 18px; min-width:120px; }
  .stat .n { font-size:24px; font-weight:700; color:var(--accent); }
  .stat .t { font-size:12px; color:var(--muted); margin-top:2px; }
  nav { display:flex; gap:8px; padding:16px 28px 0; flex-wrap:wrap; }
  nav button { border:1px solid var(--line); background:var(--panel); border-radius:8px; padding:8px 16px; font-size:13.5px; cursor:pointer; color:var(--ink); }
  nav button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  .toolbar { padding:14px 28px 0; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .toolbar input[type=search] { flex:1; min-width:220px; padding:9px 12px; border:1px solid var(--line); border-radius:8px; font-size:13.5px; }
  .toolbar select, .toolbar label { font-size:13px; color:var(--muted); }
  .toolbar select { padding:8px; border:1px solid var(--line); border-radius:8px; }
  main { padding:16px 28px 40px; }
  .group { margin-bottom:22px; }
  .group h2 { font-size:15px; margin:0 0 8px; color:var(--muted); font-weight:600; }
  table { width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); border-radius:10px; overflow:hidden; font-size:13px; }
  th, td { text-align:left; padding:8px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { background:#f0f2f5; font-size:12px; color:var(--muted); font-weight:600; position:sticky; top:0; }
  tr:last-child td { border-bottom:none; }
  tr.cardrow { cursor:pointer; }
  tr.cardrow:hover td { background:#f7f9ff; }
  code { background:var(--tag); padding:1px 6px; border-radius:5px; font-size:12px; }
  .pill { display:inline-block; font-size:11px; padding:1px 8px; border-radius:99px; background:var(--tag); color:var(--accent); margin-right:4px; }
  .pill.warn { background:#fff3e0; color:#b25e09; }
  .detail { background:#fbfcfe; border:1px dashed var(--line); border-radius:8px; padding:12px 16px; font-size:13px; line-height:1.75; }
  .detail b { color:var(--ink); }
  .muted { color:var(--muted); }
  .gap { background:#fff8e6; border:1px solid #f0dfa8; border-radius:10px; padding:12px 16px; font-size:13px; margin-bottom:16px; }
  footer { padding:0 28px 30px; color:var(--muted); font-size:12px; }
</style>
</head>
<body>
<header>
  <h1>FLOW 字典浏览器 <span style="font-weight:400;color:#9aa4b2">v0 草案</span></h1>
  <div class="sub">财务分析指标库 · 会计基础数据（准则 / 科目 / 分录模板） — 由 YAML 数据集机械生成 · 生成时间 <span id="gen"></span></div>
</header>
<div class="stats" id="stats"></div>
<nav id="tabs"></nav>
<div class="toolbar">
  <input type="search" id="q" placeholder="搜索：指标名 / 编码 / 公式 / 科目名 / 场景…">
  <span id="facet"></span>
</div>
<main id="view"></main>
<footer>数据来源：指标库初始数据集 v0 · 会计基础数据集 v0（docs/knowledge-base/02_research/synthesis/）。本页面随数据集每次演进重建。</footer>
<script>
const DATA = __DATA__;
document.getElementById('gen').textContent = DATA.generated_at;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const TB = {period_flow:'期间流量', point_balance:'时点余额', average_balance:'平均余额'};

const state = { tab:'metrics', q:'', domain:'', mpm:'' };
const tabs = [ ['metrics','指标库'], ['logistics','物流行业指标集'], ['accounts','会计科目'], ['entries','分录模板'], ['relations','勾稽关系'], ['standards','准则登记册'] ];

function renderStats(){
  const mpm = [...DATA.metrics_general, ...DATA.metrics_logistics].filter(m=>m.mpm).length;
  const items = [ [DATA.metrics_general.length,'通用指标'], [DATA.metrics_logistics.length,'物流指标'], [DATA.accounts.length,'会计科目'], [DATA.entry_templates.length,'分录模板'], [DATA.relations.length,'勾稽关系'], [Object.keys(DATA.report_items).length,'报表项目对照'], [mpm,'MPM 指标'] ];
  document.getElementById('stats').innerHTML = items.map(([n,t])=>`<div class="stat"><div class="n">${n}</div><div class="t">${t}</div></div>`).join('');
}

function renderTabs(){
  document.getElementById('tabs').innerHTML = tabs.map(([k,t])=>`<button class="${state.tab===k?'active':''}" data-tab="${k}">${t}</button>`).join('');
  document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{state.tab=b.dataset.tab; state.q=''; document.getElementById('q').value=''; renderAll();});
}

function metricRow(m, set){
  return `<tr class="cardrow" data-id="${set}:${m.metric_code}"><td><code>${esc(m.metric_code)}</code></td><td><b>${esc(m.name)}</b>${m.mpm?' <span class="pill warn">MPM</span>':''}</td><td>${esc(m.formula_text||'')}</td><td>${esc(m.unit||'')}</td><td>${TB[m.time_behavior]||esc(m.time_behavior||'')}</td><td class="muted">${(m.depends_on||[]).map(d=>`<code>${esc(d)}</code>`).join(' ')||'—'}</td></tr>`;
}
function metricDetail(m){
  return `<tr><td colspan="6"><div class="detail">
    <b>定义</b>：${esc(m.definition||'—')}<br>
    <b>口径</b>：${esc(m.caliber||'—')}<br>
    ${m.decompositions?'<b>分解</b>：'+m.decompositions.map(d=>esc(d.name)+'：'+esc(d.formula_text)).join('；')+'<br>':''}
    <b>基准</b>：${esc(m.benchmark||'—')}<br>
    <b>CAS 取数</b>：${(m.source_cas||[]).map(esc).join('、')||'—'}<br>
    <b>IFRS 对照</b>：${esc(m.source_ifrs||'—')}<br>
    ${m.reconciliation?'<b>调节关系</b>：'+esc(m.reconciliation)+'<br>':''}
    ${m.migrates_from?'<b>迁移来源</b>：<code>'+esc(m.migrates_from)+'</code><br>':''}
    <b>来源</b>：${esc(m.provenance||'—')}
  </div></td></tr>`;
}
function renderMetrics(list, set){
  let ms = list;
  if (state.domain) ms = ms.filter(m=>m.domain===state.domain);
  if (state.mpm) ms = ms.filter(m=>String(!!m.mpm)===state.mpm);
  if (state.q) ms = ms.filter(m=>JSON.stringify(m).toLowerCase().includes(state.q));
  const groups = {};
  ms.forEach(m=>{(groups[m.domain] ||= []).push(m);});
  let html = '';
  for (const [dom, rows] of Object.entries(groups)){
    html += `<div class="group"><h2>${esc(DATA.domains[dom]||dom)}（${rows.length}）</h2><table>
      <tr><th style="width:14%">编码</th><th style="width:16%">指标</th><th>公式</th><th style="width:7%">单位</th><th style="width:10%">时间行为</th><th style="width:16%">依赖</th></tr>
      ${rows.map(m=>metricRow(m,set)).join('')}</table></div>`;
  }
  return html || '<p class="muted">无匹配结果</p>';
}
function renderAccounts(){
  let as = DATA.accounts;
  if (state.q) as = as.filter(a=>(a.code+a.name+a.category).toLowerCase().includes(state.q));
  const groups = {};
  as.forEach(a=>{(groups[a.category] ||= []).push(a);});
  let html = '';
  for (const [cat, rows] of Object.entries(groups)){
    html += `<div class="group"><h2>${esc(cat)}类（${rows.length}）</h2><table>
      <tr><th style="width:10%">编号</th><th>科目名称</th><th style="width:14%">余额方向</th><th style="width:14%">状态</th><th style="width:30%">准则出处 / 备注</th></tr>
      ${rows.map(a=>`<tr><td><code>${esc(a.code)}</code></td><td>${esc(a.name)}</td><td>${esc(a.balance_side)}</td><td>${a.status==='added_2024'?'<span class="pill warn">2024 新增</span>':'<span class="pill">现行</span>'}</td><td class="muted">${esc(a.standard_ref||'')}${a.code_note?'；'+esc(a.code_note):''}</td></tr>`).join('')}</table></div>`;
  }
  return html || '<p class="muted">无匹配结果</p>';
}
function renderEntries(){
  let es = DATA.entry_templates;
  if (state.q) es = es.filter(e=>JSON.stringify(e).toLowerCase().includes(state.q));
  return es.map(e=>`<div class="group"><h2>${esc(e.template_id)} · ${esc(e.scenario)}</h2><table>
    <tr><th style="width:8%">方向</th><th style="width:34%">科目</th><th>金额来源规则</th></tr>
    ${e.lines.map(l=>`<tr><td><b>${esc(l.direction)}</b></td><td>${esc(l.account)}</td><td class="muted">${esc(l.amount_rule)}</td></tr>`).join('')}
  </table>
  <div class="detail" style="margin-top:6px"><b>准则依据</b>：${esc(e.standard_ref||'—')}　<b>关联指标</b>：${(e.related_metrics||[]).map(m=>`<code>${esc(m)}</code>`).join(' ')||'—'}${e.note?'<br><b>备注</b>：'+esc(e.note):''}</div></div>`).join('') || '<p class="muted">无匹配结果</p>';
}
function renderRelations(){
  return `<table><tr><th style="width:22%">关系</th><th style="width:34%">表达式</th><th>说明</th></tr>
  ${DATA.relations.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td><code>${esc(r.expression)}</code></td><td class="muted">${esc(r.note)}<br>来源：${esc(r.provenance||'')}</td></tr>`).join('')}</table>`;
}
function renderStandards(){
  let html = `<table><tr><th style="width:18%">编号</th><th>名称</th><th style="width:12%">发布方</th><th style="width:40%">说明</th></tr>
  ${DATA.standards.map(s=>`<tr><td><code>${esc(s.id)}</code></td><td>${esc(s.name)}</td><td>${esc(s.issuer||'')}</td><td class="muted">${esc(s.note||'')}</td></tr>`).join('')}</table>`;
  if (DATA.known_gaps.length){
    html = `<div class="gap"><b>已知缺口（诚实记录）</b><br>${DATA.known_gaps.map(g=>'· '+esc(g)).join('<br>')}</div>` + html;
  }
  return html;
}

function renderFacet(){
  const f = document.getElementById('facet');
  if (state.tab==='metrics'){
    const doms = [...new Set(DATA.metrics_general.map(m=>m.domain))];
    f.innerHTML = `<select id="fdomain"><option value="">全部能力域</option>${doms.map(d=>`<option ${state.domain===d?'selected':''} value="${d}">${DATA.domains[d]||d}</option>`).join('')}</select>
    <select id="fmpm"><option value="">全部口径</option><option value="false" ${state.mpm==='false'?'selected':''}>法定/通用口径</option><option value="true" ${state.mpm==='true'?'selected':''}>仅 MPM</option></select>`;
    document.getElementById('fdomain').onchange = e=>{state.domain=e.target.value; renderView();};
    document.getElementById('fmpm').onchange = e=>{state.mpm=e.target.value; renderView();};
  } else f.innerHTML = '';
}
function renderView(){
  const v = document.getElementById('view');
  if (state.tab==='metrics') v.innerHTML = renderMetrics(DATA.metrics_general,'g');
  else if (state.tab==='logistics') v.innerHTML = renderMetrics(DATA.metrics_logistics,'l');
  else if (state.tab==='accounts') v.innerHTML = renderAccounts();
  else if (state.tab==='entries') v.innerHTML = renderEntries();
  else if (state.tab==='relations') v.innerHTML = renderRelations();
  else if (state.tab==='standards') v.innerHTML = renderStandards();
  // 卡片展开
  v.querySelectorAll('tr.cardrow').forEach(tr=>{
    tr.onclick = ()=>{
      const [set, code] = tr.dataset.id.split(':');
      const list = set==='g'?DATA.metrics_general:DATA.metrics_logistics;
      const m = list.find(x=>x.metric_code===code);
      const next = tr.nextElementSibling;
      if (next && next.classList.contains('detailrow')){ next.remove(); return; }
      const dtr = document.createElement('tr'); dtr.className='detailrow';
      dtr.innerHTML = metricDetail(m);
      tr.after(dtr);
    };
  });
}
function renderAll(){ renderStats(); renderTabs(); renderFacet(); renderView(); }
document.getElementById('q').oninput = e=>{ state.q = e.target.value.trim().toLowerCase(); renderView(); };
renderAll();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
