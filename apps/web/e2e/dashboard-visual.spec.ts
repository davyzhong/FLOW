import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 1440, height: 900, name: "dashboard-1440-linux.png" },
  { width: 1920, height: 1080, name: "dashboard-1920-linux.png" },
]) {
  test(`dashboard visual baseline at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/");
    await expect(page.getByTestId("metric-card")).toHaveCount(8);
    await expect(page).toHaveScreenshot(viewport.name, {
      fullPage: true,
      animations: "disabled",
      maxDiffPixelRatio: 0.03,
    });
  });
}
