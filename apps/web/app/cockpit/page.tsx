import { CockpitOverviewApp } from "../../components/cockpit/cockpit-overview-app";
import { AppShell } from "../../components/shell/app-shell";
import type { DashboardFilters } from "../../lib/api/client";
import { DASHBOARD_FILTER_KEYS } from "../../lib/deep-links";

/**
 * S01 CFO 驾驶舱 · 集团总览（批次 A）
 *
 * 设计依据：docs/05_design/2026-09-29-cfo-cockpit-design.md §5.1 + §9-Q2
 * （与现有 dashboard 快照页「演进替换」：同一筛选契约，驾驶舱为新的呈现层）。
 *
 * 筛选从 URL 读取（可分享/可回链），与既有 dashboard 一致。
 */

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function CockpitOverviewPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const initialFilters: DashboardFilters = {};
  for (const key of DASHBOARD_FILTER_KEYS) {
    const value = first(query[key]);
    if (value) initialFilters[key] = value;
  }
  const filterKey = DASHBOARD_FILTER_KEYS.map(
    (key) => `${key}=${initialFilters[key] ?? ""}`,
  ).join("&");
  return (
    <AppShell>
      <CockpitOverviewApp key={filterKey} initialFilters={initialFilters} />
    </AppShell>
  );
}
