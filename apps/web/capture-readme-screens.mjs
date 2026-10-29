// README 最新界面截图采集（真实登录 + 生产构建页面全页截图）。
// 用法：FLOW_WEB_PASSWORD=<密码> node capture-readme-screens.mjs <输出目录>
// 视口：桌面 1440x1000（fullPage）；导入向导加一版移动 390。
// 等待：networkidle + 图表渲染余量，保证 ECharts 完成绘制。
import { mkdirSync } from "node:fs";
import { chromium } from "@playwright/test";

const outDir = process.argv[2];
const password = process.env.FLOW_WEB_PASSWORD;
if (!outDir || !password) {
  console.error("usage: FLOW_WEB_PASSWORD=... node capture-readme-screens.mjs <outdir>");
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });

const base = "http://localhost:3000";
const desktop = { width: 1440, height: 1000 };
const mobile = { width: 390, height: 844 };

const pages = [
  ["cockpit", "/cockpit", "desktop"],
  ["cockpit-profitability", "/cockpit/profitability", "desktop"],
  ["cockpit-balance-sheet", "/cockpit/balance-sheet", "desktop"],
  ["cockpit-working-capital", "/cockpit/working-capital", "desktop"],
  ["cockpit-expenses", "/cockpit/expenses", "desktop"],
  ["cockpit-cashflow", "/cockpit/cashflow", "desktop"],
  ["cockpit-risk", "/cockpit/risk", "desktop"],
  ["cockpit-consolidation", "/cockpit/consolidation", "desktop"],
  ["data-import", "/data/import", "desktop"],
  ["data-import", "/data/import", "mobile"],
  ["reports", "/reports", "desktop"],
];

const browser = await chromium.launch();
try {
  async function signIn(target) {
    await target.goto(`${base}/cockpit`, { waitUntil: "domcontentloaded" });
    if (!target.url().includes("/login")) {
      console.log("auth disabled, direct access");
      return;
    }
    await target.goto(`${base}/login`, { waitUntil: "networkidle" });
    await target.fill("#password", password);
    await target.click("button[type=submit]");
    await target.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 20000 });
    await target.waitForTimeout(1500);
    console.log("login ok");
  }

  const context = await browser.newContext({ viewport: desktop });
  const page = await context.newPage();
  await signIn(page);

  const mobileContext = await browser.newContext({ viewport: mobile });
  const mobilePage = await mobileContext.newPage();
  await signIn(mobilePage);

  let lastSlug = "";
  for (const [slug, path, viewport] of pages) {
    const target = viewport === "mobile" ? mobilePage : page;
    await target.goto(`${base}${path}`, { waitUntil: "networkidle" });
    await target.waitForTimeout(2500); // ECharts 动画与懒加载余量
    const suffix = viewport === "mobile" ? "mobile" : "desktop";
    const file = `${outDir}/${slug}--${suffix}.png`;
    await target.screenshot({ path: file, fullPage: true });
    if (slug !== lastSlug) console.log(`captured ${slug}`);
    lastSlug = slug;
  }
  console.log("done");
} finally {
  await browser.close();
}
