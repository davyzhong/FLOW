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

export type CopilotAnswer = {
  interaction_id: string;
  outcome: string;
  context_digest: string;
  provider: string;
  model: string;
  template_version: string;
  answer: {
    facts: CopilotSectionInput[];
    judgments: CopilotSectionInput[];
    hypotheses: CopilotSectionInput[];
    questions: CopilotSectionInput[];
    degradation: "none" | "insufficient_data";
  };
};

export type CopilotSectionInput = {
  text: string;
  citations: readonly string[];
};

export type CopilotQuestionInput = {
  question: string;
  actor: string;
  batch_id?: string | null;
  metric_snapshot_id?: string | null;
  analysis_run_id?: string | null;
};

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
  askCopilot(
    findingId: string,
    input: CopilotQuestionInput,
  ): Promise<CopilotAnswer> {
    return submit<CopilotAnswer>(
      `/api/v1/copilot/investigations/${findingId}/ask`,
      "POST",
      input,
    );
  },
};

export type IntakeBatch = { id: string; name: string; status: string };
export type IntakeSource = { id: string; sha256: string; size_bytes: number };
export type IntakeMapping = {
  id: string;
  sequence: number;
  sheets: {
    source_sheet: string;
    target_sheet_id: string;
    fields: {
      target_field_id: string;
      source_header: string;
      source_column: string;
      method: string;
      confidence: string;
    }[];
    unresolved_required_fields: string[];
  }[];
  confidence_summary: Record<string, number>;
  confirmed_by: string | null;
};
export type IntakeImport = {
  id: string;
  status: string;
  is_published: boolean;
  issues: {
    id: string; severity: "blocking" | "warning"; code: string; message: string;
    evidence: string; repair_suggestion: string; sheet_name: string | null;
    source_row: number | null; source_column: string | null; acknowledged: boolean;
  }[];
  reconciliations: {
    code: string; passed: boolean; expected_value: string | null;
    actual_value: string | null; details: Record<string, unknown>;
  }[];
  next_allowed_actions: string[];
};

export type MappingOverrideInput = {
  target_sheet_id: string;
  target_field_id: string;
  source_sheet: string;
  source_header: string;
};

async function download(path: string, fallbackFilename: string): Promise<void> {
  const response = await fetch(requestUrl(path), {
    headers: { Accept: "application/octet-stream" },
  });
  if (!response.ok) {
    throw new FlowApiError(response.status, `upstream_status_${response.status}`, "下载失败");
  }
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = /filename="([^"]+)"/.exec(disposition);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = match?.[1] ?? fallbackFilename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("workbook", file, file.name);
  const response = await fetch(requestUrl(path), { method: "POST", body: form });
  if (!response.ok) {
    throw new FlowApiError(response.status, `upstream_status_${response.status}`, "上传失败");
  }
  return (await response.json()) as T;
}

export const intakeApi = {
  createBatch(name: string): Promise<IntakeBatch> {
    return submit<IntakeBatch>("/api/v1/intake/batches", "POST", { name });
  },
  uploadSource(batchId: string, file: File): Promise<IntakeSource> {
    return uploadFile<IntakeSource>(`/api/v1/intake/batches/${batchId}/sources`, file);
  },
  async downloadTemplate(): Promise<void> {
    await download("/api/v1/intake/templates/flow.excel.v1", "flow.excel.v1.template.xlsx");
  },
  proposeMapping(sourceId: string): Promise<IntakeMapping> {
    return submit<IntakeMapping>(`/api/v1/intake/sources/${sourceId}/mapping-proposals`, "POST", {});
  },
  confirmMapping(mappingId: string, actor: string): Promise<IntakeMapping> {
    return submit<IntakeMapping>(`/api/v1/intake/mappings/${mappingId}/confirm`, "POST", {
      actor,
    });
  },
  applyOverrides(
    mappingId: string,
    sourceFileId: string,
    sourceSha256: string,
    overrides: MappingOverrideInput[],
    actor: string,
  ): Promise<IntakeMapping> {
    return submit<IntakeMapping>(`/api/v1/intake/mappings/${mappingId}/overrides`, "POST", {
      actor,
      source_file_id: sourceFileId,
      source_sha256: sourceSha256,
      overrides,
    });
  },
  validateImport(sourceId: string, mappingId: string): Promise<IntakeImport> {
    return submit<IntakeImport>(`/api/v1/intake/sources/${sourceId}/validate`, "POST", {
      mapping_version_id: mappingId,
    });
  },
  async getImportVersion(batchId: string, importId: string): Promise<IntakeImport> {
    const history = await request<{ versions: IntakeImport[] }>(`/api/v1/intake/batches/${batchId}/versions`);
    const version = history.versions.find((item) => item.id === importId);
    if (!version) throw new Error("导入版本不存在");
    return version;
  },
  acknowledgeWarning(issueId: string, actor: string, reason: string) {
    return submit<unknown>(`/api/v1/intake/issues/${issueId}/acknowledge`, "POST", {
      actor,
      reason,
    });
  },
  publishImport(importId: string): Promise<IntakeImport> {
    return submit<IntakeImport>(`/api/v1/intake/imports/${importId}/publish`, "POST", {});
  },
  async exportStandardizedWorkbook(importId: string): Promise<void> {
    await download(
      `/api/v1/intake/imports/${importId}/standardized-workbook`,
      "flow.excel.v1.standardized.xlsx",
    );
  },
  getCleaningSummary(
    importId: string,
    signal?: AbortSignal,
  ): Promise<{
    status: string;
    totals: { raw_values: number; transformed_values: number; records: number };
    transform_rules: {
      rule_id: string;
      rule_version: number;
      applied_count: number;
      samples: Record<string, unknown>[];
    }[];
    quality_issues: { blocking: number; warning: number };
    reconciliation: { passed: number; failed: number };
  }> {
    return request(`/api/v1/intake/imports/${importId}/cleaning-summary`, signal);
  },
};
