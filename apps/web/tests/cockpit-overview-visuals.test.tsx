import { describe, expect, it, vi } from "vitest";

vi.mock("../components/cockpit/charts/echarts-base", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../components/cockpit/charts/echarts-base")>()),
  ChartBox: ({ title, testId }: { title: string; testId?: string }) => <div data-testid={testId}>{title}</div>,
}));
import { render, screen } from "@testing-library/react";

import { CockpitOverviewVisuals } from "../components/cockpit/cockpit-overview-visuals";
import type { CockpitModuleResponse, CockpitOverviewResponse, CockpitProfitabilityResponse } from "../lib/api/client";

const overview = {
  context: { metric_snapshot_id: "overview-snapshot", as_of_month: "FY2023" },
  trends: [{
    status: "complete",
    unit: "CNY",
    series: [
      { key: "revenue", title: "营业收入", unit: "CNY", points: [{ period: "FY2022", value: 120000000, status: "ready" }, { period: "FY2023", value: 150000000, status: "ready" }] },
      { key: "operating_profit", title: "营业利润", unit: "CNY", points: [{ period: "FY2022", value: 10000000, status: "ready" }, { period: "FY2023", value: 14000000, status: "ready" }] },
      { key: "gross_margin", title: "毛利率", unit: "ratio", points: [{ period: "FY2022", value: 0.31, status: "ready" }, { period: "FY2023", value: 0.34, status: "ready" }] },
      { key: "operating_cash_flow", title: "经营现金流", unit: "CNY", points: [{ period: "FY2022", value: 9000000, status: "ready" }, { period: "FY2023", value: 12000000, status: "ready" }] },
    ],
  }],
} as unknown as CockpitOverviewResponse;

const supplements = {
  profitability: {
    periods: [{
      period: "FY2023", report_id: "report-2023", snapshot_id: "snapshot-2023",
      consistency: { status: "passed" },
      metrics: [
        { metric_code: "roe", status: "available", value: "0.126", formula: "净利润 ÷ 平均净资产", report_id: "report-2023", snapshot_id: "snapshot-2023" },
        { metric_code: "net_margin", status: "available", value: "0.089", formula: "净利润 ÷ 营业收入", report_id: "report-2023", snapshot_id: "snapshot-2023" },
        { metric_code: "total_asset_turnover", status: "available", value: "0.9", formula: "营业收入 ÷ 平均总资产", report_id: "report-2023", snapshot_id: "snapshot-2023" },
        { metric_code: "equity_multiplier", status: "available", value: "1.6", formula: "平均总资产 ÷ 平均净资产", report_id: "report-2023", snapshot_id: "snapshot-2023" },
      ],
    }],
    source_notice: "公开财报演示口径",
  } as unknown as CockpitProfitabilityResponse,
  cashflow: {
    title: "现金流", period: "FY2023", prior_period: "FY2022", snapshot_id: "cash-snapshot",
    report_ids: ["report-2023"], source_notice: "公开财报披露", unit: "百万元",
    charts: { cash_bridge: {
      title: "现金变动桥", type: "waterfall", unit: "百万元",
      steps: { 年初: 30, 经营: 12, 投资: -8, 筹资: 4, 年末: 38 },
      analysis_question: "现金余额如何变化？", fact_classes: ["reported"], source_ids: ["cash-flow"], metric_codes: [], snapshot_id: "cash-snapshot",
    } },
  } as unknown as CockpitModuleResponse,
  expenses: {
    title: "费用分析", period: "FY2023", prior_period: "FY2022", snapshot_id: "expense-snapshot",
    report_ids: ["report-2023"], source_notice: "公开财报披露", unit: "百万元",
    charts: { expense_structure: {
      title: "费用结构", type: "ratio_bar", unit: "百万元",
      series: { 销售: 20, 管理: 12, 研发: 8, 财务: 3 },
      analysis_question: "各项费用如何构成？", fact_classes: ["reported"], source_ids: ["expense"], metric_codes: [], snapshot_id: "expense-snapshot",
    } },
  } as unknown as CockpitModuleResponse,
};

describe("CockpitOverviewVisuals", () => {
  it("把经营趋势、现金桥、杜邦因子和费用结构组成可追溯的报告画布", () => {
    render(<CockpitOverviewVisuals overview={overview} supplements={supplements} loading={false} />);

    expect(screen.getByTestId("cockpit-overview-revenue-profit-chart")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "收入与营业利润" })).toBeTruthy();
    expect(screen.getByTestId("cockpit-overview-cashflow-chart")).toBeTruthy();
    expect(screen.getByTestId("cockpit-overview-expense-chart")).toBeTruthy();
    expect(screen.getByText("净资产收益率 ROE")).toBeTruthy();
    expect(screen.getByText("12.60%")).toBeTruthy();
    expect(screen.getByText(/集团披露口径/)).toBeTruthy();
    expect(screen.getByRole("link", { name: /查看现金流明细/ }).getAttribute("href")).toBe("/cockpit/cashflow");
    expect(screen.getByRole("link", { name: /查看费用分析/ }).getAttribute("href")).toBe("/cockpit/expenses");
    expect(screen.getByRole("link", { name: /杜邦分析/ }).getAttribute("href")).toBe("/cockpit/profitability");
    for (const key of ["revenue", "operating_profit", "gross_margin", "operating_cash_flow"]) {
      expect(screen.getByTestId(`cockpit-overview-trend-row-${key}`)).toBeTruthy();
    }
  });

  it("没有可用的披露补充时明确展示不可用状态，不补造图表", () => {
    render(<CockpitOverviewVisuals overview={overview} supplements={null} loading={false} />);
    expect(screen.getByText(/尚无可用的已发布现金流披露/)).toBeTruthy();
    expect(screen.getByText(/尚无可用的已发布费用披露/)).toBeTruthy();
    expect(screen.queryByTestId("cockpit-overview-cashflow-chart")).toBeNull();
  });
});
