import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WorkflowNav } from "../components/dashboard/workflow-nav";

// T1 认证壳守卫（GPT 整改计划 Task 1 / FE-03、FE-04）：
// 退出入口只允许出现在已认证应用的工作流侧栏（AppShell 传入 showLogout）；
// 根布局不得再渲染全局退出 footer（曾导致 /login 与所有业务页底部出现孤立按钮）；
// 登录页不得回退到整页行内样式。

const WEB_ROOT = join(__dirname, "..");

describe("auth shell placement", () => {
  it("renders the logout entry only when showLogout is set", () => {
    const { unmount } = render(<WorkflowNav showLogout />);
    expect(screen.getByRole("button", { name: "退出登录" })).toBeInTheDocument();
    unmount();

    render(<WorkflowNav />);
    expect(screen.queryByRole("button", { name: "退出登录" })).not.toBeInTheDocument();
  });

  it("keeps the root layout free of auth UI", () => {
    const layout = readFileSync(join(WEB_ROOT, "app", "layout.tsx"), "utf-8");
    expect(layout).not.toContain("/api/auth/logout");
  });

  it("keeps the login page free of inline styles", () => {
    const login = readFileSync(join(WEB_ROOT, "app", "login", "page.tsx"), "utf-8");
    expect(login).not.toContain("style={{");
    expect(login).toContain('import "./login.css"');
  });
});
