"use client";

/**
 * S01 CFO 驾驶舱 · 图表构建器（批次 C-1）
 *
 * 每个构建器是**纯函数**：数据（contracts 类型）→ EChartsOption。
 * 不含副作用、不含数据获取，便于单测与快照。
 *
 * 通用不变量（全图表遵守）：
 * - unavailable 序列不画线、不补零（返回 undefined 让 ChartBox 显示空态）
 * - 管控线用 markLine 显式标注数值，不只靠颜色
 * - tooltip 一律带单位
 * - 颜色语义固定：蓝=本期/主指标，绿=改善，红=恶化，黄=警示，灰=未就绪
 */

import type { EChartsOption } from "echarts";

import { AXIS, CHART_THEME, TOOLTIP, legend } from "./echarts-base";

/**
 * ECharts 的 TS 联合类型对回调签名与 series 形状要求极严；构建器产出的是
 * 已由单测逐条断言的运行时结构。此处统一按 CoreOption 收口（等价于 EChartsOption
 * 的宽松侧），避免 10 个构建器各自散落 `as unknown as` 断言。
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type ChartOption = NonNullable<EChartsOption extends infer _O ? Record<string, unknown> : never>;

// ── 1. 柱线双轴组合（收入/利润/现金流趋势） ────────────────────────────

export interface ComboSeries {
  key: string;
  title: string;
  axis: "bar" | "line";
  points: { period: string; value: number; display: string; status: string }[];
  unit: string;
}

export function buildCombo(series: ComboSeries[]): ChartOption | undefined {
  const usable = series.filter((s) => s.points.some((p) => p.status === "ready"));
  if (usable.length === 0) return undefined;
  const periods = usable[0].points.map((p) => p.period);
  return {
    tooltip: { ...TOOLTIP, axisPointer: { type: "cross" } },
    legend: legend(usable.map((s) => `${s.title}（${s.unit}）`)),
    grid: { left: 56, right: usable.some((s) => s.axis === "line") ? 56 : 20, top: 34, bottom: 30 },
    xAxis: { type: "category", data: periods, ...AXIS },
    yAxis:
      usable.some((s) => s.axis === "line") && usable.some((s) => s.axis === "bar")
        ? [
            { type: "value", name: usable.find((s) => s.axis === "bar")?.unit ?? "", ...AXIS },
            {
              type: "value",
              name: usable.find((s) => s.axis === "line")?.unit ?? "",
              ...AXIS,
              splitLine: { show: false },
            },
          ]
        : { type: "value", ...AXIS },
    series: usable.map((s, i) => {
      const isLine = s.axis === "line";
      const yAxisIndex = isLine && usable.some((x) => x.axis === "bar") ? 1 : 0;
      const color = [CHART_THEME.blue, CHART_THEME.green, CHART_THEME.warn][i % 3];
      return {
        name: `${s.title}（${s.unit}）`,
        type: s.axis,
        yAxisIndex,
        data: s.points.map((p) => (p.status === "ready" ? p.value : null)),
        itemStyle: { color },
        lineStyle: isLine ? { width: 2.4, color } : undefined,
        areaStyle: isLine ? { color: `${color}14` } : undefined,
        symbolSize: 6,
        connectNulls: false,
        barMaxWidth: 26,
      };
    }),
  };
}

// ── 2. 四象限散点（经营单元矩阵：收入达成 × 净利率） ────────────────────

export interface QuadrantPoint {
  name: string;
  x: number;
  y: number;
  size: number;
  risk: "ok" | "attention" | "risk";
  detail: string;
}

export function buildQuadrant(
  points: QuadrantPoint[],
  opts: { xName: string; yName: string; vLine: number; hLine: number; xUnit?: string; yUnit?: string },
): ChartOption | undefined {
  if (points.length === 0) return undefined;
  const color = (r: QuadrantPoint["risk"]) =>
    r === "risk" ? CHART_THEME.red : r === "attention" ? CHART_THEME.warn : CHART_THEME.green;
  return {
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: unknown) => {
        const d = (p as { data?: QuadrantPoint[] })?.data?.[0];
        return d ? `${d.name}<br>${d.detail}` : "";
      },
    },
    grid: { left: 56, right: 24, top: 20, bottom: 40 },
    xAxis: {
      type: "value",
      name: opts.xName + (opts.xUnit ? `（${opts.xUnit}）` : ""),
      nameTextStyle: { color: CHART_THEME.mut, fontSize: 10 },
      ...AXIS,
    },
    yAxis: {
      type: "value",
      name: opts.yName + (opts.yUnit ? `（${opts.yUnit}）` : ""),
      nameTextStyle: { color: CHART_THEME.mut, fontSize: 10 },
      ...AXIS,
    },
    series: [
      {
        type: "scatter",
        data: points.map((p) => ({ value: [p.x, p.y], ...p, itemStyle: { color: color(p.risk) } })),
        symbolSize: (v: number[]) => Math.max(10, Math.min(38, (v[2] ?? 10) / 6)),
        label: {
          show: true,
          formatter: (p: { data?: { name?: string } }) => p.data?.name ?? "",
          position: "top",
          fontSize: 10.5,
          color: CHART_THEME.ink,
        },
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { type: "dashed", color: CHART_THEME.gray },
          data: [
            { xAxis: opts.vLine, label: { formatter: `关注线 ${opts.vLine}`, fontSize: 9, color: CHART_THEME.gray } },
            { yAxis: opts.hLine, label: { formatter: `均值 ${opts.hLine}`, fontSize: 9, color: CHART_THEME.gray } },
          ],
        },
      },
    ],
  };
}

// ── 3. 差异桥瀑布（含守恒核对块） ────────────────────────────────────

export interface WaterfallStep {
  label: string;
  /** 绝对值（总额）或增量（中间项） */
  value: number;
  kind: "total" | "up" | "down";
}

