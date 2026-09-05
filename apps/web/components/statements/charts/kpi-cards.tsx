"use client";

// KPI 卡片网格：展示值 + 精确原值（悬停/小字）。
export type KpiCardDatum = { label: string; display: string; exact: string | null };

export function KpiCards({ items }: { items: KpiCardDatum[] }) {
  return (
    <dl className="stmt-kpi-grid" aria-label="核心财务指标">
      {items.map((item) => (
        <div className="stmt-kpi" data-testid="statement-kpi" key={item.label}>
          <dt>{item.label}</dt>
          <dd title={item.exact ?? undefined}>{item.display}</dd>
        </div>
      ))}
    </dl>
  );
}
