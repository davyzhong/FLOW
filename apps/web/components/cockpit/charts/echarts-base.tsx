"use client";

/**
 * S01 CFO 驾驶舱 · ECharts 基座（批次 C-1）
 *
 * 选型依据：用户 2026-09-30 裁决「引入 ECharts」。
 * 实施计划 §6 Q1 结论：复杂图表（仪表盘/热力/杜邦/瀑布/散点）由 ECharts 承担，
 * 简单趋势图同样统一到 ECharts，保证配色/坐标轴/无障碍行为全站一致。
 *
 * 工程约束：
 * - 按需引入（echarts/core + 具体 chart/组件），不做全量 import（避免 bundle 膨胀）
 * - 单一实例复用：同一容器多次渲染不重复 init
 * - 卸载时 dispose，路由切换不泄漏
 * - resize 走 ResizeObserver，不绑 window.resize（避免每图表一个监听）
 * - 主题集中在 CHART_THEME，语义色与 cockpit.css 保持一致
 */

import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, GaugeChart, HeatmapChart, LineChart, PieChart, RadarChart, ScatterChart, TreemapChart } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  RadarChart,
  GaugeChart,
  HeatmapChart,
  TreemapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  MarkLineComponent,
  MarkPointComponent,
  DataZoomComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

/** 语义色：与 cockpit.css 的 CSS 变量保持一致（正/负/警示/未就绪） */
export const CHART_THEME = {
  blue: "#2563eb",
  blueSoft: "#93c5fd",
  green: "#16a34a",
  red: "#dc2626",
  warn: "#d97706",
  gold: "#b45309",
  gray: "#b0b0b0",
  ink: "#0f172a",
  mut: "#64748b",
  line: "#e2e8f0",
  teal: "#0d9488",
  purple: "#7c3aed",
  ltblue: "#60a5fa",
} as const;

/** 通用轴配置（保持所有图表的坐标轴行为一致） */
export const AXIS = {
  axisLine: { lineStyle: { color: CHART_THEME.line } },
  axisTick: { show: false },
  axisLabel: { color: CHART_THEME.mut, fontSize: 11 },
  splitLine: { lineStyle: { color: CHART_THEME.line } },
} as const;

export const TOOLTIP = {
  trigger: "axis" as const,
  backgroundColor: "rgba(255,255,255,.97)",
  borderColor: CHART_THEME.line,
  textStyle: { color: CHART_THEME.ink, fontSize: 12 },
} as const;

export function legend(names: string[]) {
  return { data: names, top: 0, right: 0, itemWidth: 10, itemHeight: 8, textStyle: { fontSize: 11, color: CHART_THEME.mut } };
}

/**
 * ECharts 容器 hook：按需初始化、复用实例、自动 resize 与 dispose。
 *
 * @param option 图表配置；传 undefined 时不渲染
 * @param deps   依赖变化时 setOption（避免每次渲染都重建）
 */
export function useEChart(option: EChartsOption | undefined, deps: unknown[] = []) {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!option) return;
    const chart = chartRef.current;
    if (!chart) return;
    chart.setOption(option, { notMerge: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}

/** 通用图表容器：包裹标题 + ECharts 画布 + 无障碍摘要 */
export function ChartBox({
  title,
  sub,
  option,
  deps,
  ariaLabel,
  height = 280,
  testId,
}: {
  title: string;
  sub?: string;
  option: EChartsOption | undefined;
  deps?: unknown[];
  ariaLabel?: string;
  height?: number;
  testId?: string;
}) {
  const ref = useEChart(option, deps ?? [option]);
  const empty = !option;
  return (
    <article className="card chart-card" data-testid={testId}>
      <div className="ct">
        <h3 className="ct">{title}</h3>
        {sub ? <span className="sub">{sub}</span> : null}
      </div>
      {empty ? (
        <div className="chart-empty" style={{ height }}>
          暂无可用数据（不补零）
        </div>
      ) : (
        <div
          ref={ref}
          role="img"
          aria-label={ariaLabel ?? title}
          style={{ width: "100%", height }}
        />
      )}
    </article>
  );
}

export type { EChartsOption };
