import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkflowNav } from "../../components/dashboard/workflow-nav";

// Task 2C：模块入口导航测试。usePathname 以 mock 注入（组件依赖 Next app router）。
const mockPathname = vi.hoisted(() => ({ value: "/" }));
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname.value,
}));

function renderAt(path: string) {
  mockPathname.value = path;
  return render(<WorkflowNav />);
}

describe("WorkflowNav 模块入口（Task 2C）", () => {
  beforeEach(() => {
    mockPathname.value = "/";
  });

  it("渲染公开财报分析入口并指向 /public（implemented）", () => {
    renderAt("/public");
    const link = screen.getByRole("link", { name: /公开财报分析/ });
    expect(link).toHaveAttribute("href", "/public");
  });

  it("渲染企业内部分析工作台入口并指向 /internal（designed）", () => {
    renderAt("/internal");
    const link = screen.getByRole("link", { name: /企业内部分析工作台/ });
    expect(link).toHaveAttribute("href", "/internal");
  });

  it("渲染专业治理底座入口（designed，governance 层）并指向内部页锚点", () => {
    renderAt("/internal");
    const link = screen.getByRole("link", { name: /专业治理底座/ });
    expect(link).toHaveAttribute("href", "/internal#governance");
  });

  it("旧路由兼容分组保留：数据接入/驾驶舱/工作台/报表/指标库", () => {
    renderAt("/");
    for (const label of ["数据接入", "经营总览", "四问工作台", "报告与导出", "报表分析", "指标库"]) {
      expect(screen.getByRole("link", { name: new RegExp(label) })).toBeInTheDocument();
    }
  });

  it("各路由下 AppShell 导航可见（单一导航）", () => {
    for (const route of ["/", "/public", "/internal", "/data", "/statements", "/metric-library"]) {
      const { unmount } = renderAt(route);
      expect(screen.getByRole("navigation", { name: "FLOW 工作流" })).toBeInTheDocument();
      unmount();
    }
  });
});
