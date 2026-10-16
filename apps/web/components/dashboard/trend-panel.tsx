import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { reportsSnapshotHref } from "../../lib/deep-links";
import { ChartBox } from "../cockpit/charts/echarts-base";
import { buildCombo } from "../cockpit/charts/builders";
import { formatFinancialValue } from "../cockpit/number-format";

type SeriesKey = "revenue" | "operating_profit" | "operating_cash_flow";

const SERIES: { key: SeriesKey; title: string }[] = [
  { key: "revenue", title: "营业收入" },
  { key: "operating_profit", title: "经营利润" },
  { key: "operating_cash_flow", title: "经营现金流" },
];

export function TrendPanel({ trends }: { trends: DashboardResponse["trends"] }) {
  const points = trends.points;
  const option = buildCombo(SERIES.map(({ key, title }) => ({
    key,
    title,
    axis: "line" as const,
    unit: "CNY",
    points: points.map((point) => ({
      period: point.month,
      value: Number(point[key].exact_value ?? 0),
      display: formatFinancialValue(point[key].exact_value, { unit: "CNY" }),
      status: point[key].status === "available" && point[key].exact_value !== null ? "ready" : "unavailable",
    })),
  })));
  return (
    <section className="panel trend-panel" aria-labelledby="trend-heading">
      <div className="panel-heading"><div><span>02</span><h3 id="trend-heading">12 个月经营趋势</h3></div><small>{trends.coverage_count}/12 月已发布</small></div>
      <ChartBox title="近 12 个月经营趋势" sub="人民币元" option={option} ariaLabel="近 12 个月经营收入、利润与现金流趋势" height={260} />
      <div className="chart-legend"><span className="revenue">营业收入</span><span className="profit">经营利润</span><span className="cash">经营现金流</span></div>
      <details className="trend-details"><summary>查看趋势数据</summary>
        <table aria-label="趋势数据明细"><thead><tr><th>月份</th><th>收入</th><th>经营利润</th><th>现金流</th><th>毛利率</th></tr></thead>
          <tbody>{points.map((point) => <tr key={point.month}><th><Link href={reportsSnapshotHref(point.metric_snapshot_id)} title="在报告中心查看该月指标快照">{point.month}</Link></th><td>{formatFinancialValue(point.revenue.exact_value, { unit: "CNY" })}</td><td>{formatFinancialValue(point.operating_profit.exact_value, { unit: "CNY" })}</td><td>{formatFinancialValue(point.operating_cash_flow.exact_value, { unit: "CNY" })}</td><td>{formatFinancialValue(point.gross_margin.exact_value, { metricCode: "gross_margin", unit: "ratio" })}</td></tr>)}</tbody>
        </table>
      </details>
    </section>
  );
}
