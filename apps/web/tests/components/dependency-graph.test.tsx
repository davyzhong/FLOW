import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
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
  it("渲染全部节点与分层", () => {
    render(<DependencyGraph metrics={metrics} domains={{ profitability: "盈利能力" }} />);
    expect(screen.getByRole("img", { name: /指标依赖关系有向图/ })).toBeInTheDocument();
    for (const code of ["revenue", "gross_margin", "net_margin", "eva"]) {
      expect(screen.getByLabelText(`指标${code}（${code}）`)).toBeInTheDocument();
    }
  });

  it("点击节点高亮上下游并显示计数", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.click(screen.getByLabelText("指标net_margin（net_margin）"));
    expect(screen.getByRole("status")).toHaveTextContent(/上游依赖 2 个、下游引用 1 个/);
    fireEvent.click(screen.getByRole("button", { name: "清除选择" }));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("分层过滤只保留对应节点", () => {
    render(<DependencyGraph metrics={metrics} domains={{}} />);
    fireEvent.change(screen.getByLabelText(/分层/), { target: { value: "professional" } });
    expect(screen.getByLabelText("指标eva（eva）")).toBeInTheDocument();
    expect(screen.queryByLabelText("指标revenue（revenue）")).not.toBeInTheDocument();
  });

  it("环依赖不崩溃并给出警示", () => {
    const cyclic = [entry("a", ["b"]), entry("b", ["a"])];
    render(<DependencyGraph metrics={cyclic} domains={{}} />);
    expect(screen.getByRole("note")).toHaveTextContent(/依赖环/);
  });
});
