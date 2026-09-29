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

const W = 720;
const H = 220;
const PAD = { top: 16, right: 56, bottom: 30, left: 62 };

function niceTicks(min: number, max: number, count = 4): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [min];
  const step = (max - min) / count;
  const mag = 10 ** Math.floor(Math.log10(Math.abs(step) || 1));
  const norm = step / mag;
  const nice = norm >= 5 ? 10 : norm >= 2 ? 5 : norm >= 1 ? 2 : 1;
  const tick = nice * mag;
  const start = Math.floor(min / tick) * tick;
  const ticks: number[] = [];
  for (let v = start; v <= max + tick; v += tick) {
    ticks.push(Number(v.toFixed(10)));
  }
  return ticks;
}

export function CockpitTrendPanel({ series }: { series: CockpitTrendSeries }) {
  const points = series.points ?? [];
  const ready = points.filter((p) => p.status === "ready" && Number.isFinite(p.value));

  if (ready.length === 0) {
    return (
      <article
        className="trend is-unavailable"
        data-testid="cockpit-trend-unavailable"
        data-key={series.key}
      >
        <header>
          <h4>{series.title}</h4>
          {series.unit ? <small>{series.unit}</small> : null}
        </header>
        <p className="trend__msg">该期间暂无可用数据（不补零）</p>
      </article>
    );
  }

  const values = ready.map((p) => p.value);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const pad = (rawMax - rawMin) * 0.15 || Math.abs(rawMax || 1) * 0.15;
  const ticks = niceTicks(rawMin - pad, rawMax + pad);
  const lo = Math.min(...ticks, rawMin - pad);
  const hi = Math.max(...ticks, rawMax + pad);

  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const x = (i: number) =>
    PAD.left + (ready.length === 1 ? plotW / 2 : (i / (ready.length - 1)) * plotW);
  const y = (v: number) => PAD.top + plotH - ((v - lo) / (hi - lo || 1)) * plotH;

  const line = ready
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`)
    .join(" ");
  const area = `${line} L${x(ready.length - 1).toFixed(1)},${(PAD.top + plotH).toFixed(1)} L${x(0).toFixed(1)},${(PAD.top + plotH).toFixed(1)} Z`;
  const labelStep = Math.max(1, Math.ceil(ready.length / 8));

  return (
    <article
      className="trend"
      data-testid="cockpit-trend"
      data-key={series.key}
      data-points={ready.length}
    >
      <header>
        <h4>{series.title}</h4>
        {series.unit ? <small>{series.unit}</small> : null}
      </header>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${series.title}趋势，${ready.length} 期，从 ${ready[0].display_value} 到 ${ready[ready.length - 1].display_value}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {ticks.map((t) => (
          <g key={t}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(t)}
              y2={y(t)}
              stroke="#e2e8f0"
              strokeWidth={1}
            />
            <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" fontSize={10} fill="#94a3b8">
              {t.toLocaleString()}
            </text>
          </g>
        ))}
        <path d={area} fill="rgba(37,99,235,.08)" />
        <path d={line} fill="none" stroke="#2563eb" strokeWidth={2.4} />
        {ready.map((p, i) => (
          <circle key={p.period} cx={x(i)} cy={y(p.value)} r={3.2} fill="#2563eb">
            <title>{`${p.period}：${p.display_value}${series.unit}`}</title>
          </circle>
        ))}
        {ready.map((p, i) =>
          i % labelStep === 0 || i === ready.length - 1 ? (
            <text
              key={p.period}
              x={x(i)}
              y={H - 9}
              textAnchor="middle"
              fontSize={9.5}
              fill="#94a3b8"
            >
              {p.period}
            </text>
          ) : null,
        )}
      </svg>
    </article>
  );
}
