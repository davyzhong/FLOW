import type { components } from "@flow/contracts";

export type WorkspaceResponse = components["schemas"]["WorkspaceResponse"];

const API_BASE_URL = process.env.NEXT_PUBLIC_FLOW_API_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`FLOW API request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export const flowApi = {
  getWorkspace(): Promise<WorkspaceResponse> {
    return request<WorkspaceResponse>("/api/v1/workspace");
  },
};
