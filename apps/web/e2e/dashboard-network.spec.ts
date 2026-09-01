import { expect, test } from "@playwright/test";

const forbidden = /source-files|source-records|canonical|metric-values|analysis-runs|analysis-results|findings/i;

test("browser consumes only the typed dashboard API boundary", async ({ page }) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/")) apiRequests.push(url.pathname);
  });

  await page.goto("/");
  await expect(page.getByTestId("metric-card")).toHaveCount(8);
  await page.getByLabel("期间").selectOption("ytd");
  await expect(page).toHaveURL(/period_view=ytd/);

  expect(apiRequests.length).toBeGreaterThanOrEqual(2);
  expect(apiRequests.every((path) => path === "/api/v1/dashboard/overview")).toBe(true);
  expect(apiRequests.filter((path) => forbidden.test(path))).toEqual([]);
});