export function buildWaterfall(
  steps: WaterfallStep[],
  unit: string,
  opts: { checkLine?: string } = {},
): ChartOption | undefined {
  if (steps.length === 0) return undefined;
  // 计算堆叠基线：total 从 0 起；up/down 从前累计起
  const base: number[] = [];
  const delta: number[] = [];
  let acc = 0;
  for (const s of steps) {
    if (s.kind === "total") {
      base.push(0);
      delta.push(s.value);
      acc = s.value;
    } else {
      base.push(s.value >= 0 ? acc : acc + s.value);
      delta.push(Math.abs(s.value));
      acc += s.value;
    }
  }
  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (ps: { name: string; dataIndex: number }[]) => {
        const i = ps[0].dataIndex;
        const s = steps[i];
        const sign = s.kind === "down" ? "−" : s.kind === "up" ? "+" : "";
        return `${s.label}<br>${sign}${Math.abs(s.value).toLocaleString()} ${unit}`;
      },
    },
    grid: { left: 58, right: 20, top: 20, bottom: opts.checkLine ? 44 : 30 },
    xAxis: { type: "category", data: steps.map((s) => s.label), ...AXIS, axisLabel: { ...AXIS.axisLabel, interval: 0, fontSize: 10 } },
    yAxis: { type: "value", name: unit, ...AXIS },
    series: [
      { type: "bar", stack: "w", itemStyle: { color: "transparent" }, data: base, barMaxWidth: 44 },
      {
        type: "bar",
        stack: "w",
        barMaxWidth: 44,
        data: delta.map((v, i) => ({
          value: v,
          itemStyle: {
            color:
              steps[i].kind === "total"
                ? CHART_THEME.blue
                : steps[i].kind === "up"
                  ? CHART_THEME.green
                  : CHART_THEME.red,
            borderRadius: steps[i].kind === "total" ? ([3, 3, 0, 0] as [number, number, number, number]) : ([2, 2, 2, 2] as [number, number, number, number]),
          },
        })),
        label: {
          show: true,
          position: "top",
          fontSize: 10,
          color: CHART_THEME.ink,
          formatter: (p: { dataIndex: number }) => {
            const s = steps[p.dataIndex];
            const sign = s.kind === "down" ? "−" : s.kind === "up" ? "+" : "";
            return `${sign}${Math.abs(s.value).toLocaleString()}`;
          },
        },
      },
    ],
  };
}

