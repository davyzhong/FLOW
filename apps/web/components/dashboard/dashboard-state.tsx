import type { DashboardResponse } from "../../lib/api/client";
import { dashboardStateMessage } from "./dashboard-format";

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

export function DashboardLoaded({ dashboard }: { dashboard: DashboardResponse }) {
  const message = dashboardStateMessage(dashboard.state);
  if (dashboard.state === "empty") {
    return <div className="dashboard-state dashboard-state--empty">{message}</div>;
  }
  return (
    <section className="dashboard-loaded" aria-label="经营驾驶舱内容">
      <div className={`dashboard-state-banner dashboard-state-banner--${dashboard.state}`}>
        {message}
      </div>
      <div className="dashboard-preview-grid" aria-label="驾驶舱摘要">
        <div>
          <strong>{dashboard.metric_cards.length}</strong>
          <span>核心指标</span>
        </div>
        <div>
          <strong>{dashboard.trends.coverage_count}/12</strong>
          <span>趋势覆盖</span>
        </div>
        <div>
          <strong>{dashboard.findings.length}</strong>
          <span>经营发现</span>
        </div>
      </div>
    </section>
  );
}
