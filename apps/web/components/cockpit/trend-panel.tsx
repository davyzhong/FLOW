"use client";

/**
 * S01 CFO 驾驶舱 · 趋势面板（批次 A）
 *
 * 技术选型：手写 SVG，零新依赖。
 * 依据：设计文档 §6「图表技术沿用零依赖手写 SVG（statements/trend-panel 惯例）」；
 * 实施计划 §6 Q1 图表选型未裁决前不引入新图表库（避免不可逆依赖）。
 *
 * 本组件渲染**单序列**（一个指标一条线）。多序列（柱+线双轴）属批次 C。
 * 不可用时显式显示原因，不补零、不画假线。
 */

import type { CockpitTrendSeries } from "./cockpit-types";
import { ChartBox } from "./charts/echarts-base";
import { buildCombo } from "./charts/builders";
import { formatFinancialValue } from "./number-format";


export function CockpitTrendPanel({ series }: { series: CockpitTrendSeries }) {
  const points = series.points ?? [];
  const ready = points.filter((point) => point.status === "ready" && Number.isFinite(point.value));
  if (ready.length === 0) {
    return (
      <article className="trend is-unavailable" data-testid="cockpit-trend-unavailable" data-key={series.key}>
        <header><h4>{series.title}</h4>{series.unit ? <small>{series.unit}</small> : null}</header>
        <p className="trend__msg">该期间暂无可用数据（不补零）</p>
      </article>
    );
  }

  const isRatio = series.unit === "ratio";
  const chartUnit = isRatio ? "%" : series.unit;
  const firstPeriod = ready[0].period;
  const lastPeriod = ready[ready.length - 1].period;
  const option = buildCombo([{
    key: series.key,
    title: series.title,
    axis: "line",
    unit: chartUnit,
    points: points.map((point) => ({
      period: point.period,
      value: isRatio ? Number((point.value * 100).toFixed(2)) : point.value,
      display: isRatio
        ? formatFinancialValue(point.value, { unit: "ratio" })
        : formatFinancialValue(point.value, { unit: series.unit }),
      status: point.status,
    })),
  }]);

  return (
    <article className="trend" data-testid="cockpit-trend" data-key={series.key} data-points={ready.length}>
      <ChartBox
        title={series.title}
        sub={chartUnit}
        option={option}
        ariaLabel={`${series.title}趋势，${firstPeriod} 至 ${lastPeriod}，${ready.length} 期，单位${chartUnit}，从 ${formatFinancialValue(ready[0].value, { unit: series.unit })} 到 ${formatFinancialValue(ready[ready.length - 1].value, { unit: series.unit })}`}
        height={250}
      />
      <details className="trend-details">
        <summary>查看趋势数据</summary>
        <table aria-label={`${series.title}趋势数据明细`}>
          <thead><tr><th>期间</th><th>{series.title}</th></tr></thead>
          <tbody>{points.map((point) => <tr key={point.period}>
            <th>{point.period}</th>
            <td>{point.status === "ready" ? formatFinancialValue(point.value, { unit: series.unit }) : "—"}</td>
          </tr>)}</tbody>
        </table>
      </details>
    </article>
  );
}