// ── 4. 仪表盘（带管控线，偿债能力） ────────────────────────────────────

export interface GaugeSpec {
  title: string;
  value: number;
  max: number;
  /** 管控线；higherIsWorse=true 表示越低越好 */
  controlLine: number;
  unit: string;
  higherIsWorse: boolean;
}

export function buildGauges(specs: GaugeSpec[]): ChartOption | undefined {
  if (specs.length === 0) return undefined;
  return {
    series: specs.map((s, i) => {
      // higherIsWorse（越低越好，如资产负债率）：value > line 为 breach
      // higherIsWorse=false（越高越好，如流动比率）：value < line 为 breach
      // 「接近」= 距管控线 20% 以内（与控制线同侧），不跨过
      const breach = s.higherIsWorse ? s.value > s.controlLine : s.value < s.controlLine;
      // 「接近」= 与管控线的相对距离在 20% 以内（安全侧或危险侧都算接近）
      const distance = Math.abs(s.value - s.controlLine) / (s.controlLine || 1);
      const near = distance <= 0.2;
      const color = breach ? CHART_THEME.red : near ? CHART_THEME.warn : CHART_THEME.green;
      return {
        type: "gauge",
        center: [`${(i * 100) / specs.length + 50 / specs.length}%`, "58%"],
        radius: "74%",
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: s.max,
        axisLine: {
          lineStyle: {
            width: 10,
            color: [
              [s.controlLine / s.max, CHART_THEME.line],
              [1, `${color}22`],
            ] as [number, string][],
          },
        },
        pointer: { length: "58%", width: 4, itemStyle: { color } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          distance: -2,
          fontSize: 8,
          color: CHART_THEME.gray,
          formatter: (v: number) => (v % (s.max / 4) === 0 ? v : ""),
        },
        title: { offsetCenter: [0, "64%"], fontSize: 10.5, color: CHART_THEME.mut },
        detail: {
          offsetCenter: [0, "94%"],
          fontSize: 14,
          fontWeight: 700,
          color: CHART_THEME.ink,
          formatter: (v: number) => `${v}${s.unit}`,
        },
        data: [{ value: s.value, name: `${s.title}｜管控线 ${s.controlLine}${s.unit}` }],
      };
    }),
  };
}

// ── 5. 环形/玫瑰（结构占比） ────────────────────────────────────────────

export interface Slice {
  name: string;
  value: number;
  color?: string;
}

export function buildDonut(slices: Slice[], unit: string, rose = false): ChartOption | undefined {
  const usable = slices.filter((s) => Number.isFinite(s.value) && s.value > 0);
  if (usable.length === 0) return undefined;
  const palette = [CHART_THEME.blue, CHART_THEME.teal, CHART_THEME.purple, CHART_THEME.gold, CHART_THEME.ltblue];
  return {
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: { name: string; value: number; percent: number }) =>
        `${p.name}<br>${p.value.toLocaleString()} ${unit}（${p.percent}%）`,
    },
    series: [
      {
        type: "pie",
        ...(rose ? { roseType: "radius" as const } : {}),
        radius: rose ? ["28%", "72%"] : ["48%", "72%"],
        center: ["50%", "54%"],
        avoidLabelOverlap: true,
        label: {
          show: true,
          position: "outside",
          fontSize: 10.5,
          color: CHART_THEME.ink,
          formatter: "{b}\n{d}%",
        },
        labelLine: { length: 10, length2: 10 },
        data: usable.map((s, i) => ({
          name: s.name,
          value: s.value,
          itemStyle: { color: s.color ?? palette[i % palette.length] },
        })),
      },
    ],
  };
}

