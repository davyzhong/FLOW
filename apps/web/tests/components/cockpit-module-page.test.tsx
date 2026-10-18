import { fireEvent, render, screen, within } from "@testing-library/react";
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
      unit: "ratio",
      periods: ["FY2022", "FY2023"],
      series: { 资产负债率: ["0.7713", "0.6319"] },
      analysis_question: "资产负债率在报告期之间如何变化？",
      fact_classes: ["reported", "derived"],
      source_ids: ["r1", "r2"],
      metric_codes: ["bs.total_liab", "bs.total_assets"],
      snapshot_id: "snap-1",
      drilldown_target: "/statements?report=r1#stmt-row-合并资产负债表-负债合计",
      empty_reason: null,
      fact_ids: {
        FY2022: "CN-SEG-FY2022-SEGMENT_REVENUE",
        FY2023: "CN-SEG-FY2023-SEGMENT_REVENUE",
      },
      note: "有息负债率需短债拆分，未披露 → unavailable",
    },
    unavailable_trend: {
      title: "未披露趋势",
      type: "line",
      unit: "百万元",
      periods: [],
      series: {},
      analysis_question: "当前是否存在可比较的来源事实？",
      fact_classes: ["reported"],
      snapshot_id: "snap-1",
      empty_reason: "原始财报未披露月度明细，无法形成趋势。",
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
    expect(within(screen.getAllByTestId("module-kpi")[0]).getByText(/前期/)).toHaveTextContent(
      "前期 FY2022 58,881.09 百万元",
    );
    expect(screen.getAllByRole("link", { name: "查看 FY2022 来源财报" }).length).toBe(2);
    for (const link of screen.getAllByRole("link", { name: "查看 FY2022 来源财报" })) {
      expect(link).toHaveAttribute("href", "/statements?report=r2");
    }
    for (const link of screen.getAllByRole("link", { name: "查看 FY2023 来源财报" })) {
      expect(link).toHaveAttribute("href", "/statements?report=r1");
    }
    expect(screen.getAllByText("资本结构趋势").length).toBeGreaterThan(0);
    expect(screen.getByText("FY2022 / FY2023 · %")).toBeVisible();
    expect(screen.getByText("分析问题：资产负债率在报告期之间如何变化？")).toBeVisible();
    expect(screen.getByText("计算指标")).toBeVisible();
    fireEvent.click(screen.getByText("查看图表来源与指标口径"));
    expect(screen.getByRole("link", { name: "bs.total_liab" })).toHaveAttribute(
      "href", "/metric-library?focus=bs.total_liab",
    );
    expect(screen.getByRole("link", { name: "bs.total_assets" })).toHaveAttribute(
      "href", "/metric-library?focus=bs.total_assets",
    );
    expect(
      screen.getAllByRole("link").find(
        (link) => link.getAttribute("href") === "/statements?report=r1#stmt-row-合并资产负债表-负债合计",
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("cockpit-module-chart-capital_structure_trend")).toBeVisible();
    expect(screen.getByText("原始财报未披露月度明细，无法形成趋势。")).toBeVisible();
    fireEvent.click(screen.getByText("查看来源登记事实 ID"));
    expect(screen.getByText("FY2023 · CN-SEG-FY2023-SEGMENT_REVENUE")).toBeVisible();
    expect(screen.getByText("来源登记：config/damai/source_facts_v1.yaml")).toBeVisible();
    expect(screen.getByText("债务期限结构")).toBeVisible();
    expect(screen.getByText(/大麦物流演示主体引用/)).toBeVisible();
    expect(fetchSpy).toHaveBeenCalledOnce();
  });
});


describe("费用图表 API 形态", () => {
  it("KPI 标明比较期间、只表达变化方向并提供指标口径深链", async () => {
    vi.spyOn(client.flowApi, "getCockpitModule").mockResolvedValue({
      ...moduleFixture,
      kpis: [{
        name: "现金比率",
        status: "available",
        value: "0.5000",
        prior_value: "0.5000",
        unit: "ratio",
        caliber_note: null,
      }],
    });

    render(<CockpitModulePage moduleId="balance-sheet" title="资产负债" />);
    const kpi = (await screen.findByText("现金比率")).closest("li");
    expect(kpi).not.toBeNull();
    expect(within(kpi as HTMLElement).getByText(/前期/)).toHaveTextContent(
      "前期 FY2022 0.50 倍",
    );
    expect(screen.getByText("较 FY2022 持平 0.00%（0.00 倍）")).toHaveAttribute(
      "data-direction",
      "flat",
    );
    expect(screen.getByRole("link", { name: "查看指标口径" })).toHaveAttribute(
      "href",
      "/metric-library?focus=cash_ratio",
    );
  });

  it("将 DSO、DIO、DPO 与 CCC 分别链接到正确指标定义", async () => {
    vi.spyOn(client.flowApi, "getCockpitModule").mockResolvedValue({
      ...moduleFixture,
      module: "working-capital",
      kpis: [
        ["DSO", "dso_days"],
        ["DIO", "dio_days"],
        ["DPO", "dpo_days"],
        ["CCC", "ccc_days"],
      ].map(([name]) => ({
        name,
        status: "available",
        value: "30.0000",
        unit: "day",
        caliber_note: null,
      })),
    } as CockpitModuleResponse);

    render(<CockpitModulePage moduleId="working-capital" title="营运资金" />);
    await screen.findByText("DSO");
    for (const code of ["dso_days", "dio_days", "dpo_days", "ccc_days"]) {
      const link = screen.getAllByRole("link", { name: "查看指标口径" }).find(
        (candidate) => candidate.getAttribute("href") === `/metric-library?focus=${code}`,
      );
      expect(link).toHaveAttribute("href", `/metric-library?focus=${code}`);
    }
  });

  it("不为无法确认指标口径的名称生成猜测链接", async () => {
    vi.spyOn(client.flowApi, "getCockpitModule").mockResolvedValue({
      ...moduleFixture,
      kpis: [{
        name: "客户数",
        status: "available",
        value: "1200",
        unit: "人",
        caliber_note: null,
      }],
    });

    render(<CockpitModulePage moduleId="working-capital" title="营运资金" />);
    const kpi = (await screen.findByText("客户数")).closest("li");
    expect(kpi).not.toBeNull();
    expect(within(kpi as HTMLElement).queryByRole("link", { name: "查看指标口径" })).toBeNull();
    expect(within(kpi as HTMLElement).getByRole("link", { name: "查看 FY2023 来源财报" })).toHaveAttribute(
      "href",
      "/statements?report=r1",
    );
  });

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
          periods: [],
          series: { 销售: "1476.0000", 管理: "738.0000", 研发: "210.0000", 财务: "83.0000" },
          analysis_question: "当期各项期间费用如何构成？",
          fact_classes: ["reported"],
          source_ids: ["r1", "r2"],
          metric_codes: ["selling_expense", "admin_expense", "rnd_expense", "financial_expense"],
          snapshot_id: "snap-1",
          drilldown_target: "/statements?report=r1",
          empty_reason: null,
        },
      },
    } as CockpitModuleResponse);

    render(<CockpitModulePage moduleId="expenses" title="费用分析" />);
    expect(await screen.findByTestId("cockpit-module-chart-expense_structure")).toBeVisible();
    expect(within(screen.getByRole("table")).getByRole("columnheader", { name: "FY2023" })).toBeVisible();
    expect(screen.getAllByText("1,476.00 百万元").length).toBeGreaterThan(0);
  });
});
