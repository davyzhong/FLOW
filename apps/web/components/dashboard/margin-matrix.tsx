import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { dashboardFilterHref } from "../../lib/deep-links";

function band(value: string): string {
  const margin = Number(value);
  if (margin >= 0.29) return "heat-4";
  if (margin >= 0.28) return "heat-3";
  if (margin >= 0.27) return "heat-2";
  return "heat-1";
}

export function MarginMatrix({ matrix }: { matrix: DashboardResponse["margin_matrix"] }) {
  const cells = new Map(matrix.cells.map((cell) => [`${cell.customer_segment_id}:${cell.logistics_product_id}`, cell]));
  return (
    <section className="panel matrix-panel">
      <div className="panel-heading"><div><span>06</span><h3>客户群 × 产品毛利矩阵</h3></div><small>同比口径</small></div>
      <div className="table-scroll" role="region" aria-label="毛利矩阵横向滚动区域" tabIndex={0}><table aria-label="客户群与产品毛利矩阵"><thead><tr><th>客户群</th>{matrix.columns.map((column) => <th key={column.id}><Link href={dashboardFilterHref({ logistics_product_id: column.id })} title="按该产品筛选驾驶舱">{column.name}</Link></th>)}</tr></thead>
        <tbody>{matrix.rows.map((row) => <tr key={row.id}><th><Link href={dashboardFilterHref({ customer_segment_id: row.id })} title="按该客户群筛选驾驶舱">{row.name}</Link></th>{matrix.columns.map((column) => { const cell = cells.get(`${row.id}:${column.id}`); return <td key={column.id} className={cell?.actual_margin.exact_value ? band(cell.actual_margin.exact_value) : undefined}>{cell ? (
          <Link
            href={dashboardFilterHref({ customer_segment_id: row.id, logistics_product_id: column.id })}
            title={`${row.name} × ${column.name}：按组合筛选驾驶舱`}
          >
            <strong>{cell.actual_margin.display_value}</strong><small className={`is-${cell.comparison.semantic_direction}`}>{cell.comparison.display_value}</small>
          </Link>
        ) : <><strong>—</strong><small className="is-neutral">—</small></>}</td>; })}</tr>)}</tbody>
      </table></div>
      <div className="matrix-legend" aria-label="毛利率色阶"><span>低</span><i className="heat-1" /><i className="heat-2" /><i className="heat-3" /><i className="heat-4" /><span>高</span></div>
    </section>
  );
}
