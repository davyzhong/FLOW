#!/usr/bin/env node
/** 生成九重点页的本机静态交付包；页面/API 只从指定候选服务采集。 */

import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(root, "apps/web/package.json"));
const { chromium } = require("playwright");
const pages = [
  ["cockpit", "集团财务总览", "/cockpit"],
  ["profitability", "盈利能力与杜邦分析", "/cockpit/profitability"],
  ["balance-sheet", "资产负债", "/cockpit/balance-sheet"],
  ["working-capital", "营运资金", "/cockpit/working-capital"],
  ["expenses", "费用分析", "/cockpit/expenses"],
  ["cashflow", "现金流", "/cockpit/cashflow"],
  ["risk", "财务风险", "/cockpit/risk"],
  ["consolidation", "分部趋势", "/cockpit/consolidation"],
  ["data", "数据工作台", "/data"],
];

function args(argv) {
  const result = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!["--url", "--output"].includes(argv[i]) || !argv[i + 1]) throw new Error("用法：node scripts/export_cockpit_closeout_bundle.mjs --url URL --output NEW_DIRECTORY");
    result[argv[i].slice(2)] = argv[i + 1]; i += 1;
  }
  if (!result.url || !result.output) throw new Error("必须提供 --url 与 --output");
  return result;
}

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

