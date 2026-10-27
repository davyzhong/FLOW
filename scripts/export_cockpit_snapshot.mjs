#!/usr/bin/env node

/**
 * 从正在运行的本机 FLOW 导出可离线浏览的 CFO 驾驶舱快照。
 *
 * 输出为单个 HTML：内嵌真实页面全页截图、驾驶舱 API 原始响应和来源指纹；
 * 不加载远程字体、脚本、样式、图片或接口。快照只读，筛选/下钻仍需运行应用。
 */

import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(root, "apps/web/package.json"));
const { chromium } = require("playwright");

function argumentsFrom(argv) {
  const values = { url: "http://127.0.0.1:3000", output: "docs/assets/screenshots/cockpit-single-machine/offline-preview.html" };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (key === "--url" || key === "--output") {
      const value = argv[index + 1];
      if (!value) throw new Error(`${key} 缺少参数值`);
      values[key.slice(2)] = value;
      index += 1;
    } else {
      throw new Error(`未知参数：${key}`);
    }
  }
  return values;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function formatKpi(card) {
  const exact = Number(card.primary?.exact_value);
  if (!Number.isFinite(exact)) return "暂无数据";
  if (card.unit === "CNY") return `${(exact / 100_000_000).toFixed(2)} 亿元`;
  if (card.unit === "ratio" || card.unit === "%") return `${(exact * 100).toFixed(2)}%`;
  if (card.unit === "order") return `${Math.round(exact).toLocaleString("zh-CN")} 单`;
  return `${exact.toLocaleString("zh-CN", { maximumFractionDigits: 2 })} ${escapeHtml(card.unit)}`;
}

async function fetchJson(page, route) {
  const result = await page.evaluate(async (apiRoute) => {
    const response = await fetch(apiRoute, { cache: "no-store" });
    const body = await response.json();
    if (!response.ok) throw new Error(`${apiRoute} 返回 HTTP ${response.status}`);
    return body;
  }, route);
  return result;
}

