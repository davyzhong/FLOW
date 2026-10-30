import type { EChartsOption } from "echarts";

import type { CockpitModuleChart } from "../../../lib/api/client";
import { CHART_THEME, EXPENSE_CATEGORY_COLORS, SERIES_PALETTE } from "./echarts-base";
import { buildCombo, buildDonut, buildRankBar, buildWaterfall } from "./builders";
import { formatFinancialValue } from "../number-format";

export type ModuleChartData = Partial<CockpitModuleChart> & Pick<CockpitModuleChart, "type" | "unit">;

function asNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function buildModuleChartOption(
  chart: ModuleChartData,
  fallbackUnit: string,
): EChartsOption | undefined {
  const periods = chart.periods ?? [];
  const unit = chart.unit ?? fallbackUnit;
  const entries = Object.entries(chart.series ?? {});

  if (chart.type === "waterfall" && chart.steps) {
    const order = Object.entries(chart.steps);
    const steps = order.flatMap(([label, raw], index) => {
      const value = asNumber(raw);
      if (value === null) return [];
      const kind: "total" | "up" | "down" = index === 0 || index === order.length - 1
        ? "total"
        : value >= 0 ? "up" : "down";
      return [{ label, value, kind }];
    });
    return buildWaterfall(steps, unit) as EChartsOption | undefined;
  }

  if (chart.type === "treemap") {
    const currentIndex = Math.max(0, periods.length - 1);
    const data = entries.flatMap(([name, raw]) => {
      const values = Array.isArray(raw) ? raw : [raw];
      const value = asNumber(values[currentIndex]);
      return value === null || value <= 0 ? [] : [{ name, value }];
    });
    if (data.length === 0) return undefined;
    return {
      tooltip: { trigger: "item", formatter: (params: unknown) => {
        const item = params as { name?: string; value?: number };
        return `${item.name ?? ""}<br>${formatFinancialValue(item.value ?? 0, { unit })}`;
      } },
      textStyle: { fontFamily: CHART_THEME.font },
      series: [
        {
          type: "treemap",
          data,
          roam: false,
          breadcrumb: { show: false },
          color: [...SERIES_PALETTE],
          label: { show: true, formatter: "{b}", color: CHART_THEME.ink, fontFamily: CHART_THEME.font },
        },
      ],
    };
  }

  if (chart.type === "bar" && entries.length > 0 && entries.every(([, value]) => !Array.isArray(value))) {
    const rows = entries.flatMap(([name, raw]) => {
      const value = asNumber(raw);
      return value === null ? [] : [{
        name,
        value,
        display: formatFinancialValue(value, { unit }),
        color: EXPENSE_CATEGORY_COLORS[name],
      }];
    });
    return buildRankBar(rows, unit) as EChartsOption | undefined;
  }

  if (chart.type === "ratio_bar" && entries.length > 0 && entries.every(([, value]) => !Array.isArray(value))) {
    const slices = entries.flatMap(([name, raw]) => {
      const value = asNumber(raw);
      return value === null ? [] : [{ name, value: Math.abs(value), color: EXPENSE_CATEGORY_COLORS[name] }];
    });
    return buildDonut(slices, unit) as EChartsOption | undefined;
  }

  if ((chart.type === "line" || chart.type === "ratio_bar" || chart.type === "bar") && entries.length > 0) {
    const isPercent = unit === "ratio" || unit === "%";
    const normalizedUnit = unit === "ratio" ? "%" : unit;
    const series = entries.map(([title, raw]) => {
      const values = Array.isArray(raw) ? raw : [raw];
      const alignedPeriods = periods.length ? periods : values.map((_, index) => `第 ${index + 1} 期`);
      const points = alignedPeriods.map((period, index) => {
        const parsed = asNumber(values[index]);
        const value = parsed === null ? null : isPercent && unit === "ratio" ? Number((parsed * 100).toFixed(2)) : parsed;
        return {
          period,
          value: value ?? 0,
          display: value === null ? "—" : formatFinancialValue(value, { unit: normalizedUnit }),
          status: value === null ? "unavailable" : "ready",
        };
      });
      return { key: title, title, axis: chart.type === "line" ? "line" as const : "bar" as const, color: EXPENSE_CATEGORY_COLORS[title], unit: normalizedUnit, points };
    });
    return buildCombo(series) as EChartsOption | undefined;
  }

  return undefined;
}

export function normalizeModuleSeries(raw: unknown): unknown[] {
  if (Array.isArray(raw)) return raw;
  if (raw === null || raw === undefined) return [];
  return [raw];
}
