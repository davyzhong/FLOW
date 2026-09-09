import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FourQuestionWorkbench } from "../../components/analysis/four-question-workbench";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const REPORTS = {
  reports: [
    {
      id: "report-1",
      company_name: "顺丰控股",
      stock_code: "002352.SZ",
      report_kind: "一季报",
      period_label: "2026Q1",
      status: "published",
      created_at: "2026-09-01T09:00:00+08:00",
    },
  ],
};

const WORKBENCH = {
  workbench_id: "flow.analysis.objective_topics.v1",
  report: {
    id: "report-1",
    company_name: "顺丰控股",
    period_label: "2026Q1",
    unit_note: "人民币万元",
  },
  questions: [
    {
      key: "growth",
      name: "增长",
      metrics: [
        { metric_code: "revenue", available: true, value: "500.0000" },
        { metric_code: "revenue_growth", available: false },
      ],
    },
    {
      key: "profit",
      name: "盈利",
      metrics: [{ metric_code: "net_margin", available: true, value: "0.0320" }],
    },
    { key: "capital", name: "资本", metrics: [] },
    { key: "cash", name: "现金", metrics: [] },
  ],
  management_watch: [
    {
      code: "cash_content_below_one",
      message: "净利润现金含量 0.6000，经营现金流低于净利润",
      direction: "negative",
    },
  ],
  facts_available: ["is.revenue", "is.net_profit", "cf.ocf"],
};

function mockFetch(): ReturnType<typeof vi.fn> {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/statements")) return jsonResponse(REPORTS);
    if (url.includes("/analysis/workbench/")) return jsonResponse(WORKBENCH);
    return jsonResponse({ detail: "not found" }, 404);
  });
}

describe("FourQuestionWorkbench", () => {
  it("renders four questions, management watch, and honest unavailability", async () => {
    vi.stubGlobal("fetch", mockFetch());
    render(<FourQuestionWorkbench />);

    await waitFor(() => {
      expect(screen.getByText("四问指标")).toBeTruthy();
    });
    expect(screen.getByText("增长")).toBeTruthy();
    expect(screen.getByText("盈利")).toBeTruthy();
    // 管理关注：≤3 条、带方向标签与数值
    expect(screen.getByText("管理关注（≤3 条，提示复核）")).toBeTruthy();
    expect(screen.getByText(/净利润现金含量 0.6000/)).toBeTruthy();
    // 不可用指标诚实降级
    expect(screen.getByText("暂不可算（缺披露事实）")).toBeTruthy();
  });

});
