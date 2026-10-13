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
import type { CockpitDrill, CockpitKpiCard as Card, CockpitPolarity } from "./cockpit-types";

function Comparison({
  label,
  value,
  polarity,
}: {
  label: string;
  value: DashboardValue;
  polarity: CockpitPolarity;
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
  const good = polarity === "positive" ? rising : polarity === "negative" ? !rising : true;
  return (
    <span
      className={`cmp ${good ? "is-good" : "is-bad"}`}
      data-status="ok"
      aria-label={`${label}：${value.display_value}`}
    >
      <small>{label}</small>
      <span className="cmp__value">
        {rising ? "↑" : value.semantic_direction === "negative" ? "↓" : "→"}
        {value.display_value}
      </span>
    </span>
  );
}

export function CockpitKpiCard({
  card,
  onDrill,
}: {
  card: Card;
  onDrill?: (drill: CockpitDrill) => void;
}) {
  const [opened, setOpened] = useState(false);

  const open = useCallback(() => {
    setOpened(true);
    onDrill?.({
      metricCode: card.metric_code,
      title: card.title,
      value: card.primary.display_value,
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
        <h4>{card.title}</h4>
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
      className={`kpi ${stateClass}`}
      data-testid="cockpit-kpi"
      data-metric={card.metric_code}
    >
      <button
        type="button"
        className="kpi__open"
        onClick={open}
        aria-label={`${card.title}：${card.primary.display_value}${card.unit}，查看计算口径与来源`}
      >
        <div className="kpi__top">
          <span className="kpi__cat">{card.category}</span>
          {card.control_line ? <span className="kpi__line">管控线 {card.control_line.display_value}</span> : null}
        </div>
        <h4>{card.title}</h4>
        <div className="kpi__value">
          {card.primary.display_value}
          <small>{card.unit}</small>
        </div>
        <div className="kpi__cmps">
          <Comparison label="同比" value={card.comparisons.yoy} polarity={card.polarity} />
          <Comparison label="环比" value={card.comparisons.mom} polarity={card.polarity} />
          <Comparison label="行业分位" value={card.comparisons.percentile} polarity="neutral" />
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
  onDrill,
}: {
  cards: Card[];
  onDrill?: (drill: CockpitDrill) => void;
}) {
  return (
    <section className="kpi-section" aria-label="核心经营指标">
      <div className="section-heading">
        <div>
          <span>01</span>
          <h3>核心经营指标</h3>
        </div>
        <small>三基准：同比 / 环比 / 行业分位 · 口径常驻 · 点击穿透</small>
      </div>
      <div className="kpi-grid">
        {cards.map((card) => (
          <CockpitKpiCard card={card} key={card.metric_code} onDrill={onDrill} />
        ))}
      </div>
    </section>
  );
}
