import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// U7 四问工作台（借鉴 #5）：管理关注 ≤3 条、四问指标诚实降级、无严重无障碍违规。
test("workbench page renders four questions without serious axe violations", async ({
  page,
}) => {
  await page.goto("/analysis");
  await expect(page.getByRole("heading", { name: "四问分析工作台" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "四问指标" })).toBeVisible();

  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical",
  );
  expect(serious).toEqual([]);
});
