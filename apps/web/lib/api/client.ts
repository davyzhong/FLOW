import type { components, operations } from "@flow/contracts";

export type WorkspaceResponse = components["schemas"]["WorkspaceResponse"];
export type DashboardResponse = components["schemas"]["DashboardOverviewResponse"];
export type DashboardFilters = NonNullable<
  operations["dashboard_overview_api_v1_dashboard_overview_get"]["parameters"]["query"]
>;
export type InvestigationContext = components["schemas"]["InvestigationContextResponse"];
export type InvestigationAcknowledgement =
  | components["schemas"]["EvidenceDecisionResponse"]
  | components["schemas"]["ConclusionResponse"]
  | components["schemas"]["FindingTransitionResponse"];

export type InvestigationQuery = {
  finding_id: string;
  batch_id?: string | null;
  metric_snapshot_id?: string | null;
  analysis_run_id?: string | null;
};

export type EvidenceDecisionInput = {
  decision: "verified" | "rejected";
  reviewer: string;
  comment?: string | null;
};

export type ConclusionInput = {
  verified_facts: string;
  analysis_judgment: string;
  open_questions: string;
  recommendation: string;
  editor: string;
};

export type FindingTransitionInput = {
  decision: "submitted" | "approved" | "rejected" | "returned";
  reviewer: string;
  comment?: string | null;
};

export class FlowApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_FLOW_API_URL ?? "";

function requestUrl(path: string): URL {
  if (!path.startsWith("/api/v1/") || path.includes("..")) {
    throw new Error(`FLOW API request path is not allow-listed: ${path}`);
  }
  const base =
    API_BASE_URL === "" && typeof globalThis.location?.origin === "string"
      ? globalThis.location.origin
      : API_BASE_URL;
  return new URL(path, base || undefined);
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(requestUrl(path), {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`FLOW API request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

type ErrorBody = { detail?: { code?: string; message?: string } };

async function submit<T>(
  path: string,
  method: "POST" | "PUT",
  body: unknown,
): Promise<T> {
  const response = await fetch(requestUrl(path), {
    method,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let code = `upstream_status_${response.status}`;
    let message = `FLOW API request failed with status ${response.status}`;
    try {
      const parsed = (await response.json()) as ErrorBody;
      if (parsed.detail?.code) code = parsed.detail.code;
      if (parsed.detail?.message) message = parsed.detail.message;
    } catch {
      // keep fallback message
    }
    throw new FlowApiError(response.status, code, message);
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
  getInvestigation(
    query: InvestigationQuery,
    signal?: AbortSignal,
  ): Promise<InvestigationContext> {
    const parameters = new URLSearchParams();
    for (const key of ["batch_id", "metric_snapshot_id", "analysis_run_id"] as const) {
      const value = query[key];
      if (value) parameters.set(key, value);
    }
    const suffix = parameters.toString();
    return request<InvestigationContext>(
      `/api/v1/investigations/${query.finding_id}${suffix ? `?${suffix}` : ""}`,
      signal,
    );
  },
  decideEvidence(
    findingId: string,
    evidenceId: string,
    input: EvidenceDecisionInput,
  ): Promise<InvestigationAcknowledgement> {
    return submit<InvestigationAcknowledgement>(
      `/api/v1/investigations/${findingId}/evidence/${evidenceId}/decision`,
      "POST",
      input,
    );
  },
  saveConclusion(
    findingId: string,
    input: ConclusionInput,
  ): Promise<InvestigationAcknowledgement> {
    return submit<InvestigationAcknowledgement>(
      `/api/v1/investigations/${findingId}/conclusion`,
      "PUT",
      input,
    );
  },
  transitionFinding(
    findingId: string,
    input: FindingTransitionInput,
  ): Promise<InvestigationAcknowledgement> {
    return submit<InvestigationAcknowledgement>(
      `/api/v1/investigations/${findingId}/transition`,
      "POST",
      input,
    );
  },
};
