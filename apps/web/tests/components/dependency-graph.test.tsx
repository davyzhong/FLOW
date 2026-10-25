import { render, screen, fireEvent } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "vitest";

// jsdom 缺少 reactflow 依赖的浏览器 API（官方测试指引）
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
  // @ts-expect-error DOMMatrixReadOnly polyfill（reactflow d3-zoom 用）
  globalThis.DOMMatrixReadOnly ??= class {
    m22 = 1;
  };
});

import { DependencyGraph } from "../../components/metric-library/dependency-graph";
import type { MetricLibraryEntry } from "../../lib/api/client";

function entry(metric_code: string, depends_on: string[], tier: "core" | "professional" = "core"): MetricLibraryEntry {
  return {
    metric_code,
    name: `指标${metric_code}`,
    domain: "profitability",
    definition: "d",
    formula_text: "f",
    formula: { op: "identity", args: [metric_code] },
    depends_on,
    tier,
    analysis_dimensions: ["trend"],
    collection: "general",
    aliases: [],
    alternative_calibers: [],
    source_cas: [],
    decompositions: [],
    mpm: false,
  } as MetricLibraryEntry;
}

const metrics = [
  entry("revenue", [], "core"),
  entry("gross_margin", ["revenue"], "core"),
  entry("net_margin", ["gross_margin"], "core"),
  entry("eva", ["net_margin"], "professional"),
];

describe("DependencyGraph", () => {
  it("默认聚焦常用指标，切换全部后可见完整图谱", () => {
    render(<DependencyGraph metrics={metrics} domains={{ profitability: "盈利能力" }} />);
    expect(screen.getByRole("region", { name: /指标依赖关系有向图/ })).toBeInTheDocument();
    expect(screen.getByText(/默认聚焦常用指标/)).toBeInTheDocument();
    expect(screen.queryByLabelText("指标eva（eva）")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "all" } });
    for (const code of ["revenue", "gross_margin", "net_margin", "eva"]) {
      expect(screen.getByLabelText(`指标${code}（${code}）`)).toBeInTheDocument();
    }
  });

  it("点击节点高亮上下游并显示计数", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "all" } });
    fireEvent.click(screen.getByLabelText("指标net_margin（net_margin）"));
    expect(screen.getByRole("status")).toHaveTextContent(/上游依赖 2 个、下游引用 1 个/);
    fireEvent.click(screen.getByRole("button", { name: "清除选择" }));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("键盘 Enter/Space 可切换节点选中态", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "all" } });
    const node = screen.getByLabelText("指标net_margin（net_margin）");

    fireEvent.keyDown(node, { key: "Enter" });
    expect(node).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("status")).toHaveTextContent(/上游依赖 2 个、下游引用 1 个/);

    fireEvent.keyDown(node, { key: " " });
    expect(node).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("跨 collection 重复指标编码保留为独立图节点", () => {
    const duplicates = [
      { ...entry("gross_margin", [], "core"), name: "毛利率", collection: "general" as const },
      { ...entry("gross_margin", [], "core"), name: "毛利率（物流口径）", collection: "logistics" as const },
    ];
    render(<DependencyGraph metrics={duplicates} domains={{}} />);

    expect(screen.getAllByLabelText(/gross_margin/)).toHaveLength(2);
    expect(screen.getByLabelText("毛利率（gross_margin）")).toBeInTheDocument();
    expect(screen.getByLabelText("毛利率（物流口径）（gross_margin）")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("毛利率（物流口径）（gross_margin）"));
    expect(screen.getByRole("link", { name: "查看指标卡片" })).toHaveAttribute(
      "href",
      "/metric-library?focus=gross_margin&collection=logistics",
    );
  });

  it("分层过滤只保留对应节点", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "professional" } });
    expect(screen.getByLabelText("指标eva（eva）")).toBeInTheDocument();
    expect(screen.queryByLabelText("指标revenue（revenue）")).not.toBeInTheDocument();
  });

  it("切换分层时清除已隐藏节点的选中状态", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "all" } });
    fireEvent.click(screen.getByLabelText("指标eva（eva）"));
    expect(screen.getByRole("status")).toHaveTextContent("指标eva");

    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "core" } });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "查看指标卡片" })).not.toBeInTheDocument();
  });

  it("环依赖不崩溃并给出警示", () => {
    const cyclic = [entry("a", ["b"]), entry("b", ["a"])];
    render(<DependencyGraph metrics={cyclic} domains={{}} />);
    expect(screen.getByRole("note")).toHaveTextContent(/依赖环/);
  });
});
