import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, readFile, writeFile } from "node:fs/promises";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(repositoryRoot, "apps/web/package.json"));
const { chromium } = require("playwright");
const sourceMatrixPath = path.join(repositoryRoot, "docs/60_delivery/verification/visual-language-20261024/results.json");
if (!process.env.FLOW_VISUAL_AUDIT_OUTPUT) {
  throw new Error("请设置 FLOW_VISUAL_AUDIT_OUTPUT 指向新的结果文件，避免覆盖历史验收截图");
}
const matrixPath = path.resolve(process.env.FLOW_VISUAL_AUDIT_OUTPUT);
const matrixDirectory = path.dirname(matrixPath);
const historicalDirectory = path.dirname(sourceMatrixPath);
if (matrixDirectory === historicalDirectory || matrixDirectory.startsWith(`${historicalDirectory}${path.sep}`)) {
  throw new Error("新结果目录不能位于 2026-10-24 历史验收目录内，避免覆盖截图");
}
const baseUrl = process.env.FLOW_VISUAL_AUDIT_URL ?? "http://127.0.0.1:13100";
const codeCommit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: repositoryRoot, encoding: "utf8" }).trim();
const viewportSpecs = {
  desktop: { width: 1440, height: 1000 },
  tablet: { width: 1024, height: 900 },
  mobile: { width: 390, height: 844 },
};
const matrix = JSON.parse(await readFile(sourceMatrixPath, "utf8"));
await mkdir(matrixDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];

try {
  for (const previous of matrix.results) {
    const viewport = viewportSpecs[previous.viewport];
    if (!viewport) throw new Error(`未知视口：${previous.viewport}`);
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    const apiErrors = [];
    const externalRequests = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("request", (request) => {
      if (new URL(request.url()).origin !== baseUrl) externalRequests.push(request.url());
    });
    page.on("response", (response) => {
      if (response.url().includes("/api/") && response.status() >= 400) {
        apiErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    let status = 0;
    try {
      const response = await page.goto(new URL(previous.route, baseUrl).toString(), { waitUntil: "networkidle", timeout: 30000 });
      status = response?.status() ?? 0;
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(250);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }

    const dimensions = await page.evaluate(() => ({
      doc: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
      body: document.body.scrollWidth,
      contentReady: Boolean(document.querySelector("h1, main, [data-status='ready']")) && document.body.innerText.trim().length > 0,
    }));
    const horizontalOverflow = dimensions.doc > viewport.width || dimensions.body > viewport.width;
    const result = {
      route: previous.route,
      viewport: previous.viewport,
      status,
      ...dimensions,
      errors,
      apiErrors,
      externalRequests: [...new Set(externalRequests)],
      horizontalOverflow,
      contentReady: status >= 200 && status < 300 && dimensions.contentReady,
      bad: status < 200 || status >= 300 || errors.length > 0 || apiErrors.length > 0 || externalRequests.length > 0 || horizontalOverflow,
      screenshot: previous.screenshot,
    };
    await page.screenshot({ path: path.join(matrixDirectory, result.screenshot), fullPage: true });
    results.push(result);
    await context.close();
    console.log(`${results.length}/${matrix.results.length} ${result.viewport} ${result.route} ${result.bad ? "FAIL" : "PASS"}`);
  }
} finally {
  await browser.close();
}

matrix.capturedAt = new Date().toISOString();
matrix.codeCommit = codeCommit;
matrix.baseUrl = baseUrl;
matrix.results = results;
matrix.summary = {
  total: results.length,
  contentReady: results.filter((result) => result.contentReady).length,
  bad: results.filter((result) => result.bad).length,
  apiErrors: results.reduce((count, result) => count + result.apiErrors.length, 0),
  browserErrors: results.reduce((count, result) => count + result.errors.length, 0),
  externalRequests: results.reduce((count, result) => count + result.externalRequests.length, 0),
  horizontalOverflow: results.filter((result) => result.horizontalOverflow).length,
};
await writeFile(matrixPath, `${JSON.stringify(matrix, null, 2)}\n`);
console.log(JSON.stringify(matrix.summary));
