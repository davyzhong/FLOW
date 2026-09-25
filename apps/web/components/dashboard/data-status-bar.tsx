import Link from "next/link";

import type { DashboardResponse } from "../../lib/api/client";
import { dataBatchHref, reportsFocusHref } from "../../lib/deep-links";

export function DataStatusBar({ dashboard }: { dashboard: DashboardResponse }) {
  const status = dashboard.data_status;
  return (
    <div className="data-status-bar" role="status" aria-label="数据治理状态">
      <span><i className="status-dot" /><Link href={dataBatchHref(dashboard.context.batch_id)} title="在数据工作台查看该批次">数据批次 {status.batch_status === "published" ? "已发布" : status.batch_status}</Link></span>
      <span>质量校验 {status.quality_status === "passed" ? "通过" : status.quality_status}</span>
      <span>对账 {status.reconciliation_status === "passed" ? "通过" : status.reconciliation_status}</span>
      <span><Link href={reportsFocusHref(dashboard.context.metric_snapshot_id)} title="在报告中心查看该指标快照">快照 {dashboard.context.metric_definition_set_id}</Link></span>
      <span className="data-status-bar__right">分析引擎 {dashboard.context.analysis_engine_version}</span>
    </div>
  );
}
