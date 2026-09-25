import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

// 深链接收端（批次一 §2.1）：?focus={metric_code} / ?entry={entry_id} 滚动定位并高亮卡片；
// 依赖 chip、治理事件表、分录模板关联指标 → 卡片锚点链接（§2.2-5/6、§2.3）。

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function metric(
  metricCode: string,
  entryId: string,
  collection: "general" | "logistics",
  dependsOn: string[] = [],
) {
  return {
    metric_code: metricCode,
    name: `指标-${metricCode}`,
    entry_id: entryId,
    status: "effective",
    execution_kind: "facts",
    collection,
    domain: "profitability",
    definition: "定义",
    formula_text: "公式",
    mpm: false,
    aliases: [],
    depends_on: dependsOn,
    source_cas: [],
    decompositions: [],
    alternative_calibers: [],
  };
}

const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { profitability: "盈利能力" },
  report_items: [],
  metrics: [
    metric("roe", "entry-roe", "general"),
    metric("gross_margin", "entry-gm", "general", ["roe", "unknown_code"]),
    metric("on_time_rate", "entry-otr", "logistics"),
  ],
  relations: [],
  accounting: {
    dataset_id: "flow.accounting_foundation.v1",
    status: "effective",
    known_gaps: [],
    categories: [],
    accounts: [],
    superseded_notes: [],
    standards: [],
    entry_templates: [
      {
        template_id: "tpl-1",
        scenario: "确认收入",
        business_context: null,
        lines: [],
        standard_ref: null,
        related_metrics: ["roe", "unknown_code"],
      },
    ],
  },
};

const EVENTS = {
  events: [
    {
      id: "ev-1",
      metric_code: "roe",
      version: 2,
      action: "activate",
      operator: "finance.bp",
      reason: "口径生效",
      created_at: "2026-09-10T08:00:00+00:00",
    },
    {
      id: "ev-2",
      metric_code: "retired_metric",
      version: 1,
      action: "retire",
      operator: "finance.bp",
      reason: "退役",
      created_at: "2026-09-09T08:00:00+00:00",
    },
  ],
};

function stubLibraryFetch() {
  return vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/metric-library/events")) return Promise.resolve(jsonResponse(EVENTS));
      return Promise.resolve(jsonResponse(LIBRARY));
    }),
  );
}

describe("MetricLibraryApp 深链定位", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("?focus= 命中物流指标时切换到对应分区并高亮卡片锚点", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp focus="on_time_rate" />);
    expect(await screen.findByText("指标-on_time_rate")).toBeInTheDocument();
    const card = document.getElementById("metric-entry-entry-otr");
    expect(card).not.toBeNull();
    expect(card).toHaveClass("ml-metric--focused");
    expect(screen.getByRole("button", { name: "物流行业指标" })).toHaveClass("is-active");
    expect(screen.queryByText(/未找到指标/)).not.toBeInTheDocument();
  });

  it("?entry= 按 entry_id 定位并赋予卡片锚点 id", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp entry="entry-roe" />);
    expect(await screen.findByText("指标-roe")).toBeInTheDocument();
    expect(document.getElementById("metric-entry-entry-roe")).toHaveClass("ml-metric--focused");
  });

  it("参数对象不存在时显式提示且展示完整列表", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp focus="no_such_metric" />);
    expect(await screen.findByText(/未找到指标「no_such_metric」/)).toBeInTheDocument();
    expect(screen.getByText("指标-roe")).toBeInTheDocument();
  });

  it("依赖指标 chip 对已知编码渲染链接、未知编码保持纯文本", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp />);
    expect(await screen.findByText("指标-gross_margin")).toBeInTheDocument();
    const depLink = screen.getByRole("link", { name: "roe" });
    expect(depLink).toHaveAttribute("href", "/metric-library?focus=roe");
    // unknown_code 不在库内：诚实约束——不渲染链接
    expect(screen.queryByRole("link", { name: "unknown_code" })).not.toBeInTheDocument();
    expect(screen.getByText("unknown_code")).toBeInTheDocument();
  });

  it("治理事件表的已知指标编码链接到卡片锚点，未知编码不渲染链接", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp />);
    fireEvent.click(await screen.findByRole("button", { name: "治理记录" }));
    expect(await screen.findByText("口径生效")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: "roe" });
    expect(link).toHaveAttribute("href", "/metric-library?focus=roe");
    expect(screen.queryByRole("link", { name: "retired_metric" })).not.toBeInTheDocument();
  });

  it("分录模板关联指标对已知编码渲染链接", async () => {
    stubLibraryFetch();
    render(<MetricLibraryApp />);
    fireEvent.click(await screen.findByRole("button", { name: "会计基础数据" }));
    expect(await screen.findByText("确认收入")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "roe" })).toHaveAttribute(
      "href",
      "/metric-library?focus=roe",
    );
    expect(screen.queryByRole("link", { name: "unknown_code" })).not.toBeInTheDocument();
  });
});
