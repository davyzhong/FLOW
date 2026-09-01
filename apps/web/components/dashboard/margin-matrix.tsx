import type { DashboardResponse } from "../../lib/api/client";

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
      <div className="table-scroll"><table aria-label="客户群与产品毛利矩阵"><thead><tr><th>客户群</th>{matrix.columns.map((column) => <th key={column.id}>{column.name}</th>)}</tr></thead>
        <tbody>{matrix.rows.map((row) => <tr key={row.id}><th>{row.name}</th>{matrix.columns.map((column) => { const cell = cells.get(`${row.id}:${column.id}`); return <td key={column.id} className={cell?.actual_margin.exact_value ? band(cell.actual_margin.exact_value) : undefined}><strong>{cell?.actual_margin.display_value ?? "—"}</strong><small className={`is-${cell?.comparison.semantic_direction ?? "neutral"}`}>{cell?.comparison.display_value ?? "—"}</small></td>; })}</tr>)}</tbody>
      </table></div>
      <div className="matrix-legend" aria-label="毛利率色阶"><span>低</span><i className="heat-1" /><i className="heat-2" /><i className="heat-3" /><i className="heat-4" /><span>高</span></div>
    </section>
  );
}
