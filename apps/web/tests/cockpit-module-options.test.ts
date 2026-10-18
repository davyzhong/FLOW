import { describe, expect, it } from "vitest";

import { buildModuleChartOption, normalizeModuleSeries } from "../components/cockpit/charts/module-options";

describe("模块图表数据适配", () => {
  it("接受费用接口返回的标量系列并生成结构图", () => {
    const option = buildModuleChartOption({
      type: "ratio_bar",
      unit: "百万元",
      series: { 销售: "1476.0000", 管理: "738.0000", 研发: null },
    }, "百万元") as { series: { type: string; data: { name: string; value: number }[] }[] };
    expect(option.series[0].type).toBe("pie");
    expect(option.series[0].data).toMatchObject([
      { name: "销售", value: 1476 },
      { name: "管理", value: 738 },
    ]);
  });

  it("单期分类柱图复用排名横条构建器并保留分类值", () => {
    const option = buildModuleChartOption({
      type: "bar",
      unit: "百万元",
      series: { 经营活动: "120.5", 投资活动: "-30.2" },
    }, "百万元") as { series: { type: string; data: { value: number }[] }[]; yAxis: { data: string[] } };
    expect(option.series[0].type).toBe("bar");
    expect(option.yAxis.data).toEqual(["投资活动", "经营活动"]);
    expect(option.series[0].data.map((item) => item.value)).toEqual([-30.2, 120.5]);
  });

  it("比例趋势按百分比展示并保留期间空值", () => {
    const option = buildModuleChartOption({
      type: "line",
      unit: "ratio",
      periods: ["FY2022", "FY2023"],
      series: { 资产负债率: ["0.6286", null] },
    }, "百万元") as { series: { data: (number | null)[] }[] };
    expect(option.series[0].data).toEqual([62.86, null]);
  });

  it("表格适配器同时接受列表、标量与缺失值", () => {
    expect(normalizeModuleSeries(["1", null])).toEqual(["1", null]);
    expect(normalizeModuleSeries("1")).toEqual(["1"]);
    expect(normalizeModuleSeries(null)).toEqual([]);
  });
});
