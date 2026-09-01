import type { DashboardResponse } from "../../lib/api/client";

type Point = DashboardResponse["trends"]["points"][number];
type SeriesKey = "revenue" | "operating_profit" | "operating_cash_flow";

function path(points: Point[], key: SeriesKey): string {
  const values = points.map((point) => Number(point[key].exact_value ?? 0));
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  return values.map((value, index) => `${index === 0 ? "M" : "L"} ${18 + index * 48} ${122 - ((value - minimum) / spread) * 92}`).join(" ");
}

export function TrendPanel({ trends }: { trends: DashboardResponse["trends"] }) {
  const points = trends.points;
  return (
    <section className="panel trend-panel" aria-labelledby="trend-heading">
      <div className="panel-heading"><div><span>02</span><h3 id="trend-heading">12 个月经营趋势</h3></div><small>{trends.coverage_count}/12 月已发布</small></div>
      <svg className="trend-chart" viewBox="0 0 570 155" role="img" aria-label="近 12 个月经营趋势">
        {[30, 76, 122].map((y) => <line x1="18" y1={y} x2="550" y2={y} key={y} className="chart-grid" />)}
        <path d={path(points, "revenue")} className="trend-line trend-line--revenue" />
        <path d={path(points, "operating_profit")} className="trend-line trend-line--profit" />
        <path d={path(points, "operating_cash_flow")} className="trend-line trend-line--cash" />
      </svg>
      <div className="chart-legend"><span className="revenue">营业收入</span><span className="profit">经营利润</span><span className="cash">经营现金流</span></div>
      <details className="trend-details"><summary>查看趋势数据</summary>
        <table aria-label="趋势数据明细"><thead><tr><th>月份</th><th>收入</th><th>经营利润</th><th>现金流</th><th>毛利率</th></tr></thead>
          <tbody>{points.map((point) => <tr key={point.month}><th>{point.month}</th><td>{point.revenue.display_value}</td><td>{point.operating_profit.display_value}</td><td>{point.operating_cash_flow.display_value}</td><td>{point.gross_margin.display_value}</td></tr>)}</tbody>
        </table>
      </details>
    </section>
  );
}
