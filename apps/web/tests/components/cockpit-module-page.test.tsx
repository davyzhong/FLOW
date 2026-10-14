import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
  it("渲染 KPI 网格、图表数据表与不可用块", async () => {
    const fetchSpy = vi
      .spyOn(client.flowApi, "getCockpitModule")
      .mockResolvedValue(moduleFixture);
    render(<CockpitModulePage moduleId="balance-sheet" title="资产负债" />);
    expect(await screen.findByText("71,850.9 百万元")).toBeVisible();
    expect(screen.getByText("前期 58,881.1 百万元")).toBeVisible();
    expect(screen.getByText("资本结构趋势")).toBeVisible();
    expect(screen.getByText("债务期限结构")).toBeVisible();
    expect(screen.getByText(/大麦物流演示主体引用/)).toBeVisible();
    expect(fetchSpy).toHaveBeenCalledOnce();
  });
});
