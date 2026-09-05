#!/usr/bin/env python3
"""生成「指标库 v0 评审台」自包含 HTML 原型。

数据源（单一事实源，均为知识库 v0 草案数据集）：
- docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml（指标/映射/关系）
- docs/knowledge-base/02_research/synthesis/会计基础数据集_v0_草案.yaml（科目/准则/分录）
补充参考（内嵌）：42 项具体准则清单（知识库调研 07/10 号资料）。
输出：docs/knowledge-base/03_assets/visual_prototypes/metric-library-v0-review.html
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "docs/knowledge-base/02_research/synthesis"
DATA_YAML = SYN / "指标库初始数据集_v0_草案.yaml"
ACC_YAML = SYN / "会计基础数据集_v0_草案.yaml"
OUT = ROOT / "docs/knowledge-base/03_assets/visual_prototypes/metric-library-v0-review.html"

data = yaml.safe_load(DATA_YAML.read_text(encoding="utf-8"))
acc = yaml.safe_load(ACC_YAML.read_text(encoding="utf-8"))

# 42 项具体准则清单（调研 07 号资料；实施期以财政部原文核验版本状态）
SPECIFIC_42 = [
    ["CAS 1", "存货", ""], ["CAS 2", "长期股权投资", "2014 修订"], ["CAS 3", "投资性房地产", ""],
    ["CAS 4", "固定资产", ""], ["CAS 5", "生物资产", ""], ["CAS 6", "无形资产", ""],
    ["CAS 7", "非货币性资产交换", "2019 修订"], ["CAS 8", "资产减值", ""], ["CAS 9", "职工薪酬", "2014 修订"],
    ["CAS 10", "企业年金基金", ""], ["CAS 11", "股份支付", ""], ["CAS 12", "债务重组", "2019 修订"],
    ["CAS 13", "或有事项", ""], ["CAS 14", "收入", "2017 修订（新收入）"], ["CAS 15", "建造合同", "已并入 CAS 14"],
    ["CAS 16", "政府补助", "2017 修订"], ["CAS 17", "借款费用", ""], ["CAS 18", "所得税", ""],
    ["CAS 19", "外币折算", ""], ["CAS 20", "企业合并", ""], ["CAS 21", "租赁", "2018 修订（新租赁）"],
    ["CAS 22", "金融工具确认和计量", "2017 修订"], ["CAS 23", "金融资产转移", "2017 修订"],
    ["CAS 24", "套期会计", "2017 修订"], ["CAS 25", "保险合同", "2020 全面修订"],
    ["CAS 26", "再保险合同", ""], ["CAS 27", "石油天然气开采", ""],
    ["CAS 28", "会计政策、会计估计变更和差错更正", ""], ["CAS 29", "资产负债表日后事项", ""],
    ["CAS 30", "财务报表列报", "2014 修订"], ["CAS 31", "现金流量表", ""], ["CAS 32", "中期财务报告", ""],
    ["CAS 33", "合并财务报表", "2014 修订"], ["CAS 34", "每股收益", ""], ["CAS 35", "分部报告", ""],
    ["CAS 36", "关联方披露", ""], ["CAS 37", "金融工具列报", "2017 修订"],
    ["CAS 38", "首次执行企业会计准则", ""], ["CAS 39", "公允价值计量", "2014 新增"],
    ["CAS 40", "合营安排", "2014 新增"], ["CAS 41", "在其他主体中权益的披露", "2014 新增"],
    ["CAS 42", "持有待售的非流动资产、处置组和终止经营", "2017 新增"],
]

DOMAIN_META = {
    "solvency": {"label": "偿债能力", "color": "#2563eb"},
    "operation": {"label": "营运能力", "color": "#0d9488"},
    "profitability": {"label": "盈利能力", "color": "#16a34a"},
    "growth": {"label": "发展能力", "color": "#ea580c"},
    "cashflow": {"label": "现金流", "color": "#7c3aed"},
    "scale": {"label": "规模（物流专用）", "color": "#475569"},
}

payload = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "dictionary_id": data["dictionary_id"],
    "accounting_id": acc["dataset_id"],
    "accounting_gaps": acc.get("known_gaps", []),
    "domains": data["domains"],
    "domain_meta": DOMAIN_META,
    "report_items": data["report_items"],
    "metrics_general": data["metrics_general"],
    "metrics_logistics": data["metrics_logistics"],
    "relations": data["relations"],
    "standards_register": acc.get("standards", []),
    "standards_specific42": SPECIFIC_42,
    "accounts": acc["accounts"],
    "entry_templates": acc.get("entry_templates", []),
}

payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FLOW 指标库 v0 评审台</title>
<style>
:root{--ink:#1e293b;--sub:#64748b;--line:#e2e8f0;--bg:#f6f8fb;--card:#fff;--blue:#2563eb}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);font-size:14px;line-height:1.55}
header{background:#0f172a;color:#fff;padding:18px 28px;display:flex;flex-wrap:wrap;gap:14px;align-items:baseline}
header h1{font-size:19px;font-weight:600}
header .meta{color:#94a3b8;font-size:12.5px}
header .spacer{flex:1}
.tabs{display:flex;gap:4px;padding:10px 28px 0;background:#0f172a;flex-wrap:wrap}
.tabs button{border:0;background:#1e293b;color:#cbd5e1;padding:8px 16px;border-radius:8px 8px 0 0;cursor:pointer;font-size:13.5px}
.tabs button.active{background:var(--bg);color:var(--ink);font-weight:600}
main{padding:20px 28px 120px;max-width:1280px;margin:0 auto}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 18px;min-width:130px}
.stat b{font-size:22px;display:block}
.stat span{color:var(--sub);font-size:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px}
.card h3{font-size:15px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.code{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--sub)}
.chip{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:99px;background:#f1f5f9;color:#475569;border:1px solid var(--line)}
.chip.domain{color:#fff;border:0}
.chip.mpm{background:#fef3c7;color:#92400e;border-color:#fde68a}
.chip.add24{background:#dcfce7;color:#166534;border-color:#bbf7d0}
.chip.sups{background:#fee2e2;color:#991b1b;border-color:#fecaca}
.formula{font-family:ui-monospace,Menlo,monospace;background:#f8fafc;border:1px dashed var(--line);border-radius:8px;padding:8px 12px;margin:8px 0;font-size:13px}
.detail{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:6px 18px;margin-top:8px;font-size:12.8px;color:#334155}
.detail .k{color:var(--sub);margin-right:4px}
.dep{font-family:ui-monospace,monospace;font-size:12px;background:#eef2ff;color:#3730a3;padding:1px 7px;border-radius:6px;margin-right:4px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-top:10px}
.seg button{border:0;background:#fff;padding:5px 13px;cursor:pointer;font-size:12.5px;color:var(--sub)}
.seg button.on{color:#fff}
.seg .in.on{background:#16a34a}.seg .maybe.on{background:#d97706}.seg .out.on{background:#94a3b8}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
.filters input{padding:8px 12px;border:1px solid var(--line);border-radius:8px;font-size:13.5px;min-width:220px}
.fchip{padding:6px 13px;border:1px solid var(--line);border-radius:99px;background:#fff;cursor:pointer;font-size:12.8px;color:var(--sub)}
.fchip.active{border-color:var(--blue);color:var(--blue);background:#eff6ff}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}
.tablewrap{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:auto;max-height:640px}
.tablewrap table{border:0;border-radius:0}
th{background:#f1f5f9;text-align:left;padding:9px 12px;font-weight:600;border-bottom:1px solid var(--line);position:sticky;top:0}
td{padding:8px 12px;border-bottom:1px solid #f1f5f9;vertical-align:top}
.section-note{color:var(--sub);font-size:12.5px;margin:6px 0 14px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:900px){.two-col{grid-template-columns:1fr}}
.dock{position:fixed;left:0;right:0;bottom:0;background:#0f172a;color:#e2e8f0;padding:10px 28px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;box-shadow:0 -4px 16px rgba(15,23,42,.25)}
.dock .counts b{color:#4ade80}
.dock button{border:0;border-radius:8px;padding:8px 16px;cursor:pointer;font-size:13.5px}
.dock .copy{background:#2563eb;color:#fff}
.dock .reset{background:#334155;color:#cbd5e1}
.deptree{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;font-family:ui-monospace,monospace;font-size:13px;white-space:pre;overflow-x:auto}
.hide{display:none!important}
.legend{font-size:12px;color:var(--sub);margin:4px 0 14px}
h2{font-size:16.5px;margin:4px 0 10px}
</style>
</head>
<body>
<header>
  <h1>FLOW 指标库 v0 评审台</h1>
  <span class="meta" id="dicid"></span>
  <span class="spacer"></span>
  <span class="meta">依据 D040 · 数据源：指标库初始数据集_v0_草案.yaml + 会计基础数据集_v0_草案.yaml · 生成时间 <span id="genat"></span></span>
</header>
<div class="tabs" id="tabs">
  <button data-t="overview" class="active">总览</button>
  <button data-t="general">通用指标（40）</button>
  <button data-t="logistics">物流行业指标（15）</button>
  <button data-t="relations">勾稽与分解关系</button>
  <button data-t="mapping">报表项目映射 CAS↔IFRS</button>
  <button data-t="foundation">会计基础数据</button>
</div>
<main>
  <section id="page-overview" class="hide"></section>
  <section id="page-general" class="hide">
    <h2>通用财务指标 · 逐项判断</h2>
    <div class="section-note">对每个指标选择「纳入 / 待定 / 剔除」。卡片可看公式、口径要点、CAS/IFRS 取数与依赖。完成后点底部「复制筛选结果」发回对话。</div>
    <div class="filters"><input id="q-general" placeholder="搜索编码 / 名称 / 公式…"><span id="fchips-general" style="display:flex;gap:8px;flex-wrap:wrap"></span><label style="font-size:12.8px;color:var(--sub);display:flex;align-items:center;gap:4px"><input type="checkbox" id="mpm-general"> 仅看 MPM</label></div>
    <div id="list-general"></div>
  </section>
  <section id="page-logistics" class="hide">
    <h2>物流行业指标集 · 15 个（迁移自 flow.metrics.logistics.v1）</h2>
    <div class="section-note">该 15 个指标已在 V1 引擎落地并有已知答案门禁；此处的判断将决定它们迁移为库内「行业指标集版本」时的取舍。</div>
    <div class="filters"><input id="q-logistics" placeholder="搜索编码 / 名称 / 公式…"><label style="font-size:12.8px;color:var(--sub);display:flex;align-items:center;gap:4px"><input type="checkbox" id="mpm-logistics"> 仅看 MPM</label></div>
    <div id="list-logistics"></div>
  </section>
  <section id="page-relations" class="hide">
    <h2>勾稽与分解关系</h2>
    <div class="section-note">指标间不是孤立清单，而是依赖图。这些关系进入实施后将由确定性引擎按依赖序计算。</div>
    <div id="list-relations"></div>
    <div class="deptree" id="dupont-tree"></div>
  </section>
  <section id="page-mapping" class="hide">
    <h2>取数报表项目字典（CAS ↔ IFRS 对照）</h2>
    <div class="section-note">指标卡片的 source_cas / source_ifrs 引用此处项目；CAS 侧以财会〔2018〕15 号一般企业财务报表格式为底稿。</div>
    <div id="list-mapping"></div>
  </section>
  <section id="page-foundation" class="hide">
    <h2>会计基础数据（科目 / 准则 / 分录）</h2>
    <div class="section-note">数据源：<span class="code" id="accid"></span>。科目含余额方向与 2024 汇编新增标记；分录为模板样例并与指标关联（related_metrics）。已知缺口见页尾。</div>
    <h2 style="margin-top:14px;font-size:15px">会计科目（<span id="acc-count"></span>）</h2>
    <div class="filters">
      <input id="q-accounts" placeholder="搜索编号 / 名称…">
      <span id="fchips-acc" style="display:flex;gap:8px;flex-wrap:wrap"></span>
    </div>
    <div class="tablewrap" id="list-accounts"></div>
    <h2 style="margin-top:22px;font-size:15px">准则登记册与 42 项具体准则</h2>
    <div id="list-standards"></div>
    <h2 style="margin-top:22px;font-size:15px">典型分录模板（<span id="entry-count"></span>）</h2>
    <div class="section-note">规则出处：基本准则第十一条「企业应当采用借贷记账法记账」。related_metrics 表示该分录影响哪些指标取数——这是「基础数据 → 指标库」的使用链路。</div>
    <div id="list-entries"></div>
    <div class="card" style="margin-top:16px"><h3>已知缺口（诚实边界）</h3>
      <div class="detail" id="acc-gaps"></div></div>
  </section>
</main>
<div class="dock">
  <span class="counts" id="dock-counts"></span>
  <span class="spacer" style="flex:1"></span>
  <button class="reset" onclick="resetAll()">重置为全部纳入</button>
  <button class="copy" onclick="copyResult()">复制筛选结果</button>
</div>
<script>
const DATA = __DATA_JSON__;
const DM = DATA.domain_meta;
let sel = JSON.parse(localStorage.getItem("flow_metric_sel") || "{}");
let accCat = "all";
const get = c => sel[c] || "in";
const set = (c,v) => { sel[c]=v; localStorage.setItem("flow_metric_sel", JSON.stringify(sel)); render(); };
function resetAll(){ sel = {}; localStorage.removeItem("flow_metric_sel"); render(); }

function chip(domain){ const m=DM[domain]||{label:domain,color:"#64748b"};
  return `<span class="chip domain" style="background:${m.color}">${m.label}</span>`; }

function card(m, kind){
  const st = get(m.metric_code);
  const deps = (m.depends_on||[]).map(d=>`<span class="dep">← ${d}</span>`).join("") || '<span style="color:#94a3b8">无依赖（基础指标）</span>';
  const cas = Array.isArray(m.source_cas)? m.source_cas.join("；") : (m.source_cas||"—");
  return `<div class="card" data-code="${m.metric_code}" data-domain="${m.domain}">
    <h3>${m.name} <span class="code">${m.metric_code}</span> ${chip(m.domain)}
      ${m.mpm?'<span class="chip mpm">MPM 管理层口径</span>':""}
      <span class="chip">${m.unit}</span><span class="chip">${m.time_behavior}</span>
      ${kind==="logistics"?'<span class="chip">迁移自 v1</span>':""}</h3>
    <div class="formula">${m.formula_text||""}</div>
    <div class="detail">
      <div><span class="k">定义</span>${m.definition||"—"}</div>
      <div><span class="k">口径要点</span>${m.caliber||"—"}</div>
      <div><span class="k">CAS 取数</span>${cas}</div>
      <div><span class="k">IFRS 对照</span>${m.source_ifrs||"—"}</div>
      <div><span class="k">依赖</span><span>${deps}</span></div>
      <div><span class="k">来源</span>${m.provenance||"—"}</div>
    </div>
    <div class="seg">
      <button class="in ${st==='in'?'on':''}" onclick="set('${m.metric_code}','in')">纳入</button>
      <button class="maybe ${st==='maybe'?'on':''}" onclick="set('${m.metric_code}','maybe')">待定</button>
      <button class="out ${st==='out'?'on':''}" onclick="set('${m.metric_code}','out')">剔除</button>
    </div>
  </div>`;
}

function renderList(id, list, kind, qid, domainFilter){
  const q = (document.getElementById(qid)?.value||"").trim().toLowerCase();
  const mpmOnly = document.getElementById("mpm-"+kind)?.checked;
  const el = document.getElementById(id);
  const shown = list.filter(m=>{
    if(domainFilter && domainFilter!=="all" && m.domain!==domainFilter) return false;
    if(mpmOnly && !m.mpm) return false;
    if(!q) return true;
    return [m.metric_code,m.name,m.formula_text,m.definition,m.caliber].join(" ").toLowerCase().includes(q);
  });
  el.innerHTML = shown.length? shown.map(m=>card(m,kind)).join("") : '<div class="section-note">无匹配指标。</div>';
}

function renderFilters(){
  const wrap = document.getElementById("fchips-general");
  const domains = ["all", ...Object.keys(DM).filter(d=>DATA.metrics_general.some(m=>m.domain===d))];
  if(!wrap.dataset.built){
    wrap.innerHTML = domains.map(d=>`<button class="fchip${d==='all'?' active':''}" data-d="${d}">${d==='all'?'全部':DM[d].label}</button>`).join("");
    wrap.addEventListener("click",e=>{ const b=e.target.closest(".fchip"); if(!b)return;
      wrap.querySelectorAll(".fchip").forEach(x=>x.classList.remove("active")); b.classList.add("active");
      renderList("list-general",DATA.metrics_general,"general","q-general",b.dataset.d); });
    wrap.dataset.built = "1";
  }
}

function renderOverview(){
  const g=DATA.metrics_general,l=DATA.metrics_logistics;
  const byDomain={}; g.forEach(m=>byDomain[m.domain]=(byDomain[m.domain]||0)+1);
  const mpm=[...g,...l].filter(m=>m.mpm).length;
  const withDeps=[...g,...l].filter(m=>(m.depends_on||[]).length).length;
  const add24=DATA.accounts.filter(a=>a.status==="added_2024").length;
  document.getElementById("page-overview").innerHTML = `
    <h2>总览</h2>
    <div class="stats">
      <div class="stat"><b>${g.length}</b><span>通用财务指标</span></div>
      <div class="stat"><b>${l.length}</b><span>物流行业指标（迁移自 v1）</span></div>
      <div class="stat"><b>${Object.keys(DATA.report_items).length}</b><span>报表项目取数映射（CAS↔IFRS）</span></div>
      <div class="stat"><b>${DATA.relations.length}</b><span>勾稽 / 分解关系</span></div>
      <div class="stat"><b>${DATA.accounts.length}</b><span>会计科目（含 ${add24} 个 2024 新增）</span></div>
      <div class="stat"><b>${DATA.entry_templates.length}</b><span>分录模板（关联指标）</span></div>
      <div class="stat"><b>${mpm}</b><span>MPM 管理层口径指标</span></div>
      <div class="stat"><b>${withDeps}</b><span>含依赖边的指标</span></div>
    </div>
    <div class="legend">通用指标按能力域分布：</div>
    <div class="stats">${Object.entries(byDomain).map(([d,n])=>
      `<div class="stat"><b style="color:${DM[d].color}">${n}</b><span>${DM[d].label}</span></div>`).join("")}</div>
    <div class="card"><h3>设计要点（D040 已确认边界）</h3>
      <div class="detail">
        <div><span class="k">范围</span>会计基础数据做查阅级 + 取数映射，不做核算级总账</div>
        <div><span class="k">准则</span>CAS 为主，IFRS 概念级对照（MPM 等关键口径）</div>
        <div><span class="k">规模</span>通用 40 + 物流 15 起步，宁精勿滥</div>
        <div><span class="k">演进</span>建成后 flow.metrics.logistics.v1 迁移为库内行业指标集版本</div>
        <div><span class="k">变更</span>口径版本化：新版本 + 旧版本保留，不覆盖已发布快照</div>
        <div><span class="k">边界</span>AI 不创造数字；驾驶舱/报告/Copilot 只引用库内口径</div>
      </div></div>
    <div class="card"><h3>建议关注的三类筛选判断</h3>
      <div class="detail">
        <div>① 剔除当前用不到的指标——剔除不删除定义，仅标记不进入首批实施；</div>
        <div>② 口径分歧大的指标（卡片「口径要点」注明多口径并存）——可标记待定，进入正式规格时敲定默认口径；</div>
        <div>③ 物流 15 指标是否原样迁移——它们已有引擎实现与门禁，默认全部纳入。</div>
      </div></div>`;
}

function renderRelations(){
  document.getElementById("list-relations").innerHTML = DATA.relations.map(r=>`
    <div class="card"><h3>${r.name} <span class="code">${r.relation}</span></h3>
      <div class="formula">${r.expression}</div>
      <div class="detail"><div><span class="k">说明</span>${r.note}</div>
      <div><span class="k">来源</span>${r.provenance}</div></div></div>`).join("");
  document.getElementById("dupont-tree").textContent =
`ROE（净资产收益率）
├─ × 净利率（net_margin）        = 净利润 ÷ 营业收入
│    ├─ 毛利率（gross_margin）
│    ├─ 期间费用率（销售/管理/研发/财务费用率，后续版本）
│    └─ 税负（后续版本）
├─ × 总资产周转率（total_asset_turnover）= 营业收入 ÷ 平均总资产
│    ├─ 应收周转 / 存货周转 / 应付周转（ar / inventory / ap 族）
│    └─ 流动资产周转 / 固定资产周转
└─ × 权益乘数（equity_multiplier）= 平均总资产 ÷ 平均净资产
     └─ 与资产负债率（debt_asset_ratio）同向

管理用（改进杜邦）链：
ROE = 净经营资产净利率 + 杠杆贡献率
    净经营资产净利率 = 税后经营净利润 ÷ 净经营资产
    杠杆贡献率 = (净经营资产净利率 − 税后利息率) × 净财务杠杆
    ※ 经营差异率为正时杠杆才提升 ROE（重资产物流企业解释力强）`;
}

function renderMapping(){
  document.getElementById("list-mapping").innerHTML =
   `<table><thead><tr><th>编码</th><th>CAS 报表项目</th><th>IFRS 对照</th></tr></thead><tbody>` +
   Object.entries(DATA.report_items).map(([k,v])=>`<tr><td class="code">${k}</td><td>${v.cas}</td><td>${v.ifrs}</td></tr>`).join("") +
   `</tbody></table>`;
}

function renderAccounts(){
  const q=(document.getElementById("q-accounts")?.value||"").trim().toLowerCase();
  const list=DATA.accounts.filter(a=>{
    if(accCat!=="all"&&a.category!==accCat) return false;
    if(!q) return true;
    return (a.code+" "+a.name).toLowerCase().includes(q);
  });
  const cats=["all",...DATA.accounting_categories];
  document.getElementById("list-accounts").innerHTML =
   `<table><thead><tr><th>编号</th><th>名称</th><th>类别</th><th>余额方向</th><th>状态</th></tr></thead><tbody>` +
   (list.length? list.map(a=>`<tr>
      <td class="code">${a.code}</td><td>${a.name}</td><td>${a.category}</td>
      <td>${a.balance_side}</td>
      <td>${a.status==="added_2024"?'<span class="chip add24">2024 新增</span>':(a.status==="superseded"?'<span class="chip sups">已废止</span>':'现行')}</td>
    </tr>`).join("") : '<tr><td colspan="5" style="color:#94a3b8">无匹配科目。</td></tr>') +
   `</tbody></table>`;
}

function renderStandards(){
  document.getElementById("list-standards").innerHTML =
   `<div class="two-col">
     <div><div class="legend" style="font-weight:600;color:var(--ink)">准则登记册（${DATA.standards_register.length} 条，与本数据集直接相关）</div>
      <table><thead><tr><th>编号</th><th>名称</th><th>要点</th></tr></thead><tbody>` +
     DATA.standards_register.map(s=>`<tr><td class="code">${s.id}</td><td>${s.name}</td><td>${s.note||"—"}</td></tr>`).join("") +
     `</tbody></table></div>
     <div><div class="legend" style="font-weight:600;color:var(--ink)">42 项具体准则全清单</div>
      <div class="tablewrap" style="max-height:420px"><table><thead><tr><th>编号</th><th>名称</th><th>修订</th></tr></thead><tbody>` +
     DATA.standards_specific42.map(r=>`<tr><td class="code">${r[0]}</td><td>${r[1]}</td><td>${r[2]||"—"}</td></tr>`).join("") +
     `</tbody></table></div></div>
   </div>`;
}

function renderEntries(){
  document.getElementById("entry-count").textContent = DATA.entry_templates.length;
  document.getElementById("list-entries").innerHTML = DATA.entry_templates.map(e=>{
    const lines = (e.lines||[]).map(l=>`<div><b style="color:${l.direction==='借'?'#b45309':'#1d4ed8'}">${l.direction}</b>　${l.account}
      <span class="chip" style="margin-left:6px">${l.amount_rule||""}</span></div>`).join("");
    const rel = (e.related_metrics||[]).map(m=>`<span class="dep">${m}</span>`).join(" ");
    return `<div class="card"><h3>${e.scenario} <span class="code">${e.template_id}</span></h3>
      <div class="detail" style="margin-bottom:6px"><div><span class="k">业务背景</span>${e.business_context||"—"}</div>
      <div><span class="k">准则</span>${e.standard_ref||"—"}</div></div>
      <div style="font-size:13.2px">${lines}</div>
      <div style="margin-top:8px"><span class="k" style="color:var(--sub);font-size:12.8px">影响指标</span>${rel||"—"}</div>
    </div>`;}).join("");
}

function renderFoundation(){
  document.getElementById("accid").textContent = DATA.accounting_id;
  document.getElementById("acc-count").textContent = DATA.accounts.length + " 个科目";
  document.getElementById("acc-gaps").innerHTML = DATA.accounting_gaps.map(g=>`<div>${g}</div>`).join("");
  const wrap=document.getElementById("fchips-acc");
  if(!wrap.dataset.built){
    const cats=["all",...DATA.accounting_categories];
    wrap.innerHTML = cats.map(c=>`<button class="fchip${c==='all'?' active':''}" data-c="${c}">${c==='all'?'全部类别':c}</button>`).join("");
    wrap.addEventListener("click",e=>{ const b=e.target.closest(".fchip"); if(!b)return;
      wrap.querySelectorAll(".fchip").forEach(x=>x.classList.remove("active")); b.classList.add("active");
      accCat=b.dataset.c; renderAccounts(); });
    wrap.dataset.built="1";
  }
  renderAccounts(); renderStandards(); renderEntries();
}

function renderDock(){
  const all=[...DATA.metrics_general,...DATA.metrics_logistics];
  const n={in:0,maybe:0,out:0}; all.forEach(m=>n[get(m.metric_code)]++);
  document.getElementById("dock-counts").innerHTML =
    `已选：纳入 <b>${n.in}</b> · 待定 ${n.maybe} · 剔除 ${n.out}（共 ${all.length}）`;
}

function render(){
  renderOverview();
  renderList("list-general",DATA.metrics_general,"general","q-general",document.querySelector("#fchips-general .fchip.active")?.dataset.d||"all");
  renderList("list-logistics",DATA.metrics_logistics,"logistics","q-logistics",null);
  renderRelations(); renderMapping(); renderFoundation(); renderDock();
}

document.getElementById("tabs").addEventListener("click",e=>{
  const b=e.target.closest("button"); if(!b)return;
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.toggle("active",x===b));
  document.querySelectorAll("main section").forEach(s=>s.classList.add("hide"));
  document.getElementById("page-"+b.dataset.t).classList.remove("hide");
});
["q-general","q-logistics","q-accounts"].forEach(id=>document.getElementById(id).addEventListener("input",()=>{
  if(id==="q-accounts") renderAccounts();
  else if(id==="q-general") renderList("list-general",DATA.metrics_general,"general","q-general",document.querySelector("#fchips-general .fchip.active")?.dataset.d||"all");
  else renderList("list-logistics",DATA.metrics_logistics,"logistics","q-logistics",null);
}));
document.getElementById("dicid").textContent = DATA.dictionary_id + " · " + DATA.accounting_id;
document.getElementById("genat").textContent = DATA.generated_at;
["mpm-general","mpm-logistics"].forEach(id=>document.getElementById(id).addEventListener("change",()=>{
  if(id==="mpm-general") renderList("list-general",DATA.metrics_general,"general","q-general",document.querySelector("#fchips-general .fchip.active")?.dataset.d||"all");
  else renderList("list-logistics",DATA.metrics_logistics,"logistics","q-logistics",null);
}));
render();
function resultText(){
  const g={in:[],maybe:[],out:[]},l={in:[],maybe:[],out:[]};
  DATA.metrics_general.forEach(m=>g[get(m.metric_code)].push(m.metric_code));
  DATA.metrics_logistics.forEach(m=>l[get(m.metric_code)].push(m.metric_code));
  const j=(o)=>o.in.length+" 纳入 / "+o.maybe.length+" 待定 / "+o.out.length+" 剔除";
  const names=(arr,codes)=>codes.map(c=>{const m=arr.find(x=>x.metric_code===c);return c+"("+(m?m.name:"")+")";}).join("、");
  return "FLOW 指标库 v0 筛选结果\n"
    + "通用指标："+j(g)+(g.out.length?"\n  剔除："+names(DATA.metrics_general,g.out):"")
    + (g.maybe.length?"\n  待定："+names(DATA.metrics_general,g.maybe):"")
    + "\n物流指标："+j(l)+(l.out.length?"\n  剔除："+names(DATA.metrics_logistics,l.out):"")
    + (l.maybe.length?"\n  待定："+names(DATA.metrics_logistics,l.maybe):"")
    + "\n（未标记的默认为纳入）";
}
function copyResult(){
  const t=resultText();
  const done=()=>{ const b=document.querySelector(".dock .copy"); b.textContent="已复制，请回到对话粘贴"; setTimeout(()=>b.textContent="复制筛选结果",2500); };
  if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(t).then(done).catch(()=>fallback()); } else fallback();
  function fallback(){ const ta=document.createElement("textarea"); ta.value=t; document.body.appendChild(ta); ta.select();
    try{document.execCommand("copy");done();}catch(e){alert(t);} ta.remove(); }
}
</script>
</body>
</html>
"""

payload["accounting_categories"] = acc["categories"]
payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(TEMPLATE.replace("__DATA_JSON__", payload_json), encoding="utf-8")
print(f"已生成 {OUT}（{OUT.stat().st_size} bytes）")
