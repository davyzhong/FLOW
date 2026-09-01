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
    const location = serializedFilters ? `?${serializedFilters}` : window.location.pathname;
    window.history.replaceState(null, "", location);
  }, [serializedFilters]);

  const retry = useCallback(() => {
    setRequest({ kind: "loading" });
    setRequestKey((value) => value + 1);
  }, []);

  return (
    <main className="dashboard-app">
      <header className="dashboard-app__header">
        <div className="dashboard-app__mark" aria-hidden="true">F</div>
        <div>
          <p>FLOW · FINANCE INTELLIGENCE</p>
          <h1>Finance BP 经营驾驶舱</h1>
        </div>
      </header>
      {request.kind === "loading" ? <DashboardLoading /> : null}
      {request.kind === "error" ? <DashboardError retry={retry} /> : null}
      {request.kind === "loaded" ? (
        <DashboardLoaded dashboard={request.dashboard} onFiltersChange={setFilters} />
      ) : null}
    </main>
  );
}
