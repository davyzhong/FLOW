import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../components/cockpit/charts/echarts-base", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../components/cockpit/charts/echarts-base")>()),
  ChartBox: ({ testId, title }: { testId?: string; title: string }) => <div data-testid={testId}>{title}</div>,
}));

import { CockpitModulePage } from "../../components/cockpit/module-page";
import * as client from "../../lib/api/client";
import type { CockpitModuleResponse } from "../../lib/api/client";

const moduleFixture: CockpitModuleResponse = {
  module: "balance-sheet",
  title: "资产负债",
  period: "FY2023",
  prior_period: "FY2022",
  snapshot_id: "snap-1",
  report_ids: ["r1", "r2"],
  source_notice: "数据源：菜鸟申请稿披露财报（IFRS）·大麦物流演示主体引用",
  unit: "百万元",
  kpis: [
    {
      name: "总资产",
      status: "available",
      value: "71850.9310",
      prior_value: "58881.0870",
      unit: "百万元",
      caliber_note: null,
    },
    {
      name: "有息负债（借款总额）",
      status: "available",
      value: "14041.8160",
      prior_value: "6862.2740",
      unit: "百万元",
      caliber_note: "申请稿「借款」为长短期混合行；短债拆分未披露",
    },
    {
      name: "短债拆分",
      status: "unavailable",
      unavailable_code: "not_disclosed",
      unit: "百万元",
      caliber_note: null,
    },
  ],
  charts: {
    capital_structure_trend: {
      title: "资本结构趋势",
      type: "line",
      periods: ["FY2022", "FY2023"],
      series: { 资产负债率: ["0.7713", "0.6319"] },
      note: "有息负债率需短债拆分，未披露 → unavailable",
    },
  },
  unavailable: [
    {
      block: "债务期限结构",
      code: "debt_maturity_split_not_disclosed",
      reason: "申请稿「借款」为长短期混合行，期限拆分未披露",
    },
  ],
};

describe("CockpitModulePage", () => {
  it("渲染 KPI、真实图形、规范数值、图表数据表与不可用块", async () => {
    const fetchSpy = vi
      .spyOn(client.flowApi, "getCockpitModule")
      .mockResolvedValue(moduleFixture);
    render(<CockpitModulePage moduleId="balance-sheet" title="资产负债" />);
    expect(await screen.findByText("71,850.93 百万元")).toBeVisible();
    expect(screen.getByText("前期 58,881.09 百万元")).toBeVisible();
    expect(screen.getAllByText("资本结构趋势").length).toBeGreaterThan(0);
    expect(screen.getByTestId("cockpit-module-chart-capital_structure_trend")).toBeVisible();
    expect(screen.getByText("债务期限结构")).toBeVisible();
    expect(screen.getByText(/大麦物流演示主体引用/)).toBeVisible();
    expect(fetchSpy).toHaveBeenCalledOnce();
  });
});


describe("费用图表 API 形态", () => {
  it("把标量费用系列作为单期图表渲染而不触发数组 map 错误", async () => {
    vi.spyOn(client.flowApi, "getCockpitModule").mockResolvedValue({
      ...moduleFixture,
      module: "expenses",
      title: "费用分析",
      kpis: [{ name: "销售费用", status: "available", value: "1476.0000", rate: "0.0189", unit: "百万元" }],
      charts: {
        expense_structure: {
          title: "费用结构",
          type: "ratio_bar",
          unit: "百万元",
          periods: ["FY2023"],
          series: { 销售: "1476.0000", 管理: "738.0000", 研发: "210.0000", 财务: "83.0000" },
        },
      },
    } as CockpitModuleResponse);

    render(<CockpitModulePage moduleId="expenses" title="费用分析" />);
    expect(await screen.findByTestId("cockpit-module-chart-expense_structure")).toBeVisible();
    expect(screen.getAllByText("1,476.00 百万元").length).toBeGreaterThan(0);
  });
});
