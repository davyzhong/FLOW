import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { dashboardFilterHref } from "../../lib/deep-links";
import { formatDeltaPercent, formatFinancialValue } from "../cockpit/number-format";

export function ProductPerformanceTable({
  table,
  catalogProductCount,
}: {
  table: DashboardResponse["product_table"];
  catalogProductCount: number;
}) {
  return (
    <section className="panel product-panel">
      <div className="panel-heading"><div><span>05</span><h3>产品经营表现</h3></div><small>有经营事实 {table.rows.length}/{catalogProductCount} 个产品 · 比较：{table.comparison_label}</small></div>
      <div className="table-scroll" role="region" aria-label="产品经营表现（可横向滚动）" tabIndex={0}><table aria-label="产品经营表现"><thead><tr><th>物流产品</th><th>收入</th><th>收入同比</th><th>订单量</th><th>订单同比</th><th>毛利率</th><th>毛利率同比</th><th>履约成本率</th></tr></thead>
        <tbody>{table.rows.length ? table.rows.map((row) => <tr key={row.logistics_product_id}><th><Link href={dashboardFilterHref({ logistics_product_id: row.logistics_product_id })} title="按该产品筛选驾驶舱"><span>{row.name}</span><small>{row.code}</small></Link></th><td>{formatFinancialValue(row.revenue.exact_value ?? row.revenue.display_value, { metricCode: "revenue", unit: "CNY" })}</td><td className={`is-${row.revenue_comparison.semantic_direction}`}>{formatDeltaPercent(row.revenue_comparison.exact_value ?? row.revenue_comparison.display_value)}</td><td>{formatFinancialValue(row.orders.exact_value ?? row.orders.display_value, { metricCode: "orders", unit: "单" })}</td><td className={`is-${row.orders_comparison.semantic_direction}`}>{formatDeltaPercent(row.orders_comparison.exact_value ?? row.orders_comparison.display_value)}</td><td>{formatFinancialValue(row.gross_margin.exact_value ?? row.gross_margin.display_value, { metricCode: "gross_margin", unit: "ratio" })}</td><td className={`is-${row.gross_margin_comparison.semantic_direction}`}>{formatFinancialValue(row.gross_margin_comparison.exact_value ?? row.gross_margin_comparison.display_value, { unit: "ratio" })}</td><td>{formatFinancialValue(row.fulfillment_cost_rate.exact_value ?? row.fulfillment_cost_rate.display_value, { metricCode: "fulfillment_cost_rate", unit: "ratio" })}</td></tr>) : <tr><td colSpan={8}>{table.degradation_message ?? "当前已发布快照未提供产品经营事实"}</td></tr>}</tbody>
      </table></div>
    </section>
  );
}
