import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { metricFocusHref } from "../../lib/deep-links";
import { formatDeltaPercent, formatFinancialValue } from "../cockpit/number-format";

type Card = DashboardResponse["metric_cards"][number];

function Comparison({ label, value, metricCode }: { label: string; value: Card["yoy"]; metricCode: string }) {
  const unavailable = value.status === "unavailable";
  const reason = unavailable ? value.unavailable_message ?? "当前不可用" : null;
  const statusLabel = value.unavailable_code?.includes("not_published") ? "未发布" : "不可用";
  const formatted = ["gross_margin", "fulfillment_cost_rate"].includes(metricCode)
    ? formatFinancialValue(value.exact_value ?? value.display_value, { unit: "ratio" })
    : formatDeltaPercent(value.exact_value ?? value.display_value);

  return (
    <span
      className={`metric-comparison is-${value.semantic_direction}`}
      data-status={value.status}
      aria-label={unavailable ? `${label}：${reason}` : `${label}：${formatted}`}
      title={reason ?? undefined}
    >
      <small>{label}</small>
      <span className="metric-comparison__value">
        {unavailable ? value.display_value : formatted}
        {unavailable ? <em className="metric-comparison__status">{statusLabel}</em> : null}
      </span>
    </span>
  );
}

export function MetricGrid({ cards }: { cards: DashboardResponse["metric_cards"] }) {
  return (
    <section className="metric-section" aria-label="核心经营指标">
      <div className="section-heading"><div><span>01</span><h3>核心经营指标</h3></div><small>实际 / 预算差异 / 同比 / YTD 预算差异</small></div>
      <div className="metric-grid">
        {cards.map((card) => (
          <article className="metric-card" data-testid="metric-card" key={card.metric_code}>
            <Link
              className="metric-card__link"
              href={metricFocusHref(card.metric_code)}
              aria-label={`${card.title}：在指标库中查看口径`}
            >
              <div className="metric-card__top"><span>{card.category}</span><small>{card.unit}</small></div>
              <h4>{card.title}</h4>
              <div className="metric-card__value">{formatFinancialValue(card.primary.exact_value ?? card.primary.display_value, { metricCode: card.metric_code, unit: card.unit, appendUnit: false })}</div>
              <div className="metric-card__comparisons">
                <Comparison label="预算" value={card.budget} metricCode={card.metric_code} />
                <Comparison label="同比" value={card.yoy} metricCode={card.metric_code} />
                <Comparison label="YTD" value={card.ytd_budget} metricCode={card.metric_code} />
              </div>
              {card.companion ? <div className="metric-card__companion">伴随指标 {formatFinancialValue(card.companion.exact_value ?? card.companion.display_value, { appendUnit: false })}</div> : null}
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
