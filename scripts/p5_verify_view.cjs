const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file:///Users/qiming/workspace/FLOW/docs/implementation/p5/sf_2026q1_report_view.html');
  await page.waitForTimeout(800);
  const checks = {
    title: await page.locator('h1').textContent(),
    kpis: await page.locator('.kpi').count(),
    metrics: await page.locator('.metric').count(),
    svgs: await page.locator('svg').count(),
    stackbars: await page.locator('.stackbar').count(),
    tables: await page.locator('table').count(),
    badges: await page.locator('.badge').allTextContents(),
    dupont_text: await page.locator('#sec-dupont svg text').allTextContents(),
    peer_text: await page.locator('#sec-peer table').textContent(),
  };
  console.log(JSON.stringify(checks, null, 1));
  console.log('JS errors:', errors.length ? errors : 'none');
  await page.screenshot({ path: '/tmp/p5_view_top.png' });
  await page.locator('#sec-dupont').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/p5_view_dupont.png' });
  await page.locator('#sec-peer').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/p5_view_peer.png' });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/p5_view_low.png' });
  await browser.close();
})();
