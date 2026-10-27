"use client";

import { formatFinancialValue } from "../../cockpit/number-format";
import { VISUAL_TOKENS } from "../../../lib/visual-tokens.generated";

const GRID_COLOR = VISUAL_TOKENS["chart-grid"];

// 利润形成 / 现金桥瀑布图：手写 SVG，无图表库依赖。
// base/total 柱从零起画，delta 柱悬浮于累计区间；红减绿增、深色为小计。
export type WaterfallDatum = { label: string; value: number; kind: "base" | "delta" | "total" };

export function WaterfallChart({
  items,
  unitLabel,
  ariaLabel,
}: {
  items: WaterfallDatum[];
  unitLabel: string;
  ariaLabel: string;
}) {
  const width = 920;
  const height = 330;
  const padL = 60;
  const padR = 14;
  const padT = 22;
  const padB = 52;
  const { bars } = items.reduce<{
    run: number;
    bars: (WaterfallDatum & { lo: number; hi: number; connector: number })[];
  }>(
    (acc, item) => {
      const connector = acc.run;
      let lo: number;
      let hi: number;
      if (item.kind === "base" || item.kind === "total") {
        lo = 0;
        hi = item.value;
        acc.run = item.value;
      } else {
        lo = Math.min(acc.run, acc.run + item.value);
        hi = Math.max(acc.run, acc.run + item.value);
        acc.run += item.value;
      }
      acc.bars.push({ ...item, lo, hi, connector });
      return acc;
    },
    { run: 0, bars: [] },
  );
  const endpoints = bars.flatMap((bar) => [bar.lo, bar.hi]);
  const minValue = Math.min(...endpoints, 0);
  const maxValue = Math.max(...endpoints, 0);
  const axisMin = minValue < 0 ? minValue * 1.06 : 0;
  const axisMax = maxValue > 0 ? maxValue * 1.06 : 0;
  const axisRange = axisMax - axisMin || 1;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;
  const y = (v: number) => padT + innerH * (1 - (v - axisMin) / axisRange);
  const barWidth = Math.min(76, (innerW / bars.length) * 0.62);
  const gridLines = [0, 1, 2, 3, 4].map((g) => {
    const gy = padT + (innerH * g) / 4;
    const gv = axisMax - (axisRange * g) / 4;
    return (
      <g key={g}>
        <line x1={padL} y1={gy} x2={width - padR} y2={gy} stroke={GRID_COLOR} />
        <text x={padL - 6} y={gy + 4} textAnchor="end" className="stmt-tick">
          {formatFinancialValue(gv, { unit: unitLabel, appendUnit: false })}
        </text>
      </g>
    );
  });
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel} className="stmt-svg">
      {gridLines}
      <line
        className="stmt-zero-line"
        x1={padL}
        y1={y(0)}
        x2={width - padR}
        y2={y(0)}
        stroke={VISUAL_TOKENS["colors-text-muted"]}
      />
      {bars.map((bar, index) => {
        const cx = padL + (innerW * (index + 0.5)) / bars.length;
        const yTop = y(Math.max(bar.hi, bar.lo));
        const barH = Math.max(2, Math.abs(y(bar.lo) - y(bar.hi)));
        const color = bar.value < 0
          ? VISUAL_TOKENS["colors-semantic-negative"]
          : bar.kind === "base" || bar.kind === "total"
            ? VISUAL_TOKENS["colors-data-revenue"]
            : VISUAL_TOKENS["colors-semantic-positive"];
        return (
          <g key={bar.label}>
            {index > 0 ? (
              <line
                x1={padL + (innerW * index) / bars.length}
                y1={y(bar.connector)}
                x2={cx - barWidth / 2}
                y2={y(bar.connector)}
                stroke={VISUAL_TOKENS["colors-line-default"]}
                strokeDasharray="3,3"
              />
            ) : null}
            <rect
              x={cx - barWidth / 2}
              y={yTop}
              width={barWidth}
              height={barH}
              fill={color}
              rx={3}
            >
              <title>{`${bar.label}：${formatFinancialValue(bar.value, { unit: unitLabel })}`}</title>
            </rect>
            <text x={cx} y={bar.value < 0 ? yTop + barH + 13 : yTop - 6} textAnchor="middle" className="stmt-vlabel">
              {bar.value >= 0 ? "" : "−"}
              {formatFinancialValue(Math.abs(bar.value), { unit: unitLabel, appendUnit: false })}
            </text>
            <text x={cx} y={height - padB + 18} textAnchor="middle" className="stmt-xlab">
              {bar.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
