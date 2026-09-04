import { defineConfig, devices } from "@playwright/test";

// apps/web 专属 Playwright 配置：由门禁脚本（scripts/test_user_closure_e2e.sh、
// scripts/test_dashboard.sh）设置 PLAYWRIGHT_BASE_URL 指向已启动的 Next dev 服务器。
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: "line",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:13100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...devices["Desktop Chrome"],
  },
});
