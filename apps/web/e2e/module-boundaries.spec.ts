import { test, expect } from "@playwright/test";

// Task 2C：模块边界 E2E。页面为批准的静态模块描述（设计 §5.4 同字节 fixture），
// 不请求 /api/v1/modules；断言三入口语义、implemented/designed 状态与无虚假按钮。

const MODULE_ENTRY = "/public";
const INTERNAL_ENTRY = "/internal";

test.describe("module boundaries", () => {
  test("公开财报分析入口呈现 implemented 状态并提供进入链接", async ({ page }) => {
    await page.goto(MODULE_ENTRY);
    const card = page.locator(".module-landing__card", { hasText: "公开财报分析" });
    await expect(card).toBeVisible();
    await expect(card.locator(".module-landing__status--implemented")).toHaveText("已实现");
    await expect(card.getByRole("link", { name: "进入公开财报分析" })).toHaveAttribute(
      "href",
      "/statements",
    );
  });

  test("企业内部分析入口呈现 designed 状态且无虚假操作按钮", async ({ page }) => {
    await page.goto(INTERNAL_ENTRY);
    const card = page.locator(".module-landing__card", { hasText: "企业内部分析工作台" });
    await expect(card).toBeVisible();
    await expect(card.locator(".module-landing__status--designed")).toHaveText("规划中");
    await expect(card.getByRole("link")).toHaveCount(0);
    await expect(card.getByText(/尚未提供可操作入口/)).toBeVisible();
  });

  test("专业治理底座（governance 层）呈现 designed 状态", async ({ page }) => {
    await page.goto(INTERNAL_ENTRY);
    const card = page.locator(".module-landing__card", { hasText: "专业治理底座" });
    await expect(card).toBeVisible();
    await expect(card.locator(".module-landing__status--designed")).toHaveText("规划中");
  });

  test("AppShell 导航保留且含三模块入口", async ({ page }) => {
    await page.goto(MODULE_ENTRY);
    const nav = page.locator('nav[aria-label="FLOW 工作流"]');
    await expect(nav).toBeVisible();
    await expect(nav.locator('a[href="/public"]')).toHaveCount(1);
    await expect(nav.locator('a[href="/internal"]')).toHaveCount(1);
    await expect(nav.locator('a[href="/internal#governance"]')).toHaveCount(1);
  });
});