// ── 6. 雷达（行业基准 / 质量对比） ─────────────────────────────────────

export interface RadarSeries {
  name: string;
  values: number[];
  dashed?: boolean;
}

export function buildRadar(indicators: string[], series: RadarSeries[], max = 100): ChartOption | undefined {
  if (indicators.length === 0 || series.length === 0) return undefined;
  const colors = [CHART_THEME.blue, CHART_THEME.gold, CHART_THEME.teal];
  return {
    tooltip: {},
    legend: legend(series.map((s) => s.name)),
    radar: {
      indicator: indicators.map((name) => ({ name, max })),
      radius: "62%",
      axisName: { color: CHART_THEME.mut, fontSize: 10.5 },
      splitLine: { lineStyle: { color: CHART_THEME.line } },
      splitArea: { show: false },
    },
    series: [
      {
        type: "radar",
        data: series.map((s, i) => ({
          value: s.values,
          name: s.name,
          itemStyle: { color: colors[i % colors.length] },
          lineStyle: { width: s.dashed ? 1.5 : 2.2, type: s.dashed ? "dashed" : "solid" },
          areaStyle: s.dashed ? { color: `${colors[i % colors.length]}14` } : { color: `${colors[i % colors.length]}33` },
        })),
      },
    ],
  };
}

// ── 7. 热力（风险维度 / 覆盖度） ──────────────────────────────────────

export function buildHeatmap(
  cells: { x: string; y: string; value: number; extra?: string }[],
  opts: { thresholds?: number[]; suffix?: string } = {},
): ChartOption | undefined {
  if (cells.length === 0) return undefined;
  const xs = [...new Set(cells.map((c) => c.x))];
  const ys = [...new Set(cells.map((c) => c.y))];
  return {
    tooltip: {
      position: "top",
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: { value: [number, number, number] }) => {
        const c = cells.find((x) => x.x === xs[p.value[0]] && x.y === ys[p.value[1]]);
        return c ? `${c.y} · ${c.x}<br>${c.value}${opts.suffix ?? ""}${c.extra ? `<br>${c.extra}` : ""}` : "";
      },
    },
    grid: { left: 14, right: 14, top: 10, bottom: opts.thresholds ? 26 : 12 },
    xAxis: { type: "category", data: xs, ...AXIS, splitArea: { show: true, areaStyle: { color: ["#fff", "#fafafa"] } } },
    yAxis: { type: "category", data: ys, ...AXIS, splitArea: { show: true, areaStyle: { color: ["#fff", "#fafafa"] } } },
    visualMap: {
      show: !!opts.thresholds?.length,
      min: 0,
      max: 100,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      itemWidth: 9,
      itemHeight: 80,
      textStyle: { fontSize: 9 },
      inRange: { color: ["#dcfce7", "#fef3c7", "#fee2e2"] },
    },
    series: [
      {
        type: "heatmap",
        data: cells.map((c) => [xs.indexOf(c.x), ys.indexOf(c.y), c.value]),
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        label: { show: true, fontSize: 11, fontWeight: 700, color: CHART_THEME.ink, formatter: (p: { value: [number, number, number] }) => String(p.value[2]) },
        emphasis: { itemStyle: { shadowBlur: 6 } },
      },
    ],
  };
}

// ── 8. 杜邦分解树（ECharts graph） ────────────────────────────────────

export interface DupontNode {
  name: string;
  x: number;
  y: number;
  symbolSize: number;
  color: string;
  formula: string;
}

