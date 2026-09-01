import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("real governed dashboard filters and hands off immutable investigation context", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Finance BP 经营驾驶舱" })).toBeVisible();
  await expect(page.getByTestId("metric-card")).toHaveCount(8);
  await expect(page.getByText("已发布经营数据")).toBeVisible();

  await page.getByLabel("期间").selectOption("ytd");
  await expect(page).toHaveURL(/period_view=ytd/);
  await expect(page.getByTestId("metric-card")).toHaveCount(8);

  await page.getByRole("link", { name: /履约成本增加：进入调查/ }).click();
  await expect(page.getByRole("heading", { name: "经营调查上下文" })).toBeVisible();
  const receipt = page.getByRole("region", { name: "不可变分析上下文" });
  await expect(receipt).toContainText("Finding ID");
  await expect(receipt).toContainText("数据批次 ID");
  await expect(receipt).toContainText("指标快照 ID");
  await expect(receipt).toContainText("分析运行 ID");
});

test("dashboard has no serious or critical axe violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("metric-card")).toHaveCount(8);
  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter(
      (violation) => violation.impact === "serious" || violation.impact === "critical",
    ),
  ).toEqual([]);
});
