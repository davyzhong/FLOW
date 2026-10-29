// README「导入→发布→驾驶舱切换」完整流程截图（真实 UI 操作）。
// 用法：node capture-import-flow.mjs <输出目录> <样例账套绝对路径>
import { mkdirSync } from "node:fs";
import { chromium } from "@playwright/test";

const outDir = process.argv[2];
const ledger = process.argv[3];
if (!outDir || !ledger) {
  console.error("usage: node capture-import-flow.mjs <outdir> <ledger.xlsx>");
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });

const base = "http://localhost:3000";
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(`${base}/data/import`, { waitUntil: "networkidle" });

  await page.setInputFiles('input[type="file"]', ledger);
  await page.fill('input[placeholder*="2025"]', "2025 年样例账套");
  await page.click('button:has-text("校验并导入")');
  await page.waitForSelector("text=导入成功", { timeout: 30000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${outDir}/data-import--uploaded.png`, fullPage: true });
  console.log("uploaded state captured");

  await page.click('button:has-text("发布到驾驶舱")');
  await page.waitForSelector("text=已发布到治理链", { timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${outDir}/data-import--published.png`, fullPage: true });
  console.log("published state captured");

  await page.click('a:has-text("前往驾驶舱查看")');
  await page.waitForURL((url) => url.pathname === "/cockpit", { timeout: 30000 });
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${outDir}/cockpit-imported--desktop.png`, fullPage: true });
  console.log("imported cockpit captured");
} finally {
  await browser.close();
}
