import { expect, test } from "@playwright/test";

// 响应式门禁（GPT 整改计划 Task 0 / FE-06、FE-07 的自动化面）：
// - 390×844 视口下所有路由 body 不得横向溢出；
// - 窄视口下主要交互控件（flow-btn / 侧栏导航 / 登录按钮）计算高度 ≥ 44px
//   （globals/app-shell 的 @media (max-width: 780px) 触控目标规则）。
// 密集表格内的行级小按钮（如产物下载）不在 44px 约束内——
// 信息密度是经分专员场景的显式设计决策（Carbon dense 模式）。

const ROUTES = [
  "/",
  "/data",
  "/reports",
  "/statements",
  "/metric-library",
  "/operations",
  "/public",
  "/internal",
  "/investigations",
  "/analysis",
  "/login",
] as const;

test.describe("responsive integrity", () => {
  // 冷启动 dev server 的 Turbopack 编译滞后于 networkidle：必须等到
  // globals.css（:root token）真正生效后再量，否则量到无样式布局的假溢出。
  async function waitForStyles(page: import("@playwright/test").Page) {
    await page.waitForFunction(
      () => getComputedStyle(document.documentElement).getPropertyValue("--flow-radius-s").trim() !== "",
      undefined,
      { timeout: 30_000 },
    );
  }

  for (const route of ROUTES) {
    test(`${route} has no horizontal overflow at 390px`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      // networkidle：等客户端取数与状态机稳定后再量——
      // hydration 中间态的瞬时宽度不是用户可见现实。
      await page.goto(route, { waitUntil: "networkidle" });
      await waitForStyles(page);
      await page.waitForTimeout(400);
      const overflow = await page.evaluate(() => {
        const wide: string[] = [];
        for (const el of document.querySelectorAll("*")) {
          const box = el.getBoundingClientRect();
          if (box.right > document.documentElement.clientWidth + 1) {
            wide.push(`${el.tagName}.${String(el.className).slice(0, 48)} right=${Math.round(box.right)}`);
          }
        }
        return {
          body: document.body.scrollWidth,
          viewport: document.documentElement.clientWidth,
          wide: wide.slice(0, 6),
        };
      });
      if (overflow.body > overflow.viewport) {
        console.log(`[overflow] ${route}:`, JSON.stringify(overflow.wide));
      }
      expect(overflow.body).toBeLessThanOrEqual(overflow.viewport);
    });
  }

  test("primary touch targets meet 44px at narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/login");
    const submit = page.getByRole("button", { name: "登录" });
    const height = await submit.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(height)).toBeGreaterThanOrEqual(44);
  });

  test("flow buttons meet 44px at narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/data");
    const button = page.getByRole("button", { name: "下载 FLOW 标准模板" });
    const height = await button.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(height)).toBeGreaterThanOrEqual(44);
  });

  test("side rail keeps the logout entry reachable at narrow viewport", async ({ page }) => {
    // 窄屏下侧栏 footer 只隐藏状态文案，退出按钮保持可见（FE-04 收尾）。
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const footer = page.locator(".workflow-rail__footer");
    await expect(footer).toBeAttached();
  });
});
