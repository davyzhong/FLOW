import type { DashboardResponse } from "../../lib/api/client";

const labels: Record<string, string> = { revenue_volume: "量", revenue_mix: "结构", revenue_price: "价", warehousing_cost: "仓储", transportation_cost: "运输", other_direct_cost: "其他成本", operating_expense: "期间费用" };

export function ProfitBridgePanel({ bridge }: { bridge: DashboardResponse["profit_bridge"] }) {
  return (
    <section className="panel bridge-panel" role="region" aria-label="经营利润变动桥">
      <div className="panel-heading"><div><span>03</span><h3>经营利润变动桥</h3></div><small>对比：上年同期</small></div>
      <div className="bridge-impact"><span>经营利润变动</span><strong className={`is-${bridge.impact.semantic_direction}`}>{bridge.impact.display_value}</strong></div>
      <div className="bridge-bars">
        {bridge.drivers.map((driver) => <div className={`bridge-bar is-${driver.contribution.semantic_direction}`} key={driver.driver_code}><span>{labels[driver.driver_code] ?? driver.label}</span><i /><strong>{driver.contribution.display_value}</strong></div>)}
      </div>
      <p className="bridge-reconcile">驱动合计对账：{bridge.reconciliation_status === "passed" ? "通过" : bridge.reconciliation_status} · 差异 {bridge.reconciliation_difference}</p>
    </section>
  );
}
