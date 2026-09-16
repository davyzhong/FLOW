import { test } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";

const CASES: Record<string, string> = {
  A_div_dtdd: '<dl class="stmt-kpi-grid"><div class="stmt-kpi__body"><dt>营业收入</dt><dd>741.42 亿元</dd></div><div class="stmt-kpi__body"><dt>净利润</dt><dd>26.51 亿元</dd></div></dl>',
  B_div_dt_span_dd: '<dl class="stmt-kpi-grid"><div class="stmt-kpi__body"><dt><span>营</span>营业收入</dt><dd>741.42 亿元</dd></div></dl>',
  C_dl_direct_dtdd_span: '<dl class="stmt-kpi-grid"><dt><span>营</span>营业收入</dt><dd>741.42 亿元</dd></dl>',
  D_div_extra_child: '<dl class="stmt-kpi-grid"><span class="seal">营</span><div class="stmt-kpi__body"><dt>营业收入</dt><dd>741.42 亿元</dd></div></dl>',
};

for (const [name, html] of Object.entries(CASES)) {
  test(`axe: ${name}`, async ({ page }) => {
    await page.setContent(`<html><body style="background:#16324f">${html}</body></html>`);
    const results = await new AxeBuilder({ page })
      .withRules(["definition-list"])
      .analyze();
    const v = results.violations.filter((x) => x.id === "definition-list");
    console.log(`RESULT ${name}: violations=${v.reduce((s, x) => s + x.nodes.length, 0)}`);
  });
}