async function main() {
  const options = args(process.argv.slice(2));
  const output = path.resolve(root, options.output);
  await mkdir(output, { recursive: false });
  const imageDir = path.join(output, "images");
  await mkdir(imageDir);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  const externalRequests = [];
  const apiResponses = new Map();
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("request", (request) => { if (new URL(request.url()).origin !== new URL(options.url).origin) externalRequests.push(request.url()); });
  page.on("response", async (response) => {
    if (!response.url().includes("/api/v1/")) return;
    try { apiResponses.set(new URL(response.url()).pathname + new URL(response.url()).search, await response.json()); } catch { /* 非 JSON 响应保留在页面验收结果 */ }
  });
  const captures = [];
  try {
    for (const [id, title, route] of pages) {
      for (const [viewport, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844]]) {
        await page.setViewportSize({ width, height });
        const before = new Set(apiResponses.keys());
        await page.goto(new URL(route, options.url).toString(), { waitUntil: "networkidle", timeout: 45_000 });
        await page.locator("main, [role=main], body").first().waitFor({ state: "visible" });
        await page.waitForTimeout(300);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
        const filename = `${id}-${viewport}.png`;
        const bytes = await page.screenshot({ path: path.join(imageDir, filename), fullPage: true, animations: "disabled" });
        const seen = [...apiResponses.keys()].filter((key) => !before.has(key));
        captures.push({ id, title, route, viewport, width, height, image: `images/${filename}`, sha256: sha(bytes), bytes: bytes.length, horizontal_overflow: overflow, api_routes: seen });
      }
    }
    const manifestBytes = await readFile(path.join(root, "data/enterprise/damai-logistics/v2/manifest.json"));
    const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
    const overview = [...apiResponses.entries()].find(([route]) => route.startsWith("/api/v1/cockpit/overview"))?.[1];
    const dataPayload = Object.fromEntries(apiResponses);
    const dataBytes = Buffer.from(JSON.stringify(dataPayload, null, 2));
    await writeFile(path.join(output, "api-responses.json"), dataBytes);
    const manifest = {
      format: "flow-cockpit-closeout-bundle/v1", candidate_sha: commit,
      data_package_manifest_sha256: sha(manifestBytes), batch_id: overview?.context?.batch_id ?? null,
      metric_snapshot_id: overview?.context?.metric_snapshot_id ?? null,
      created_at_utc: new Date().toISOString(), pages: captures,
      api_responses_sha256: sha(dataBytes), browser_errors: errors,
      external_requests: externalRequests,
      limits: ["静态图像/页面与 API 响应可离线查看；筛选、点击、编辑和报告生成需启动 FLOW。", "数据属于大麦 synthetic 演示，不是企业真实月度数据或公开 C 级证明。"],
    };
    await writeFile(path.join(output, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    const desktopCards = captures.filter((item) => item.viewport === "desktop").map((item) => {
      const mobile = captures.find((candidate) => candidate.id === item.id && candidate.viewport === "mobile");
      return `<article id="${escapeHtml(item.id)}"><h2>${escapeHtml(item.title)}</h2><nav><a href="#${escapeHtml(item.id)}">本页</a> · <a href="${escapeHtml(mobile.image)}">查看手机截图（${mobile.width}px）</a> · <a href="api-responses.json">固化 API 数据</a></nav><img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)} 实际页面截图"><p>${escapeHtml(item.width)}px 桌面图 · ${item.horizontal_overflow ? "检测到横向溢出" : "无横向溢出"}</p></article>`;
    }).join("\n");
    const toc = pages.map(([id, title]) => `<li><a href="#${escapeHtml(id)}">${escapeHtml(title)}</a></li>`).join("");
    const indexHtml = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FLOW 单机原型九页离线包</title><style>body{margin:0 auto;padding:24px;max-width:1440px;background:#f5f2eb;color:#173247;font:16px/1.6 system-ui,sans-serif}h1,h2{font-family:Georgia,"Songti SC",serif}article{margin:24px 0;padding:18px;background:white;border:1px solid #e2ddd2;border-radius:12px}img{display:block;width:100%;height:auto}a{color:#173f64}small,p{color:#647789}</style><h1>FLOW 单机原型 · 九页离线展示</h1><p>候选 ${escapeHtml(commit)} · 演示批次 ${escapeHtml(manifest.batch_id ?? "未返回")} · 数据发行清单 SHA-256 ${sha(manifestBytes)}</p><p>只读展示；交互需本机运行 FLOW。事实边界和完整指纹见 <a href="manifest.json">manifest</a>。</p><nav aria-label="静态页面目录"><ol>${toc}</ol></nav>${desktopCards}<footer><a href="api-responses.json">查看冻结 API 响应</a> · <a href="manifest.json">查看采集清单</a></footer></html>`;
    await writeFile(path.join(output, "index.html"), indexHtml, "utf8");
    const offlinePage = await browser.newPage();
    const offlineErrors = [];
    const offlineNetworkRequests = [];
    offlinePage.on("pageerror", (error) => offlineErrors.push(error.message));
    offlinePage.on("request", (request) => { if (/^https?:/i.test(request.url())) offlineNetworkRequests.push(request.url()); });
    await offlinePage.goto(new URL(`file://${path.join(output, "index.html")}`).toString(), { waitUntil: "load" });
    const offlineImages = await offlinePage.locator("img").evaluateAll((images) => images.map((image) => ({ loaded: image.complete && image.naturalWidth > 0, src: image.getAttribute("src") })));
    const staticLinks = await offlinePage.locator("a").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
    manifest.offline = {
      external_requests: offlineNetworkRequests,
      browser_errors: offlineErrors,
      images_total: offlineImages.length,
      images_loaded: offlineImages.filter((image) => image.loaded).length,
      broken_static_links: staticLinks.filter((href) => !href || href.startsWith("http:") || href.startsWith("https:")),
    };
    await offlinePage.close();
    await writeFile(path.join(output, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    console.log(`九页离线包：${path.relative(root, output)}`);
    console.log(`代码 SHA：${commit}；数据批次：${manifest.batch_id ?? "未返回"}；页面：${captures.length} 个视口`);
    console.log(`API 响应：${apiResponses.size}；外网请求：${externalRequests.length}；浏览器错误：${errors.length}；窄屏溢出：${captures.filter((item) => item.horizontal_overflow).length}`);
    if (externalRequests.length || errors.length || captures.some((item) => item.horizontal_overflow)
      || manifest.offline.external_requests.length || manifest.offline.browser_errors.length
      || manifest.offline.images_loaded !== manifest.offline.images_total || manifest.offline.broken_static_links.length) process.exitCode = 1;
  } finally { await browser.close(); }
}

main().catch((error) => { console.error(error instanceof Error ? error.stack : error); process.exitCode = 1; });