function renderHtml({ title, captureDate, commit, manifestSha, screenshot, payload, overview, tokens }) {
  const kpis = (overview.kpi_cards ?? []).map((card) => `
    <article class="kpi"><span>${escapeHtml(card.title)}</span><strong>${formatKpi(card)}</strong>
      <small>${escapeHtml(card.caliber_note ?? "")}</small></article>`).join("");
  const safeJson = JSON.stringify(payload, null, 2).replace(/</g, "\\u003c");
  const imageUri = `data:image/png;base64,${screenshot.toString("base64")}`;
  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="FLOW CFO 驾驶舱离线静态快照，含真实页面截图、API 数据和来源指纹。">
<title>${escapeHtml(title)}</title><style>
:root{color-scheme:light;--ink:${tokens.colors.text.primary};--navy:${tokens.colors.surface.nav};--paper:${tokens.colors.surface.canvas};--gold:${tokens.colors.brand.gold};--line:${tokens.colors.line.default};--muted:${tokens.colors.text.muted}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 ${tokens.typography.family.body}}
main{max-width:1320px;margin:0 auto;padding:32px 24px 64px}.masthead{display:flex;justify-content:space-between;gap:24px;align-items:end;border-bottom:1px solid var(--line);padding-bottom:22px}
.eyebrow{color:var(--gold);letter-spacing:.15em;font-size:12px;font-weight:700}.masthead h1{margin:5px 0 0;font-family:${tokens.typography.family.display};font-size:clamp(28px,5vw,48px);line-height:1.1}.meta{text-align:right;color:var(--muted);font-size:13px}
.notice{margin:20px 0;padding:13px 16px;border:1px solid ${tokens.colors.brand.gold};background:${tokens.colors.brand.goldSoft};border-radius:${tokens.radius.md};color:${tokens.colors.text.secondary};font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}.kpi{background:${tokens.colors.surface.paper};border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:${tokens.radius.md};padding:16px;min-height:118px}.kpi span{display:block;color:var(--muted);font-size:13px}.kpi strong{display:block;font:${tokens.typography.weight.bold} clamp(22px,3vw,34px)/1.25 ${tokens.typography.family.numeric};margin:6px 0}.kpi small{display:block;color:var(--muted);font-size:11px}
.figure{margin:18px 0;background:${tokens.colors.surface.paper};border:1px solid var(--line);border-radius:${tokens.radius.lg};padding:14px;box-shadow:${tokens.shadow.panel}}.figure img{display:block;width:100%;height:auto;border-radius:${tokens.radius.sm}}.figure figcaption{padding:10px 4px 0;color:var(--muted);font-size:13px}
details{margin-top:20px;background:${tokens.colors.surface.paper};border:1px solid var(--line);border-radius:${tokens.radius.md};padding:14px 18px}summary{cursor:pointer;font-weight:${tokens.typography.weight.bold}}pre{max-height:560px;overflow:auto;white-space:pre-wrap;word-break:break-word;background:${tokens.colors.surface.soft};padding:14px;border-radius:${tokens.radius.sm};font:12px/1.5 ${tokens.typography.family.mono}}
footer{margin-top:24px;color:var(--muted);font-size:12px}.tag{display:inline-block;margin:3px 6px 3px 0;padding:2px 8px;border:1px solid var(--line);border-radius:${tokens.radius.pill};background:${tokens.colors.surface.paper}}
@media(max-width:760px){main{padding:22px 14px 44px}.masthead{display:block}.meta{text-align:left;margin-top:12px}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.kpi{padding:12px}.figure{padding:7px}}
@media print{body{background:${tokens.colors.surface.paper}}.figure,.kpi{box-shadow:none;break-inside:avoid}details{display:none}}
</style></head><body><main>
<header class="masthead"><div><div class="eyebrow">FLOW / FINANCE INTELLIGENCE</div><h1>集团财务总览</h1></div>
<div class="meta">离线静态快照 · ${escapeHtml(captureDate)}<br>代码 ${escapeHtml(commit)} · 快照 ${escapeHtml(overview.context?.metric_snapshot_id ?? "未知")}</div></header>
<p class="notice">当前数据源为大麦物流合成演示数据。本页面为只读静态快照，不构成公开财报 C 级能力证明；筛选、下钻和确认操作需运行 FLOW。</p>
<section class="kpis" aria-label="关键财务指标">${kpis}</section>
<figure class="figure"><img src="${imageUri}" alt="${escapeHtml(title)}：真实 CFO 驾驶舱页面截图，含趋势图、现金流瀑布、杜邦拆解、费用结构、结论和行动项"><figcaption>页面图像从本机生产版路径 /cockpit 实际渲染；图中曲线、柱图和数值取自所列冻结快照。画布保持原始比例，便于离线查看与打印。</figcaption></figure>
<section aria-label="数据来源"><span class="tag">数据批次：${escapeHtml(overview.context?.batch_id ?? "未提供")}</span><span class="tag">期间：${escapeHtml(overview.context?.as_of_month ?? "未提供")}</span><span class="tag">指标集：${escapeHtml(overview.context?.metric_definition_set_id ?? "未提供")}</span><span class="tag">发行包 SHA-256：${escapeHtml(manifestSha)}</span></section>
<details><summary>查看随页固化的 API 原始数据（${Object.keys(payload).length} 个接口）</summary><pre>${escapeHtml(safeJson)}</pre></details>
<footer>本文件无远程依赖，可直接通过 file:// 打开。重新生成：<code>node scripts/export_cockpit_snapshot.mjs</code>。原始数据仅供追溯；如有口径差异，以 API 返回的指标定义、快照和来源记录为准。</footer>
</main></body></html>`;
}

async function main() {
  const args = argumentsFrom(process.argv.slice(2));
  const tokens = JSON.parse(await readFile(path.join(root, "packages/flow-visual-language/tokens.json"), "utf8"));
  const output = path.resolve(root, args.output);
  const outputDir = path.dirname(output);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  try {
    await page.goto(new URL("/cockpit", args.url).toString(), { waitUntil: "networkidle", timeout: 30_000 });
    await page.getByTestId("cockpit-overview-revenue-profit-chart").waitFor({ state: "visible", timeout: 30_000 });
    const [overview, profitability, cashflow, expenses, actionItems] = await Promise.all([
      fetchJson(page, "/api/v1/cockpit/overview"),
      fetchJson(page, "/api/v1/cockpit/profitability"),
      fetchJson(page, "/api/v1/cockpit/modules/cashflow"),
      fetchJson(page, "/api/v1/cockpit/modules/expenses"),
      fetchJson(page, "/api/v1/cockpit/action-items"),
    ]);
    if (!overview.source_notice?.includes("演示数据") || !overview.kpi_cards?.length) {
      throw new Error("当前 API 未返回完整且明确标注为演示数据的驾驶舱内容，拒绝生成快照");
    }
    const screenshot = await page.screenshot({ fullPage: true, animations: "disabled" });
    const manifestBytes = await readFile(path.join(root, "fixtures/damai/manifest.json"));
    const manifestSha = createHash("sha256").update(manifestBytes).digest("hex");
    const commit = execFileSync("git", ["rev-parse", "--short", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
    const payload = { overview, profitability, cashflow, expenses, action_items: actionItems };
    const title = "大麦物流集团财务驾驶舱静态快照";
    const captureDate = new Date().toISOString().slice(0, 10);
    await mkdir(outputDir, { recursive: true });
    await writeFile(output, renderHtml({ title, captureDate, commit, manifestSha, screenshot, payload, overview, tokens }), "utf8");
    const imagePath = output.replace(/\.html$/i, ".png");
    await writeFile(imagePath, screenshot);
    if (errors.length) throw new Error(`浏览器错误：${errors.join("；")}`);
    console.log(`离线快照：${path.relative(root, output)}`);
    console.log(`页面截图：${path.relative(root, imagePath)}`);
    console.log(`数据批次：${overview.context.batch_id}；财务 KPI：${overview.kpi_cards.length}；门禁数据源发行包 SHA-256：${manifestSha}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : error);
  process.exitCode = 1;
});
