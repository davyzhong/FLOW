"use client";

import { formatFinancialValue } from "../../cockpit/number-format";
import { VISUAL_TOKENS } from "../../../lib/visual-tokens.generated";

const GRID_COLOR = VISUAL_TOKENS["chart-grid"];
const CURRENT_COLOR = VISUAL_TOKENS["colors-data-revenue"];
const PRIOR_COLOR = VISUAL_TOKENS["colors-data-series4"];

// 分组柱状图（本期 vs 上期）：手写 SVG，正负共用零基线。
export type GroupedBarDatum = { label: string; current: number; prior: number | null };

export function GroupedBarChart({
  items,
  currentLabel,
  priorLabel,
  unitLabel,
  ariaLabel,
}: {
  items: GroupedBarDatum[];
  currentLabel: string;
  priorLabel: string | null;
  unitLabel: string;
  ariaLabel: string;
}) {
  const width = 620;
  const height = 300;
  const padL = 66;
  const padR = 14;
  const padT = 18;
  const padB = 46;
  const values = items.flatMap((item) => [item.current, item.prior ?? 0]);
  const maxV = Math.max(...values, 0) * 1.1;
  const minV = Math.min(...values, 0) * 1.1;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;
  const y = (v: number) => padT + innerH * (1 - (v - minV) / (maxV - minV || 1));
  const groupW = innerW / items.length;
  const barW = priorLabel === null ? Math.min(96, groupW * 0.5) : Math.min(46, groupW * 0.34);
  const zero = y(0);
  const gridLines = [0, 1, 2, 3, 4].map((g) => {
    const gy = padT + (innerH * g) / 4;
    const gv = maxV - ((maxV - minV) * g) / 4;
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
      <line x1={padL} y1={zero} x2={width - padR} y2={zero} stroke={VISUAL_TOKENS["colors-text-muted"]} />
      {items.map((item, index) => {
        const groupX = padL + groupW * (index + 0.5);
        const bars: React.ReactNode[] = [];
        const draw = (value: number, offset: number, fill: string, seriesLabel: string) => {
          const yTop = y(Math.max(value, 0));
          const barH = Math.max(2, Math.abs(y(value) - y(0)));
          bars.push(
            <g key={seriesLabel}>
              <rect
                x={groupX - (priorLabel === null ? barW / 2 : barW * 1.06) + offset}
                y={yTop}
                width={barW}
                height={barH}
                fill={fill}
                rx={3}
              >
                <title>{`${item.label} ${seriesLabel}：${formatFinancialValue(value, { unit: unitLabel })}`}</title>
              </rect>
              <text
                x={groupX - (priorLabel === null ? barW / 2 : barW * 1.06) + offset + barW / 2}
                y={value >= 0 ? yTop - 5 : yTop + barH + 13}
                textAnchor="middle"
                className="stmt-vlabel"
              >
                {formatFinancialValue(value, { unit: unitLabel, appendUnit: false })}
              </text>
            </g>,
          );
        };
        draw(item.current, priorLabel === null ? 0 : -2, CURRENT_COLOR, currentLabel);
        if (priorLabel !== null && item.prior !== null) {
          draw(item.prior, barW + 4, PRIOR_COLOR, priorLabel);
        }
        return (
          <g key={item.label}>
            {bars}
            <text x={groupX} y={height - padB + 18} textAnchor="middle" className="stmt-xlab">
              {item.label}
            </text>
          </g>
        );
      })}
      {priorLabel !== null ? (
        <g>
          <rect x={padL} y={height - 20} width={11} height={11} fill={CURRENT_COLOR} rx={2} />
          <text x={padL + 16} y={height - 11} className="stmt-legend">
            {currentLabel}
          </text>
          <rect x={padL + 92} y={height - 20} width={11} height={11} fill={PRIOR_COLOR} rx={2} />
          <text x={padL + 108} y={height - 11} className="stmt-legend">
            {priorLabel}
          </text>
        </g>
      ) : null}
    </svg>
  );
}
