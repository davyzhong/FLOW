import { afterEach, describe, expect, it, vi } from "vitest";

import { flowApi } from "../lib/api/client";

describe("FLOW API client", () => {
  afterEach(() => vi.restoreAllMocks());

  it("loads the versioned workspace contract", async () => {
    const payload = {
      workspace_id: "flow-v1",
      name: "FLOW",
      primary_role: "finance_bp",
      industry: "logistics_supply_chain",
      timezone: "Asia/Shanghai",
      currency: "CNY",
    } as const;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(flowApi.getWorkspace()).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/workspace",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });
});
