"use client";

/**
 * S01 CFO 驾驶舱 · KPI 卡（批次 A）
 *
 * 设计依据：docs/05_design/2026-09-29-cfo-cockpit-design.md（approved v0.6）
 * §5 四段式（指标卡 → 趋势与结构 → 归因排名 → 结论与行动）
 * §9-Q4 三基准（同比 + 环比 + 行业分位），预算基准内部期追加为第四注记
 *
 * 与既有 MetricGrid 的差异：
 * - 三基准（同比 / 环比 / 行业分位）而非「预算/同比/YTD」
 * - 口径注常驻（每个数字可解释）
 * - 可穿透（打开 DrillDrawer，见 cockpit-types.ts）
 * - 状态色按管控线（红突破 / 黄接近 / 绿正常 / 灰未就绪）
 *
 * 铁律：
 * - 每个上屏数字必须带 snapshot_id，否则拒绝渲染（可追溯）
 * - unavailable 不补零、不伪装；显示原因码
 */

import { useCallback, useState } from "react";

import type { DashboardValue } from "../../lib/api/client";
import { formatDeltaPercent, formatFinancialValue } from "./number-format";
import type { CockpitDrill, CockpitKpiCard as Card, CockpitPolarity, CockpitTrendSeries } from "./cockpit-types";

function formatKpiValue(value: string | number | null | undefined, metricCode: string, unit: string, appendUnit = true): string {
  const numeric = typeof value === "number" ? value : Number(value);
  if (["CNY", "人民币", "元"].includes(unit) && Number.isFinite(numeric) && Math.abs(numeric) >= 100_000_000) {
    return formatFinancialValue(numeric / 100_000_000, { unit: "亿元", appendUnit });
  }
  return formatFinancialValue(value, { metricCode, unit, appendUnit });
}

function Comparison({
  label,
  value,
  polarity,
  metricCode,
}: {
  label: string;
  value: DashboardValue;
  polarity: CockpitPolarity;
  metricCode: string;
}) {
  if (value.status === "unavailable") {
    const isUnpublished = value.unavailable_code?.includes("not_published");
    return (
      <span className="cmp is-neutral" data-status="unavailable" title={value.unavailable_message ?? "不可用"}>
        <small>{label}</small>
        <span className="cmp__value">
          —<em className="cmp__status">{isUnpublished ? "未发布" : "不可用"}</em>
        </span>
      </span>
    );
  }
  // contracts 的 semantic_direction 枚举：positive / negative / neutral / warning
  // polarity 决定着色方向：positive=越高越好，negative=越低越好，neutral=不着色
  const rising = value.semantic_direction === "positive";
  const exact = value.exact_value ?? value.display_value;
  const comparisonDisplay = ["gross_margin", "fulfillment_cost_rate"].includes(metricCode)
    ? formatFinancialValue(exact, { unit: "ratio" })
    : formatDeltaPercent(exact);
  const good = polarity === "positive" ? rising : polarity === "negative" ? !rising : true;
  return (
    <span
      className={`cmp ${good ? "is-good" : "is-bad"}`}
      data-status="ok"
      aria-label={`${label}：${comparisonDisplay}`}
    >
      <small>{label}</small>
      <span className="cmp__value">
        {rising ? "↑" : value.semantic_direction === "negative" ? "↓" : "→"}
        {comparisonDisplay}
      </span>
    </span>
  );
}

