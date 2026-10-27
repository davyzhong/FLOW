import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs/promises";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const rootRequire = createRequire(path.join(repositoryRoot, "package.json"));
const webRequire = createRequire(path.join(repositoryRoot, "apps/web/package.json"));
const { chromium } = webRequire("playwright");
const AxeBuilder = rootRequire("@axe-core/playwright").default;
const baseUrl = process.env.FLOW_VISUAL_AUDIT_URL ?? "http://127.0.0.1:13100";
const matrixPath = path.join(repositoryRoot, "docs/60_delivery/verification/visual-language-20261024/results.json");
const outputPath = path.join(repositoryRoot, "docs/60_delivery/verification/visual-language-20261024/axe-results.json");
const matrix = JSON.parse(await fs.readFile(matrixPath, "utf8"));
const routes = [...new Set(matrix.results.map(({ route }) => route))];
const browser = await chromium.launch({ headless: true });
const results = [];

for (const route of routes) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(new URL(route, baseUrl).href, { waitUntil: "networkidle" });
  const audit = await new AxeBuilder({ page }).analyze();
  results.push({
    route,
    violations: audit.violations.map(({ id, impact, nodes }) => ({
      id,
      impact,
      count: nodes.length,
      targets: nodes.map(({ target }) => target),
    })),
  });
  await context.close();
}
await browser.close();

const report = {
  capturedAt: new Date().toISOString(),
  codeCommit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: repositoryRoot, encoding: "utf8" }).trim(),
  axePackage: "@axe-core/playwright 4.13.0",
  viewport: "1440x1000 desktop default state",
  routes: results.length,
  violations: results.reduce((total, route) => total + route.violations.reduce((sum, violation) => sum + violation.count, 0), 0),
  rules: [...new Set(results.flatMap((route) => route.violations.map(({ id }) => id)))],
  results,
};
await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ outputPath, routes: report.routes, violations: report.violations, codeCommit: report.codeCommit }));
