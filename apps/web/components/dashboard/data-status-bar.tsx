import type { DashboardResponse } from "../../lib/api/client";

export function DataStatusBar({ dashboard }: { dashboard: DashboardResponse }) {
  const status = dashboard.data_status;
  return (
    <div className="data-status-bar" role="status" aria-label="数据治理状态">
      <span><i className="status-dot" />数据批次 {status.batch_status === "published" ? "已发布" : status.batch_status}</span>
      <span>质量校验 {status.quality_status === "passed" ? "通过" : status.quality_status}</span>
      <span>对账 {status.reconciliation_status === "passed" ? "通过" : status.reconciliation_status}</span>
      <span>快照 {dashboard.context.metric_definition_set_id}</span>
      <span className="data-status-bar__right">分析引擎 {dashboard.context.analysis_engine_version}</span>
    </div>
  );
}
