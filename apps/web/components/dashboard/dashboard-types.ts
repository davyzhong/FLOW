import type { DashboardFilters, DashboardResponse } from "../../lib/api/client";

export type DashboardLoad = (
  filters: DashboardFilters,
  signal: AbortSignal,
) => Promise<DashboardResponse>;

export type DashboardRequestState =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; dashboard: DashboardResponse };
