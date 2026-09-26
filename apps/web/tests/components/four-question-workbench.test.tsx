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
    report_id: "report-1",
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

// 批次一 §2.3：analysis 身份行 → /statements?report=；指标行 → /metric-library?focus=。
describe("FourQuestionWorkbench 深链", () => {
  it("身份行链接到对应财报，指标编码链接到指标库", async () => {
    vi.stubGlobal("fetch", mockFetch());
    render(<FourQuestionWorkbench />);
    await waitFor(() => expect(screen.getByText("四问指标")).toBeTruthy());
    const identityLink = screen.getByRole("link", { name: /顺丰控股 · 2026Q1/ });
    expect(identityLink).toHaveAttribute("href", "/statements?report=report-1");
    const metricLink = screen.getByRole("link", { name: "revenue" });
    expect(metricLink).toHaveAttribute("href", "/metric-library?focus=revenue");
    // 暂不可算指标同样给出定义链接
    expect(screen.getByRole("link", { name: "revenue_growth" })).toHaveAttribute(
      "href",
      "/metric-library?focus=revenue_growth",
    );
  });
});

// 批次二 §3.2：/analysis?run_id= 接收端 —— 经 GET /analytics/analysis-runs/{id} 投影运行身份。
const RUN_DETAIL = {
  id: "run-1",
  metric_snapshot_id: "ms-1",
  import_version_id: "iv-1",
  policy_id: "flow.analysis.logistics.v1",
  policy_set_hash: "a".repeat(64),
  engine_version: "flow-analysis/1",
  fingerprint: "b".repeat(64),
  status: "published",
  created_at: "2026-09-03T09:00:00+08:00",
};

function mockFetchWithRun(runStatus: number): ReturnType<typeof vi.fn> {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/statements")) return jsonResponse(REPORTS);
    if (url.includes("/analysis/workbench/")) return jsonResponse(WORKBENCH);
    if (url.endsWith("/analytics/analysis-runs/run-1")) {
      return runStatus === 200
        ? jsonResponse(RUN_DETAIL)
        : jsonResponse({ detail: { code: "resource_scope_unresolved", message: "deny" } }, runStatus);
    }
    return jsonResponse({ detail: "not found" }, 404);
  });
}

describe("FourQuestionWorkbench run_id 深链（批次二）", () => {
  it("?run_id= 命中时渲染分析运行身份卡，快照链接到报告中心", async () => {
    vi.stubGlobal("fetch", mockFetchWithRun(200));
    render(<FourQuestionWorkbench initialRunId="run-1" />);
    const card = await screen.findByTestId("analysis-run-detail");
    expect(card).toHaveTextContent("run-1");
    expect(card).toHaveTextContent("published");
    expect(card).toHaveTextContent("flow.analysis.logistics.v1");
    expect(card).toHaveTextContent("flow-analysis/1");
    const snapshotLink = screen.getByRole("link", { name: "ms-1" });
    expect(snapshotLink).toHaveAttribute("href", "/reports?snapshot=ms-1");
    // 工作台本体不受影响
    await waitFor(() => expect(screen.getByText("四问指标")).toBeTruthy());
  });

  it("?run_id= 不存在时显式提示，不静默忽略", async () => {
    vi.stubGlobal("fetch", mockFetchWithRun(403));
    render(<FourQuestionWorkbench initialRunId="run-1" />);
    expect(await screen.findByText(/未找到分析运行「run-1」/)).toBeTruthy();
    expect(screen.queryByTestId("analysis-run-detail")).toBeNull();
    await waitFor(() => expect(screen.getByText("四问指标")).toBeTruthy());
  });
});