function KpiSparkline({ series, title, metricCode }: { series: CockpitTrendSeries; title: string; metricCode: string }) {
  const points = (series.points ?? []).filter((point) => point.status === "ready" && Number.isFinite(point.value));
  if (points.length < 2) return null;
  const unit = series.unit === "ratio" ? "百分比" : series.unit === "CNY" ? "人民币元" : series.unit;
  const values = points.map((point) => point.value);
  const latest = points.at(-1)!;
  const percent = series.unit === "ratio" ? latest.value * 100 : latest.value;
  if (metricCode === "gross_margin" && percent >= 0 && percent <= 100) {
    return (
      <svg className="kpi__sparkline kpi__ring" data-testid="cockpit-kpi-ring" viewBox="0 0 60 22" role="img" aria-label={`${title} ${latest.period}，${percent.toFixed(2)}%`}>
        <circle className="kpi__ring-track" cx="30" cy="11" r="8" fill="none" strokeWidth="4" />
        <circle cx="30" cy="11" r="8" fill="none" stroke="currentColor" strokeWidth="4" pathLength="100" strokeDasharray={`${percent} ${100 - percent}`} transform="rotate(-90 30 11)" />
      </svg>
    );
  }
  if (["revenue", "operating_profit", "operating_cash_flow"].includes(metricCode) && values.length >= 3) {
    const recent = points.slice(-3);
    const hasNegative = recent.some((point) => point.value < 0);
    const baseline = hasNegative ? 11 : 20;
    const scale = hasNegative ? 8 : 17;
    const peak = Math.max(...recent.map((point) => Math.abs(point.value)), 1);
    return (
      <svg className="kpi__sparkline kpi__bars" data-testid="cockpit-kpi-bars" viewBox="0 0 60 22" role="img" aria-label={`${title} ${recent[0].period} 至 ${latest.period}，最近三期柱状趋势（零基线），单位${unit}`}>
        {hasNegative ? <line x1="10" y1={baseline} x2="52" y2={baseline} stroke="currentColor" strokeOpacity="0.25" /> : null}
        {recent.map((point, index) => {
          const height = point.value === 0 ? 1 : Math.max(2, (Math.abs(point.value) / peak) * scale);
          const y = point.value < 0 ? baseline : baseline - height;
          return <rect key={point.period} x={13 + index * 13} y={y} width="6" height={height} rx="1" fill="currentColor" />;
        })}
      </svg>
    );
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const line = values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 58},${19 - ((value - min) / span) * 15}`).join(" ");
  return (
    <svg className="kpi__sparkline" data-testid="cockpit-kpi-sparkline" viewBox="0 0 60 22" role="img" aria-label={`${title} ${points[0].period} 至 ${points.at(-1)?.period}，${points.length}期趋势，单位${unit}`}>
      <polyline points={line} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={(values.length - 1) / Math.max(values.length - 1, 1) * 58} cy={19 - ((values.at(-1)! - min) / span) * 15} r="2.4" fill="currentColor" />
    </svg>
  );
}

export function CockpitKpiCard({
  card,
  trend,
  onDrill,
  compact = false,
}: {
  card: Card;
  trend?: CockpitTrendSeries;
  onDrill?: (drill: CockpitDrill) => void;
  compact?: boolean;
}) {
  const [opened, setOpened] = useState(false);

  const open = useCallback(() => {
    setOpened(true);
    onDrill?.({
      metricCode: card.metric_code,
      title: card.title,
      value: formatKpiValue(card.primary.exact_value ?? card.primary.display_value, card.metric_code, card.unit, false),
      unit: card.unit,
      caliberNote: card.caliber_note,
      snapshotId: card.snapshot_id ?? "",
      comparisons: card.comparisons,
    });
  }, [card, onDrill]);

  // 铁律：无可追溯快照的数字不渲染
  if (!card.snapshot_id) {
    return (
      <article className="kpi is-untraceable" data-testid="cockpit-kpi-untraceable">
        <div className="kpi__top">
          <span className="kpi__cat">{card.category}</span>
        </div>
        <h2>{card.title}</h2>
        <div className="kpi__value">⚠ 不可追溯</div>
        <div className="kpi__caliber">缺少 snapshot_id，按可追溯铁律拒绝渲染</div>
      </article>
    );
  }

  const stateClass =
    card.control_status === "breach"
      ? "is-breach"
      : card.control_status === "near"
        ? "is-near"
        : card.control_status === "not_ready"
          ? "is-notready"
          : "is-ok";

  return (
    <article
      className={`kpi ${stateClass}${compact ? " kpi--supporting" : ""}`}
      data-testid="cockpit-kpi"
      data-metric={card.metric_code}
    >
      <button
        type="button"
        className="kpi__open"
        onClick={open}
        aria-label={`${card.title}：${formatKpiValue(card.primary.exact_value ?? card.primary.display_value, card.metric_code, card.unit)}，查看计算口径与来源`}
      >
        <div className="kpi__top">
          <span className="kpi__cat">{card.category}</span>
          {card.control_line ? <span className="kpi__line">管控线 {formatFinancialValue(card.control_line.exact_value ?? card.control_line.display_value, { metricCode: card.metric_code, unit: card.unit })}</span> : null}
        </div>
        <h2>{card.title}</h2>
        <div className="kpi__value-row">
          <div className="kpi__value">
            {formatKpiValue(card.primary.exact_value ?? card.primary.display_value, card.metric_code, card.unit)}
          </div>
          {trend ? <KpiSparkline series={trend} title={card.title} metricCode={card.metric_code} /> : null}
        </div>
        <div className="kpi__cmps">
          <Comparison label="同比" value={card.comparisons.yoy} polarity={card.polarity} metricCode={card.metric_code} />
          <Comparison label="环比" value={card.comparisons.mom} polarity={card.polarity} metricCode={card.metric_code} />
          <Comparison label="行业分位" value={card.comparisons.percentile} polarity="neutral" metricCode={card.metric_code} />
        </div>
        {card.caliber_note ? <div className="kpi__caliber">口径：{card.caliber_note}</div> : null}
        {card.source_label ? <div className="kpi__source">{card.source_label}</div> : null}
      </button>
      {opened ? <span className="kpi__peek" aria-hidden="true">已打开穿透</span> : null}
    </article>
  );
}

export function CockpitKpiGrid({
  cards,
  trends = [],
  onDrill,
}: {
  cards: Card[];
  trends?: CockpitTrendSeries[];
  onDrill?: (drill: CockpitDrill) => void;
}) {
  const primaryOrder = ["revenue", "operating_profit", "gross_margin", "operating_cash_flow"];
  const orderedCards = [...cards].sort((left, right) => {
    const leftOrder = primaryOrder.indexOf(left.metric_code);
    const rightOrder = primaryOrder.indexOf(right.metric_code);
    return (leftOrder < 0 ? primaryOrder.length : leftOrder) - (rightOrder < 0 ? primaryOrder.length : rightOrder);
  });
  const primaryCards = orderedCards.filter((card) => primaryOrder.includes(card.metric_code));
  const supportingCards = orderedCards.filter((card) => !primaryOrder.includes(card.metric_code));
  const renderCard = (card: Card, compact: boolean) => (
    <CockpitKpiCard
      card={card}
      trend={trends.find((series) => series.key === card.metric_code)}
      key={card.metric_code}
      onDrill={onDrill}
      compact={compact}
    />
  );
  return (
    <section className="kpi-section" aria-label="核心经营指标">
      <div className="section-heading">
        <div>
          <span>01</span>
          <h2>核心经营指标</h2>
        </div>
        <small>三基准：同比 / 环比 / 行业分位 · 口径常驻 · 点击穿透</small>
      </div>
      <div className="kpi-grid">{primaryCards.map((card) => renderCard(card, false))}</div>
      {supportingCards.length ? <section className="kpi-supporting" aria-label="补充经营指标">
        <div className="section-heading"><div><span>01A</span><h2>补充经营指标</h2></div><small>规模、单均效率、成本与营运资本</small></div>
        <div className="kpi-grid kpi-grid--supporting">{supportingCards.map((card) => renderCard(card, true))}</div>
      </section> : null}
    </section>
  );
}
