import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { OperationsOverviewApp } from "../../components/operations/operations-overview";

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
      unit_note: "人民币万元",
      version: 1,
      created_at: "2026-09-01T09:00:00+08:00",
    },
  ],
};

const PUBLIC_PERIODS = {
  periods: [
    {
      company_name: "菜鸟智慧物流网络",
      stock_code: "CAINIAO",
      period_label: "Q1FY2024",
      period_type: "fiscal_quarter",
      assurance: "unaudited",
      is_stub: true,
    },
  ],
};

const OVERVIEW = {
  report_id: "report-1",
  catalog_id: "flow.analysis.objective_finance.v1",
  themes: [
    {
      theme_id: "profit_quality",
      name: "盈利质量",
      availability: "financial_report",
      status: "available",
      reason: null,
      metrics: [
        {
          entry_id: "dupont_three_factor",
          name: "杜邦三分解（净利润总额口径 · 期末权益 · 未年化）",
          status: "computed",
          value: "0.1600",
          basis: "本期归一化事实",
          caliber_note: "净利润总额口径",
          reason: null,
          source: "d01_entry",
        },
        {
          entry_id: "gross_margin",
          name: "毛利率",
          status: "computed",
          value: "0.3200",
          basis: "本期归一化事实（财报直接口径）",
          caliber_note: "is.gross_profit ÷ is.revenue",
          reason: null,
          source: "fact_direct",
        },
        {
          entry_id: "current_ratio",
          name: "流动比率",
          status: "computed",
          value: "1.2345",
          basis: "本期归一化事实",
          caliber_note: "流动资产 ÷ 流动负债",
          reason: null,
          source: "fact_direct",
        },
        {
          entry_id: "international_parcels",
          name: "国际物流包裹量",
          status: "computed",
          value: "439.1234",
          basis: "Q1FY2023 347 百万件",
          caliber_note: "Selected Operating Data；期间累计值",
          reason: null,
          source: "operating_fact",
          period_label: "Q1FY2024",
          period_type: "fiscal_quarter",
          assurance: "unaudited",
          source_ref: "docs/source.pdf",
          source_sha256: "a".repeat(64),
          source_page: "22",
        },
      ],
    },
    {
      theme_id: "revenue_structure",
      name: "收入结构",
      availability: "financial_report",
      status: "not_applicable",
      reason: "segment_disclosure_missing",
      metrics: [],
    },
    {
      theme_id: "users_channels",
      name: "用户与渠道",
      availability: "internal_process",
      status: "not_applicable",
      reason: "internal_data_required",
      metrics: [],
    },
  ],
  management_watch: [
    {
      code: "cash_content_below_one",
      metric_code: "ocf_net_profit_ratio",
      message: "净利润现金含量 0.6000，经营现金流低于净利润",
      direction: "negative",
    },
  ],
  facts_available: ["is.revenue"],
};

