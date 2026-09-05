"use client";

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
    bars: (WaterfallDatum & { lo: number; hi: number })[];
  }>(
    (acc, item) => {
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
      acc.bars.push({ ...item, lo, hi });
      return acc;
    },
    { run: 0, bars: [] },
  );
  const maxV = Math.max(...bars.flatMap((bar) => [bar.lo, bar.hi]), 0) * 1.06;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;
  const y = (v: number) => padT + innerH * (1 - v / (maxV || 1));
  const barWidth = Math.min(76, (innerW / bars.length) * 0.62);
  const gridLines = [0, 1, 2, 3, 4].map((g) => {
    const gy = padT + (innerH * g) / 4;
    const gv = maxV - (maxV * g) / 4;
    return (
      <g key={g}>
        <line x1={padL} y1={gy} x2={width - padR} y2={gy} stroke="#e2e8f0" />
        <text x={padL - 6} y={gy + 4} textAnchor="end" className="stmt-tick">
          {gv.toFixed(0)}
        </text>
      </g>
    );
  });
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel} className="stmt-svg">
      {gridLines}
      {bars.map((bar, index) => {
        const cx = padL + (innerW * (index + 0.5)) / bars.length;
        const yTop = y(Math.max(bar.hi, bar.lo));
        const barH = Math.max(2, Math.abs(y(bar.lo) - y(bar.hi)));
        const color =
          bar.kind === "base" || bar.kind === "total"
            ? "#334155"
            : bar.value >= 0
              ? "#16a34a"
              : "#dc2626";
        return (
          <g key={bar.label}>
            {index > 0 ? (
              <line
                x1={padL + (innerW * index) / bars.length}
                y1={y(bar.lo)}
                x2={cx - barWidth / 2}
                y2={y(bar.lo)}
                stroke="#cbd5e1"
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
              <title>{`${bar.label}：${bar.value.toFixed(2)} ${unitLabel}`}</title>
            </rect>
            <text x={cx} y={yTop - 6} textAnchor="middle" className="stmt-vlabel">
              {bar.value >= 0 ? "" : "−"}
              {Math.abs(bar.value).toFixed(1)}
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
