"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { flowApi } from "../../lib/api/client";
import type { DashboardFilters } from "../../lib/api/client";
import { DashboardError, DashboardLoaded, DashboardLoading } from "./dashboard-state";
import type { DashboardLoad, DashboardRequestState } from "./dashboard-types";

const defaultLoad: DashboardLoad = (filters, signal) =>
  flowApi.getDashboard(filters, signal);

function queryString(filters: DashboardFilters): string {
  const query = new URLSearchParams();
  for (const key of [
    "period_view",
    "organization_id",
    "customer_segment_id",
    "logistics_product_id",
    "region_id",
  ] as const) {
    const value = filters[key];
    if (value !== undefined && value !== null) query.set(key, value);
  }
  return query.toString();
}

export function DashboardApp({
  loadDashboard = defaultLoad,
  initialFilters = {},
}: {
  loadDashboard?: DashboardLoad;
  initialFilters?: DashboardFilters;
}) {
  const [filters, setFilters] = useState<DashboardFilters>(initialFilters);
  const [requestKey, setRequestKey] = useState(0);
  const [request, setRequest] = useState<DashboardRequestState>({ kind: "loading" });
  const serializedFilters = useMemo(() => queryString(filters), [filters]);

  useEffect(() => {
    const controller = new AbortController();
    loadDashboard(filters, controller.signal).then(
      (dashboard) => {
        if (!controller.signal.aborted) setRequest({ kind: "loaded", dashboard });
      },
      () => {
        if (!controller.signal.aborted) setRequest({ kind: "error" });
      },
    );
    return () => controller.abort();
  }, [filters, loadDashboard, requestKey]);

  useEffect(() => {
    // initialFilters 来自 URL searchParams（app/page.tsx）：有外来深链时 filters 初值
    // 即携带参数，replaceState 序列化后原样写回，不会抹掉深链。
    const location = serializedFilters ? `?${serializedFilters}` : window.location.pathname;
    window.history.replaceState(null, "", location);
  }, [serializedFilters]);

  const retry = useCallback(() => {
    setRequest({ kind: "loading" });
    setRequestKey((value) => value + 1);
  }, []);

  const hasInitialFilters = Object.values(initialFilters).some(
    (value) => value !== undefined && value !== null && value !== "",
  );

  return (
    <div className="dashboard-app">
      {request.kind !== "loaded" || request.dashboard.state === "empty" ? (
        <header className="dashboard-app__header">
          <div className="dashboard-app__mark" aria-hidden="true">F</div>
          <div>
            <p>FLOW · FINANCE INTELLIGENCE</p>
            <h1>Finance BP 经营驾驶舱</h1>
          </div>
        </header>
      ) : null}
      {request.kind === "loading" ? <DashboardLoading /> : null}
      {request.kind === "error" ? (
        <DashboardError
          retry={retry}
          hint={
            hasInitialFilters
              ? "当前 URL 带有筛选参数；若参数对应的维度值不存在，服务端会拒绝该请求。可移除地址栏参数后重试。"
              : null
          }
        />
      ) : null}
      {request.kind === "loaded" ? (
        <DashboardLoaded dashboard={request.dashboard} onFiltersChange={setFilters} />
      ) : null}
    </div>
  );
}
