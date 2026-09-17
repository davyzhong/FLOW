import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PageState } from "../../components/ui/page-state";

// 阶段四：页面状态统一外壳。五类状态下页面 h1 稳定渲染；错误/403 用
// role=alert；恢复动作 = 重试 + 引导链接；403 标题受控展示，不裸抛技术串。

describe("PageState", () => {
  it("renders a stable h1 with retry and guide actions on error", () => {
    const retry = vi.fn();
    render(
      <PageState
        title="经营概览"
        status="error"
        message="经营概览暂时无法加载"
        retry={retry}
        actions={[{ href: "/data", label: "前往数据接入" }]}
      />,
    );

    expect(screen.getByRole("heading", { level: 1, name: "经营概览" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "重试" }));
    expect(retry).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("link", { name: "前往数据接入" })).toHaveAttribute("href", "/data");
  });

  it("omits the h1 when the page provides its own heading", () => {
    render(<PageState status="loading" message="正在读取经营数据…" />);
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(/正在读取经营数据/);
  });

  it("announces forbidden state with a controlled code, never raw english", () => {
    render(<PageState title="指标库" status="forbidden" message="请联系管理员开通数据范围。" />);
    expect(screen.getByRole("alert")).toHaveTextContent(/无权访问（403）/);
    expect(screen.getByRole("alert")).toHaveTextContent(/请联系管理员开通数据范围/);
  });

  it("keeps loading and empty states as status regions", () => {
    const { rerender } = render(<PageState title="报告中心" status="loading" message="加载中…" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    rerender(<PageState title="报告中心" status="empty" message="尚无报告快照" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
