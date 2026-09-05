"use client";

import type { ReactNode } from "react";

// 构成环形图：手写 SVG donut + 右侧图例；悬停显示精确金额与占比。
export type DonutDatum = { label: string; value: number };

const COLORS = [
  "#2563eb",
  "#0d9488",
  "#16a34a",
  "#ea580c",
  "#7c3aed",
  "#dc2626",
  "#0891b2",
  "#65a30d",
  "#d97706",
  "#475569",
];

export function DonutChart({
  items,
  unitLabel,
  ariaLabel,
}: {
  items: DonutDatum[];
  unitLabel: string;
  ariaLabel: string;
}) {
  const width = 420;
  const height = 280;
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const cx = width * 0.34;
  const cy = height / 2;
  const r = Math.min(cx, cy) - 12;
  const rIn = r * 0.56;
  const { arcs } = items.reduce<{ angle: number; arcs: ReactNode[] }>(
    (acc, item, index) => {
      const sweep = (item.value / (total || 1)) * 2 * Math.PI;
      const start = acc.angle;
      const end = start + sweep;
      acc.angle = end;
      const large = sweep > Math.PI ? 1 : 0;
      const pt = (radius: number, a: number) => [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
      const [x0, y0] = pt(r, start);
      const [x1, y1] = pt(r, end);
      const [x2, y2] = pt(rIn, end);
      const [x3, y3] = pt(rIn, start);
      acc.arcs.push(
        <path
          key={item.label}
          d={`M${x0.toFixed(1)},${y0.toFixed(1)} A${r},${r} 0 ${large} 1 ${x1.toFixed(1)},${y1.toFixed(1)} L${x2.toFixed(1)},${y2.toFixed(1)} A${rIn},${rIn} 0 ${large} 0 ${x3.toFixed(1)},${y3.toFixed(1)} Z`}
          fill={COLORS[index % COLORS.length]}
        >
          <title>{`${item.label}：${item.value.toFixed(2)} ${unitLabel}（${((item.value / (total || 1)) * 100).toFixed(1)}%）`}</title>
        </path>,
      );
      return acc;
    },
    { angle: -Math.PI / 2, arcs: [] },
  );
  const legendTop = Math.max(30, (height - items.length * 21) / 2);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel} className="stmt-svg">
      {arcs}
      <text x={cx} y={cy - 2} textAnchor="middle" className="stmt-donut-total">
        {total.toFixed(0)}
      </text>
      <text x={cx} y={cy + 15} textAnchor="middle" className="stmt-tick">
        {unitLabel}合计
      </text>
      {items.map((item, index) => (
        <g key={item.label}>
          <rect
            x={width - 148}
            y={legendTop + index * 21 - 9}
            width={11}
            height={11}
            rx={2}
            fill={COLORS[index % COLORS.length]}
          />
          <text x={width - 132} y={legendTop + index * 21 + 1} className="stmt-legend">
            {item.label}
          </text>
          <text x={width - 12} y={legendTop + index * 21 + 1} textAnchor="end" className="stmt-legend">
            {((item.value / (total || 1)) * 100).toFixed(1)}%
          </text>
        </g>
      ))}
    </svg>
  );
}
