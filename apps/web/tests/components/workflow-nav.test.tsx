import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkflowNav } from "../../components/dashboard/workflow-nav";

// F1-1 两级信息架构导航测试。usePathname 以 mock 注入（组件依赖 Next app router）。
const mockPathname = vi.hoisted(() => ({ value: "/" }));
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname.value,
}));

function renderAt(path: string) {
  mockPathname.value = path;
  return render(<WorkflowNav />);
}

describe("WorkflowNav 两级模块导航（F1-1）", () => {
  beforeEach(() => {
    mockPathname.value = "/";
  });

  it("公开财报分析分组：模块总览/报表分析/指标库 三入口", () => {
    renderAt("/public");
    expect(screen.getByRole("link", { name: /模块总览/ })).toHaveAttribute("href", "/public");
    expect(screen.getByRole("link", { name: /报表分析/ })).toHaveAttribute("href", "/statements");
    expect(screen.getByRole("link", { name: /指标库/ })).toHaveAttribute("href", "/metric-library");
    expect(screen.getByText("公开财报分析")).toBeInTheDocument();
  });

  it("内部经营分析分组：全部旧入口以正式名称保留可达", () => {
    renderAt("/");
    for (const label of ["工作台总览", "经营总览", "数据接入", "调查归因", "四问工作台", "报告与导出", "经营概览"]) {
      expect(screen.getByRole("link", { name: new RegExp(label) })).toBeInTheDocument();
    }
    // 信息架构完成：「旧路由兼容入口」暴露被移除
    expect(screen.queryByText("旧路由兼容入口")).not.toBeInTheDocument();
    expect(screen.getByText("内部经营分析")).toBeInTheDocument();
  });

  it("每个交互路由在导航中恰有 1 个 plain 入口（守护 navigation.spec 合同）", () => {
    renderAt("/statements");
    const nav = screen.getByRole("navigation", { name: "FLOW 工作流" });
    for (const href of [
      "/", "/public", "/internal", "/data", "/investigations",
      "/analysis", "/reports", "/statements", "/metric-library", "/operations",
    ]) {
      expect(nav.querySelectorAll(`a[href="${href}"]`)).toHaveLength(1);
    }
  });

  it("激活态：当前路由标记 is-active 且 aria-current=page", () => {
    renderAt("/statements");
    const active = screen.getByRole("link", { name: /报表分析/ });
    expect(active).toHaveAttribute("aria-current", "page");
    expect(active.closest("li")).toHaveClass("is-active");
  });

  it("各路由下 AppShell 导航可见（单一导航）", () => {
    for (const route of ["/", "/public", "/internal", "/data", "/statements", "/metric-library"]) {
      const { unmount } = renderAt(route);
      expect(screen.getByRole("navigation", { name: "FLOW 工作流" })).toBeInTheDocument();
      unmount();
    }
  });
});
