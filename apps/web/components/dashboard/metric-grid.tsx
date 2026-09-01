import type { DashboardResponse } from "../../lib/api/client";

type Card = DashboardResponse["metric_cards"][number];

function Comparison({ label, value }: { label: string; value: Card["yoy"] }) {
  return <span className={`metric-comparison is-${value.semantic_direction}`}><small>{label}</small>{value.display_value}</span>;
}

export function MetricGrid({ cards }: { cards: DashboardResponse["metric_cards"] }) {
  return (
    <section className="metric-section" aria-label="核心经营指标">
      <div className="section-heading"><div><span>01</span><h3>核心经营指标</h3></div><small>实际 / 预算差异 / 同比 / YTD 预算差异</small></div>
      <div className="metric-grid">
        {cards.map((card) => (
          <article className="metric-card" data-testid="metric-card" key={card.metric_code}>
            <div className="metric-card__top"><span>{card.category}</span><small>{card.unit}</small></div>
            <h4>{card.title}</h4>
            <div className="metric-card__value">{card.primary.display_value}</div>
            <div className="metric-card__comparisons">
              <Comparison label="预算" value={card.budget} />
              <Comparison label="同比" value={card.yoy} />
              <Comparison label="YTD" value={card.ytd_budget} />
            </div>
            {card.companion ? <div className="metric-card__companion">伴随指标 {card.companion.display_value}</div> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
