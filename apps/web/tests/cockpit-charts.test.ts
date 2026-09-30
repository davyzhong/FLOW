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

const ready = (period: string, value: number, display = String(value)) => ({
  period,
  value,
  display,
  status: "ready",
});
const missing = (period: string) => ({ period, value: 0, display: "—", status: "unavailable" });

describe("chart builders", () => {
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
    expect(opt.series[0].pointer.itemStyle.color).toBe("#dc2626");
  });

  it("gauge: 越低越好指标明显低于管控线为绿（距线>20%）", () => {
    const opt = buildGauges([
      { title: "资产负债率", value: 30, max: 100, controlLine: 60, unit: "%", higherIsWorse: true },
    ]) as { series: { pointer: { itemStyle: { color: string } } }[] };
    expect(opt.series[0].pointer.itemStyle.color).toBe("#16a34a");
  });

  it("gauge: 越低越好指标贴近管控线为黄（距线<=20%）", () => {
    const opt = buildGauges([
      { title: "资产负债率", value: 50, max: 100, controlLine: 60, unit: "%", higherIsWorse: true },
    ]) as { series: { pointer: { itemStyle: { color: string } } }[] };
    expect(opt.series[0].pointer.itemStyle.color).toBe("#d97706");
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
