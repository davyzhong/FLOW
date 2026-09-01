import type { components, operations } from "@flow/contracts";

export type WorkspaceResponse = components["schemas"]["WorkspaceResponse"];
export type DashboardResponse = components["schemas"]["DashboardOverviewResponse"];
export type DashboardFilters = NonNullable<
  operations["dashboard_overview_api_v1_dashboard_overview_get"]["parameters"]["query"]
>;

const API_BASE_URL = process.env.NEXT_PUBLIC_FLOW_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`FLOW API request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

function dashboardQuery(filters: DashboardFilters): string {
  const parameters = new URLSearchParams();
  const keys = [
    "period_view",
    "organization_id",
    "customer_segment_id",
    "logistics_product_id",
    "region_id",
  ] as const satisfies readonly (keyof DashboardFilters)[];
  for (const key of keys) {
    const value = filters[key];
    if (value !== undefined && value !== null) {
      parameters.set(key, value);
    }
  }
  const query = parameters.toString();
  return query ? `?${query}` : "";
}

export const flowApi = {
  getWorkspace(): Promise<WorkspaceResponse> {
    return request<WorkspaceResponse>("/api/v1/workspace");
  },
  getDashboard(
    filters: DashboardFilters = {},
    signal?: AbortSignal,
  ): Promise<DashboardResponse> {
    return request<DashboardResponse>(
      `/api/v1/dashboard/overview${dashboardQuery(filters)}`,
      signal,
    );
  },
};
