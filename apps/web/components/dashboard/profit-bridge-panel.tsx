import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { metricFocusHref } from "../../lib/deep-links";

const labels: Record<string, string> = { revenue_volume: "量", revenue_mix: "结构", revenue_price: "价", warehousing_cost: "仓储", transportation_cost: "运输", other_direct_cost: "其他成本", operating_expense: "期间费用" };

// 桥接驱动码不是指标库 metric_code。只映射到能解释该驱动的现有口径；
// 期间费用目前没有独立指标条目，因此保留为文本，不生成失效深链。
const metricCodeByDriver: Record<string, string> = {
  revenue_volume: "orders",
  revenue_mix: "revenue",
  revenue_price: "revenue_per_order",
  warehousing_cost: "direct_cost",
  transportation_cost: "direct_cost",
  other_direct_cost: "direct_cost",
};

export function ProfitBridgePanel({ bridge }: { bridge: DashboardResponse["profit_bridge"] }) {
  return (
    <section className="panel bridge-panel" role="region" aria-label="经营利润变动桥">
      <div className="panel-heading"><div><span>03</span><h3>经营利润变动桥</h3></div><small>对比：上年同期</small></div>
      <div className="bridge-impact"><span>经营利润变动</span><strong className={`is-${bridge.impact.semantic_direction}`}>{bridge.impact.display_value}</strong></div>
      <div className="bridge-bars">
        {bridge.drivers.map((driver) => {
          const metricCode = metricCodeByDriver[driver.driver_code];
          const label = labels[driver.driver_code] ?? driver.label;
          const content = <><span>{label}</span><i /><strong>{driver.contribution.display_value}</strong></>;
          return metricCode ? (
            <Link
              className={`bridge-bar is-${driver.contribution.semantic_direction}`}
              key={driver.driver_code}
              data-driver-code={driver.driver_code}
              href={metricFocusHref(metricCode)}
              title={`${driver.label}：在指标库中查看相关口径`}
            >
              {content}
            </Link>
          ) : (
            <span
              className={`bridge-bar is-${driver.contribution.semantic_direction}`}
              key={driver.driver_code}
              data-driver-code={driver.driver_code}
              title="指标库暂无该驱动的独立口径定义"
            >
              {content}
            </span>
          );
        })}
      </div>
      <p className="bridge-reconcile">驱动合计对账：{bridge.reconciliation_status === "passed" ? "通过" : bridge.reconciliation_status} · 差异 {bridge.reconciliation_difference}</p>
    </section>
  );
}