describe("OperationsOverviewApp", () => {
  it("explains when no financial reports or public periods are available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/statements")) return jsonResponse({ reports: [] });
      if (url.endsWith("/operations/public-periods")) return jsonResponse({ periods: [] });
      return jsonResponse({ detail: "not found" }, 404);
    }));
    render(<OperationsOverviewApp />);

    expect(await screen.findByText("暂无可用经营分析数据")).toBeTruthy();
    expect(screen.getByText(/导入完整财报或等待公开经营披露数据接入/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "前往数据接入" })).toHaveAttribute("href", "/data");
    expect(screen.getByRole("link", { name: "查看公开经营分析" })).toHaveAttribute("href", "/public");
  });

  it("renders six-theme facts, management watch, honest N/A, and freezes", async () => {
    const freezeSpy = vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toContain("/operations/overview/report-1/freeze");
      return jsonResponse({
        snapshot_id: "snap-ops-1",
        version: 1,
        report_type: "operations_overview",
        payload_hash: "h".repeat(64),
      });
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") return freezeSpy(input);
      if (url.endsWith("/statements")) return jsonResponse(REPORTS);
      if (url.endsWith("/operations/public-periods")) return jsonResponse(PUBLIC_PERIODS);
      if (url.includes("/operations/overview/")) return jsonResponse(OVERVIEW);
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OperationsOverviewApp />);

    await waitFor(() => {
      expect(screen.getByText("六主题概览")).toBeTruthy();
    });
    // 事实卡片：值 + 基准 + 口径（借鉴 #1/#2）
    expect(screen.getByText("16.00%", { selector: "strong" })).toBeTruthy();
    expect(screen.getByText("32.00%", { selector: "strong" })).toBeTruthy();
    expect(screen.getByText("1.23 倍", { selector: "strong" })).toBeTruthy();
    expect(screen.getByText("439.1234", { selector: "strong" })).toBeTruthy();
    expect(screen.getByText(/口径：净利润总额口径/)).toBeTruthy();
    expect(screen.getByText(/Q1FY2024 · 未经审计/)).toBeTruthy();
    expect(screen.getByText(/docs\/source.pdf · 第 22 页/)).toBeTruthy();
    expect(screen.getByText(/aaaaaaaaaaaaaaaa…/)).toBeTruthy();
    // 诚实 N/A
    expect(screen.getByText(/待内部数据（internal_data_required）/)).toBeTruthy();
    expect(screen.getByText(/公开报告未披露分部数据/)).toBeTruthy();
    expect(screen.queryByText(/待内部数据（segment_disclosure_missing）/)).toBeNull();
    // 管理关注 ≤3 带方向；带 metric_code 时可下钻指标库（深链批次三-5）
    const watchLink = screen.getByRole("link", { name: /查看指标/ });
    expect(watchLink.getAttribute("href")).toBe(
      "/metric-library?focus=ocf_net_profit_ratio",
    );
    // 范围说明（#9 客观部分）
    expect(screen.getByText(/不在客观报告范围/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "下载 Excel" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "下载 PPT" })).toBeTruthy();

    // 冻结按钮 → 显示快照信息
    fireEvent.click(screen.getByRole("button", { name: "冻结概览" }));
    await waitFor(() => {
      expect(screen.getByText(/已冻结：版本 1/)).toBeTruthy();
    });
  });

  it("loads a public quarter without pretending it is a full statement report", async () => {
    const publicOverview = {
      ...OVERVIEW,
      report_id: "operating:CAINIAO:Q1FY2024",
      management_watch: [],
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/statements")) return jsonResponse(REPORTS);
      if (url.endsWith("/operations/public-periods")) {
        return jsonResponse(PUBLIC_PERIODS);
      }
      if (url.endsWith("/operations/public/CAINIAO/Q1FY2024")) {
        return jsonResponse(publicOverview);
      }
      if (url.includes("/operations/overview/")) return jsonResponse(OVERVIEW);
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OperationsOverviewApp />);

    const selector = await screen.findByLabelText("分析数据与期间");
    fireEvent.change(selector, {
      target: { value: "public:CAINIAO:Q1FY2024" },
    });

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) =>
          String(input).includes("/operations/public/CAINIAO/Q1FY2024"),
        ),
      ).toBe(true);
    });
    expect(screen.getByText(/公开经营披露 · 未经审计/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "冻结概览" })).toBeNull();
    expect(screen.queryByRole("link", { name: "下载 PDF" })).toBeNull();
  });
});

// 批次一 §2.1/§2.3：/operations?report= 选中参数、指标行链接指标库、冻结快照链接报告中心。
describe("OperationsOverviewApp 深链", () => {
  function stubTwoReports() {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/statements")) {
        return jsonResponse({
          reports: [
            REPORTS.reports[0],
            { ...REPORTS.reports[0], id: "report-2", company_name: "圆通速递" },
          ],
        });
      }
      if (url.endsWith("/operations/public-periods")) return jsonResponse({ periods: [] });
      if (url.includes("/operations/overview/")) return jsonResponse(OVERVIEW);
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("?report= 命中时初始选中对应财报", async () => {
    const fetchMock = stubTwoReports();
    render(<OperationsOverviewApp initialReportId="report-2" />);
    const selector = await screen.findByLabelText("分析数据与期间");
    await waitFor(() => expect(selector).toHaveValue("report:report-2"));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([input]) =>
          String(input).includes("/operations/overview/report-2"),
        ),
      ).toBe(true),
    );
  });

  it("?report= 不存在时显式提示并回退到第一份财报", async () => {
    stubTwoReports();
    render(<OperationsOverviewApp initialReportId="missing-report" />);
    expect(await screen.findByText(/未找到财报/)).toBeInTheDocument();
    const selector = screen.getByLabelText("分析数据与期间");
    await waitFor(() => expect(selector).toHaveValue("report:report-1"));
  });

  it("主题指标行链接到指标库 entry 深链，冻结快照链接到报告中心", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") {
        return jsonResponse({
          snapshot_id: "snap-ops-9",
          version: 2,
          report_type: "operations_overview",
          payload_hash: "h".repeat(64),
        });
      }
      if (url.endsWith("/statements")) return jsonResponse(REPORTS);
      if (url.endsWith("/operations/public-periods")) return jsonResponse({ periods: [] });
      if (url.includes("/operations/overview/")) return jsonResponse(OVERVIEW);
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OperationsOverviewApp />);
    const metricLink = await screen.findByRole("link", { name: /杜邦三分解/ });
    expect(metricLink).toHaveAttribute("href", "/metric-library?entry=dupont_three_factor");

    fireEvent.click(screen.getByRole("button", { name: "冻结概览" }));
    const snapshotLink = await screen.findByRole("link", { name: /snap-ops-9/ });
    expect(snapshotLink).toHaveAttribute("href", "/reports?snapshot=snap-ops-9");
  });
});
