import { describe, expect, it } from "vitest";

import {
  buildAgingBars,
  buildCombo,
  buildDonut,
  buildDupont,
  buildGauges,
  buildHeatmap,
  buildQuadrant,
  buildRadar,
  buildRankBar,
  buildWaterfall,
} from "../components/cockpit/charts/builders";
import { EXPENSE_CATEGORY_COLORS, SERIES_PALETTE } from "../components/cockpit/charts/echarts-base";
import { buildModuleChartOption } from "../components/cockpit/charts/module-options";

const ready = (period: string, value: number, display = String(value)) => ({
  period,
  value,
  display,
  status: "ready",
});
const missing = (period: string) => ({ period, value: 0, display: "—", status: "unavailable" });

describe("chart builders", () => {
  it("费用环图与年度柱图使用相同分类色，第四系列为概念板中性灰", () => {
    const series = { 销售: 12, 管理: 55, 研发: 23, 财务: 10 };
    const donut = buildModuleChartOption({ type: "ratio_bar", unit: "百万元", series }, "百万元") as {
      series: { data: { name: string; itemStyle: { color: string } }[] }[];
    };
    const bars = buildModuleChartOption({ type: "bar", unit: "百万元", periods: ["FY2023"], series: Object.fromEntries(Object.entries(series).map(([name, value]) => [name, [value]])) }, "百万元") as {
      series: { name: string; itemStyle: { color: string } }[];
    };
    expect(donut.series[0].data.map(({ name, itemStyle }) => [name, itemStyle.color])).toEqual(Object.entries(EXPENSE_CATEGORY_COLORS));
    expect(bars.series.map(({ name, itemStyle }) => [name.replace("（百万元）", ""), itemStyle.color])).toEqual(Object.entries(EXPENSE_CATEGORY_COLORS));
    expect(SERIES_PALETTE[3]).toBe("#9BA6A4");
  });

  // ── 不补零铁律 ──────────────────────────────────────────────
  it("combo: 全部不可用时返回 undefined（不画假线）", () => {
    const opt = buildCombo([
      { key: "revenue", title: "营业收入", axis: "bar", unit: "万元", points: [missing("2026-01")] },
    ]);
    expect(opt).toBeUndefined();
  });

  it("combo: 部分不可用时置 null 且不连接（不补零）", () => {
    const opt = buildCombo([
      {
        key: "revenue",
        title: "营业收入",
        axis: "bar",
        unit: "万元",
        points: [ready("2026-01", 10), missing("2026-02")],
      },
    ]) as { series: { data: (number | null)[] }[] };
    expect(opt.series[0].data).toEqual([10, null]);
  });

  it("combo: bar + line 时使用双 Y 轴", () => {
    const opt = buildCombo([
      { key: "rev", title: "收入", axis: "bar", unit: "万元", points: [ready("2026-01", 10)] },
      { key: "rate", title: "毛利率", axis: "line", unit: "%", points: [ready("2026-01", 30)] },
    ]) as { yAxis: unknown[] };
    expect(Array.isArray(opt.yAxis)).toBe(true);
  });

  it("combo: 可复用同一类别的堆叠柱序列", () => {
    const opt = buildCombo([
      { key: "selling", title: "销售", axis: "bar", stack: "expenses", color: "#123456", unit: "百万元", points: [ready("FY2022", 20), ready("FY2023", 25)] },
      { key: "admin", title: "管理", axis: "bar", stack: "expenses", color: "#654321", unit: "百万元", points: [ready("FY2022", 12), ready("FY2023", 14)] },
    ]) as { series: { stack?: string; data: number[]; itemStyle: { color: string } }[] };

    expect(opt.series.map((item) => item.stack)).toEqual(["expenses", "expenses"]);
    expect(opt.series.map((item) => item.data)).toEqual([[20, 25], [12, 14]]);
    expect(opt.series.map((item) => item.itemStyle.color)).toEqual(["#123456", "#654321"]);
  });

  it("combo: 同单位但数量级悬殊的两条线可显式使用独立刻度", () => {
    const opt = buildCombo([
      { key: "revenue", title: "营业收入", axis: "line", unit: "亿元", points: [ready("FY2023", 176)] },
      { key: "profit", title: "营业利润", axis: "line", unit: "亿元", secondaryAxis: true, points: [ready("FY2023", -3)] },
    ]) as { yAxis: unknown[]; series: { yAxisIndex: number }[] };
    expect(opt.yAxis).toHaveLength(2);
    expect(opt.series.map((item) => item.yAxisIndex)).toEqual([0, 1]);
  });

  it("combo: 计数单位使用整数刻度，不把小数刻度格式化成重复整数", () => {
    const opt = buildCombo([
      { key: "batches", title: "批次数量", axis: "bar", unit: "个", points: [ready("已发布", 1)] },
    ]) as { yAxis: { minInterval?: number } };
    expect(opt.yAxis.minInterval).toBe(1);
  });

  it("donut: 零值分片被剔除（全 0 返回 undefined）", () => {
    expect(buildDonut([{ name: "A", value: 0 }], "万元")).toBeUndefined();
    const opt = buildDonut([{ name: "A", value: 0 }, { name: "B", value: 5 }], "万元") as {
      series: { data: { name: string }[] }[];
    };
    expect(opt.series[0].data.map((d) => d.name)).toEqual(["B"]);
  });

  it("gauge: 突破管控线时指针为红", () => {
    const opt = buildGauges([
      { title: "资产负债率", value: 70, max: 100, controlLine: 60, unit: "%", higherIsWorse: true },
    ]) as { series: { pointer: { itemStyle: { color: string } } }[] };
    expect(opt.series[0].pointer.itemStyle.color).toBe("#B1483E");
  });

  it("gauge: 越低越好指标明显低于管控线为绿（距线>20%）", () => {
    const opt = buildGauges([
      { title: "资产负债率", value: 30, max: 100, controlLine: 60, unit: "%", higherIsWorse: true },
    ]) as { series: { pointer: { itemStyle: { color: string } } }[] };
    expect(opt.series[0].pointer.itemStyle.color).toBe("#286048");
  });

  it("gauge: 越低越好指标贴近管控线为黄（距线<=20%）", () => {
    const opt = buildGauges([
      { title: "资产负债率", value: 50, max: 100, controlLine: 60, unit: "%", higherIsWorse: true },
    ]) as { series: { pointer: { itemStyle: { color: string } } }[] };
    expect(opt.series[0].pointer.itemStyle.color).toBe("#805415");
  });

  it("gauge: 空输入返回 undefined", () => {
    expect(buildGauges([])).toBeUndefined();
  });

  it("waterfall: total 从 0 起、增量按方向堆叠", () => {
    const opt = buildWaterfall(
      [
        { label: "预算净利", value: 100, kind: "total" },
        { label: "收入影响", value: 20, kind: "up" },
        { label: "费用影响", value: -30, kind: "down" },
        { label: "实际净利", value: 90, kind: "total" },
      ],
      "万元",
    ) as { series: { data: (number | { value: number })[] }[] };
    // base: [0, 100, 90, 0]；delta: [100, 20, 30, 90]
    expect(opt.series[0].data).toEqual([0, 100, 90, 0]);
    expect(opt.series[1].data.map((d: number | { value: number }) => (typeof d === "number" ? d : d.value))).toEqual([100, 20, 30, 90]);
  });

  it("waterfall: 算术减少使用中性色，负向结果才使用语义红", () => {
    const opt = buildWaterfall([
      { label: "期初", value: 20, kind: "total" },
      { label: "期间减少", value: -40, kind: "down" },
      { label: "期末", value: -20, kind: "total" },
    ], "万元") as { series: { data: { itemStyle: { color: string } }[] }[] };
    expect(opt.series[1].data.map((item) => item.itemStyle.color)).toEqual(["#1F4D70", "#9BA6A4", "#B1483E"]);
  });

  it("quadrant: 气泡大小按 size 缩放并夹在 10–38", () => {
    const opt = buildQuadrant(
      [{ name: "制造A", x: 100, y: 12, size: 6, risk: "ok", detail: "d" }],
      { xName: "收入", yName: "净利率", vLine: 90, hLine: 8 },
    ) as { series: { symbolSize: (v: number[]) => number }[] };
    const size = opt.series[0].symbolSize([1, 2, 6]);
    expect(size).toBeGreaterThanOrEqual(10);
    expect(size).toBeLessThanOrEqual(38);
  });

  it("radar: 虚线对比序列保留 dashed 样式", () => {
    const opt = buildRadar(["成长", "盈利"], [{ name: "本主体", values: [80, 60] }, { name: "行业", values: [70, 70], dashed: true }]) as {
      series: { data: { lineStyle: { type: string } }[] }[];
    };
    expect(opt.series[0].data[1].lineStyle.type).toBe("dashed");
  });

  it("heatmap: 无 cell 返回 undefined", () => {
    expect(buildHeatmap([])).toBeUndefined();
  });

  it("dupont: 根节点连到各分支，分支连到叶节点", () => {
    const opt = buildDupont(
      { name: "ROE", x: 50, y: 10, symbolSize: 70, color: "#2563eb", formula: "12.6%" },
      [
        {
          node: { name: "净利率", x: 20, y: 45, symbolSize: 50, color: "#0d9488", formula: "7.6%" },
          children: [{ name: "净利润", x: 10, y: 80, symbolSize: 40, color: "#5eead4", formula: "9674" }],
        },
      ],
    ) as { series: { links: { source: string; target: string }[] }[] };
    expect(opt.series[0].links).toHaveLength(2);
  });

  it("rankBar: 升序排列（越短在上）", () => {
    const opt = buildRankBar(
      [
        { name: "C", value: 30, display: "30" },
        { name: "A", value: 10, display: "10" },
      ],
      "天",
    ) as { yAxis: { data: string[] } };
    expect(opt.yAxis.data).toEqual(["A", "C"]);
  });

  it("agingBars: 全 0 返回 undefined（不画假条）", () => {
    expect(buildAgingBars([{ label: "1月内", pct: 0 }])).toBeUndefined();
  });
});
