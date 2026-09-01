import { expect, test } from "@playwright/test";

import { dashboardOracle } from "./support";

test("stale and degraded response states remain explicit", async ({ page }) => {
  const oracle = dashboardOracle();
  for (const [state, message] of [
    ["stale", "数据已陈旧，请检查最新发布批次"],
    ["degraded", "部分分析面板已降级"],
  ] as const) {
    await page.route("**/api/v1/dashboard/overview*", (route) =>
      route.fulfill({ json: { ...oracle, state } }),
    );
    await page.goto("/");
    await expect(page.getByText(message)).toBeVisible();
    await page.unrouteAll({ behavior: "wait" });
  }
});

test("failed dashboard request can be retried", async ({ page }) => {
  const oracle = dashboardOracle();
  let shouldSucceed = false;
  await page.route("**/api/v1/dashboard/overview*", (route) => {
    return shouldSucceed
      ? route.fulfill({ json: oracle })
      : route.fulfill({ status: 503, json: { detail: "temporary" } });
  });
  await page.goto("/");
  await expect(page.getByText("经营驾驶舱暂时无法加载")).toBeVisible();
  shouldSucceed = true;
  await page.getByRole("button", { name: "重试" }).click();
  await expect(page.getByTestId("metric-card")).toHaveCount(8);
});
