// 截取 P5 图形化报告与指标库评审台的板块截图，供 README 与文档引用。
// 用法：node scripts/capture_p5_report_screenshots.mjs
// 输出：docs/assets/screenshots/p5/*.png（覆盖同名文件）
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outDir = path.join(root, 'docs/assets/screenshots/p5');

const VIEWPORT = { width: 1440, height: 1000 };

// sectionGroups: 以 h2 文本前缀界定 [from, to) 的纵向裁剪区间；to 为 null 表示到页面底部。
const pages = [
  {
    file: 'docs/implementation/p5/sf_2026q1_report_view.html',
    groups: [
      { name: 'sf-overview.png', from: '①', to: '④' },
      { name: 'sf-dupont.png', from: '⑤', to: '⑥' },
      { name: 'sf-structure.png', from: '⑥', to: '⑦' },
      { name: 'sf-peer.png', from: '⑦', to: '⑧' },
      { name: 'sf-cashflow.png', from: '⑧', to: '⑩' },
    ],
  },
  {
    file: 'docs/implementation/p5/tencent_2026q2_report_view.html',
    groups: [
      { name: 'tencent-reconciliation.png', from: '①', to: '④' },
      { name: 'tencent-segments.png', from: '④', to: '⑥' },
    ],
  },
];

async function captureGroups(page, file, groups) {
  await page.goto(pathToFileUrl(path.join(root, file)));
  await page.waitForSelector('h2');
  await page.waitForTimeout(400);
  const marks = await page.$$eval('h2', (els) =>
    els.map((e) => ({ text: e.textContent.trim(), top: e.getBoundingClientRect().top + window.scrollY })),
  );
  const docHeight = await page.evaluate(() => document.documentElement.scrollHeight);
  for (const g of groups) {
    const from = marks.find((m) => m.text.startsWith(g.from));
    const to = g.to === null ? null : marks.find((m) => m.text.startsWith(g.to));
    if (!from || (g.to !== null && !to)) throw new Error(`${file}: 找不到板块标记 ${g.from}→${g.to}`);
    const y = Math.max(0, from.top - 18);
    const bottom = to ? to.top - 12 : docHeight;
    await page.screenshot({
      path: path.join(outDir, g.name),
      clip: { x: 0, y, width: VIEWPORT.width, height: bottom - y },
      fullPage: true,
    });
    console.log(`captured ${g.name} (${VIEWPORT.width}x${Math.round(bottom - y)})`);
  }
}

function pathToFileUrl(p) {
  return 'file://' + p.split('/').map(encodeURIComponent).join('/');
}

async function captureReviewWorkbench(browser) {
  const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: 2 });
  const file = path.join(root, 'docs/knowledge-base/03_assets/visual_prototypes/metric-library-v0-review.html');
  await page.goto(pathToFileUrl(file));
  await page.waitForSelector('#tabs button');
  await page.waitForTimeout(400);

  // 总览：显式点击激活（初始 section 均带 hide），从页首到总览板块底部（封顶 2200px）
  await page.click('button[data-t="overview"]');
  await page.waitForTimeout(300);
  const overviewBottom = await page.evaluate(() => {
    const el = document.querySelector('#page-overview');
    return el.getBoundingClientRect().bottom + window.scrollY;
  });
  await page.screenshot({
    path: path.join(outDir, 'metric-library-overview.png'),
    clip: { x: 0, y: 0, width: VIEWPORT.width, height: Math.min(overviewBottom + 12, 2200) },
    fullPage: true,
  });
  console.log('captured metric-library-overview.png');

  // 勾稽与分解关系（含杜邦树）
  await page.click('button[data-t="relations"]');
  await page.waitForTimeout(300);
  const rel = await page.evaluate(() => {
    const el = document.querySelector('#page-relations');
    const r = el.getBoundingClientRect();
    return { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY };
  });
  await page.screenshot({
    path: path.join(outDir, 'metric-library-relations.png'),
    clip: { x: 0, y: Math.max(0, rel.top - 60), width: VIEWPORT.width, height: Math.min(rel.bottom - rel.top + 60, 2400) },
    fullPage: true,
  });
  console.log('captured metric-library-relations.png');
  await page.close();
}

const browser = await chromium.launch();
for (const p of pages) {
  const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: 2 });
  await captureGroups(page, p.file, p.groups);
  await page.close();
}
await captureReviewWorkbench(browser);
await browser.close();