export function buildDupont(
  root: DupontNode,
  branches: { node: DupontNode; children: DupontNode[] }[],
): ChartOption | undefined {
  const data = [root, ...branches.map((b) => b.node), ...branches.flatMap((b) => b.children)];
  const links = [
    ...branches.map((b) => ({ source: root.name, target: b.node.name })),
    ...branches.flatMap((b) => b.children.map((c) => ({ source: b.node.name, target: c.name }))),
  ];
  return {
    tooltip: {
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: { data?: { formula?: string } }) => p.data?.formula ?? "",
    },
    series: [
      {
        type: "graph",
        layout: "none",
        roam: false,
        left: 24,
        right: 24,
        top: 12,
        bottom: 12,
        data: data.map((n) => ({
          name: n.name,
          x: n.x,
          y: n.y,
          symbolSize: n.symbolSize,
          itemStyle: { color: n.color },
          formula: n.formula,
        })),
        links,
        edgeSymbol: ["none", "arrow"],
        edgeSymbolSize: [0, 6],
        lineStyle: { color: CHART_THEME.mut, width: 1.4, curveness: 0.06, opacity: 0.85 },
        label: { show: true, position: "inside", fontSize: 9.5, color: "#fff", fontWeight: 600, lineHeight: 12 },
        emphasis: { scale: 1.05 },
      },
    ],
  };
}

// ── 9. 排名横条 ──────────────────────────────────────────────────────

export function buildRankBar(
  rows: { name: string; value: number; display: string; emphasis?: boolean }[],
  unit: string,
): ChartOption | undefined {
  const usable = rows.filter((r) => Number.isFinite(r.value));
  if (usable.length === 0) return undefined;
  const sorted = [...usable].sort((a, b) => a.value - b.value);
  return {
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: { name: string; value: number }) => `${p.name}<br>${p.value.toLocaleString()} ${unit}`,
    },
    grid: { left: 96, right: 60, top: 12, bottom: 20 },
    xAxis: { type: "value", ...AXIS },
    yAxis: { type: "category", data: sorted.map((r) => r.name), ...AXIS, axisLabel: { ...AXIS.axisLabel, interval: 0, fontSize: 10.5 } },
    series: [
      {
        type: "bar",
        barMaxWidth: 16,
        data: sorted.map((r) => ({
          value: r.value,
          itemStyle: {
            color: r.emphasis ? CHART_THEME.warn : CHART_THEME.blue,
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: { show: true, position: "right", fontSize: 10.5, color: CHART_THEME.ink, formatter: (p: { dataIndex: number }) => sorted[p.dataIndex].display },
      },
    ],
  };
}

// ── 10. 应收账龄分段条 ────────────────────────────────────────────────

export function buildAgingBars(segs: { label: string; pct: number; days?: string }[]): ChartOption | undefined {
  const usable = segs.filter((s) => Number.isFinite(s.pct) && s.pct >= 0);
  if (usable.length === 0 || usable.every((s) => s.pct === 0)) return undefined;
  const colors = [CHART_THEME.green, CHART_THEME.gold, CHART_THEME.warn, CHART_THEME.red];
  return {
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,.97)",
      borderColor: CHART_THEME.line,
      textStyle: { color: CHART_THEME.ink, fontSize: 12 },
      formatter: (p: { name: string; value: number }) => `${p.name}<br>${p.value}%${segs[usable.indexOf(p as never)]?.days ? `（约 ${segs[usable.indexOf(p as never)].days} 天）` : ""}`,
    },
    grid: { left: 110, right: 56, top: 12, bottom: 20 },
    xAxis: { ...AXIS, type: "value", max: 100, axisLabel: { ...AXIS.axisLabel, formatter: "{value}%" } },
    yAxis: { ...AXIS, type: "category", data: usable.map((s) => s.label), axisLabel: { ...AXIS.axisLabel, interval: 0, fontSize: 10.5 } },
    series: [
      {
        type: "bar",
        barMaxWidth: 16,
        data: usable.map((s, i) => ({ value: s.pct, itemStyle: { color: colors[i % colors.length], borderRadius: [0, 4, 4, 0] } })),
        label: { show: true, position: "right", fontSize: 10.5, color: CHART_THEME.ink, formatter: "{c}%" },
      },
    ],
  };
}
