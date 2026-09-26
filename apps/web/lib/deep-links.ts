// 全站深链 href 构造器（2026-09-26 超链接化批次一）：所有内部下钻链接的统一出处。
// 接收端参数合同见 docs/50_plans/2026-09-26-ui-deep-link-implementation-plan.md §2：
//   /metric-library ?focus={metric_code} | ?entry={entry_id}
//   /statements     ?report={report_id}
//   /reports        ?snapshot={snapshot_id 或 metric_snapshot_id} | ?focus={metric_snapshot_id}
//   /data           ?batch={batch_id}（仅会话内恢复，未命中时页面显式提示）
//   /operations     ?report={statement_report_id}
//   /               ?region_id=…&customer_segment_id=…&logistics_product_id=…&organization_id=…

export function metricFocusHref(metricCode: string): string {
  return `/metric-library?focus=${encodeURIComponent(metricCode)}`;
}

export function metricEntryHref(entryId: string): string {
  return `/metric-library?entry=${encodeURIComponent(entryId)}`;
}

export function statementReportHref(reportId: string): string {
  return `/statements?report=${encodeURIComponent(reportId)}`;
}

export function reportsSnapshotHref(snapshotId: string): string {
  return `/reports?snapshot=${encodeURIComponent(snapshotId)}`;
}

export function reportsFocusHref(metricSnapshotId: string): string {
  return `/reports?focus=${encodeURIComponent(metricSnapshotId)}`;
}

export function dataBatchHref(batchId: string): string {
  return `/data?batch=${encodeURIComponent(batchId)}`;
}

export function operationsReportHref(reportId: string): string {
  return `/operations?report=${encodeURIComponent(reportId)}`;
}

/** 分析运行定位（批次二 §3.2）：/analysis 接收 run_id，经 GET /analytics/analysis-runs/{id} 投影身份。 */
export function analysisRunHref(runId: string): string {
  return `/analysis?run_id=${encodeURIComponent(runId)}`;
}

export type DashboardDimensionFilter = {
  region_id?: string;
  customer_segment_id?: string;
  logistics_product_id?: string;
  organization_id?: string;
};

export const DASHBOARD_FILTER_KEYS = [
  "region_id",
  "customer_segment_id",
  "logistics_product_id",
  "organization_id",
] as const satisfies readonly (keyof DashboardDimensionFilter)[];

export function dashboardFilterHref(filters: DashboardDimensionFilter): string {
  const params = new URLSearchParams();
  for (const key of DASHBOARD_FILTER_KEYS) {
    const value = filters[key];
    if (value) params.set(key, value);
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

/** 指标卡片锚点 id：entry_id 优先（metric_code 跨 collection 可重复，如 gross_margin）。 */
export function metricAnchorId(metric: {
  metric_code: string;
  entry_id?: string | null;
  collection?: string;
}): string {
  if (metric.entry_id) return `metric-entry-${metric.entry_id}`;
  return `metric-${metric.collection ?? "general"}-${metric.metric_code}`;
}

/** 报表明细行 DOM id：复核更正记录以此做页内锚点（statement_type + item_name 在报告内唯一）。 */
export function statementRowId(statementType: string, itemName: string): string {
  const clean = (value: string) => value.replace(/\s+/g, "_");
  return `stmt-row-${clean(statementType)}-${clean(itemName)}`;
}
