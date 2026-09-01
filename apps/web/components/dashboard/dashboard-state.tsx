import type { DashboardFilters, DashboardResponse } from "../../lib/api/client";
import { dashboardStateMessage } from "./dashboard-format";
import { DashboardHeader } from "./dashboard-header";
import { DataStatusBar } from "./data-status-bar";
import { FindingsPanel } from "./findings-panel";
import { MarginMatrix } from "./margin-matrix";
import { MetricGrid } from "./metric-grid";
import { ProductPerformanceTable } from "./product-performance-table";
import { ProfitBridgePanel } from "./profit-bridge-panel";
import { TrendPanel } from "./trend-panel";
import { WorkflowNav } from "./workflow-nav";

export function DashboardLoading() {
  return (
    <div className="dashboard-state dashboard-state--loading" role="status" aria-label="正在加载经营驾驶舱">
      <span className="dashboard-state__pulse" aria-hidden="true" />
      <span>正在读取已发布经营数据…</span>
    </div>
  );
}

export function DashboardError({ retry }: { retry: () => void }) {
  return (
    <div className="dashboard-state dashboard-state--error" role="alert">
      <p>经营驾驶舱暂时无法加载</p>
      <button type="button" onClick={retry}>
        重试
      </button>
    </div>
  );
}

export function DashboardLoaded({
  dashboard,
  onFiltersChange,
}: {
  dashboard: DashboardResponse;
  onFiltersChange?: (filters: DashboardFilters) => void;
}) {
  const message = dashboardStateMessage(dashboard.state);
  if (dashboard.state === "empty") {
    return <div className="dashboard-state dashboard-state--empty">{message}</div>;
  }
  return (
    <section className="dashboard-loaded" aria-label="经营驾驶舱内容">
      <WorkflowNav />
      <div className="dashboard-workspace">
        <DashboardHeader dashboard={dashboard} onFiltersChange={onFiltersChange} />
        <div className={`dashboard-state-banner dashboard-state-banner--${dashboard.state}`}>
          {message}
        </div>
        <DataStatusBar dashboard={dashboard} />
        <MetricGrid cards={dashboard.metric_cards} />
        <div className="dashboard-analysis-grid">
          <TrendPanel trends={dashboard.trends} />
          <ProfitBridgePanel bridge={dashboard.profit_bridge} />
          <FindingsPanel findings={dashboard.findings} />
        </div>
        <div className="dashboard-detail-grid">
          <ProductPerformanceTable table={dashboard.product_table} />
          <MarginMatrix matrix={dashboard.margin_matrix} />
        </div>
      </div>
    </section>
  );
}
