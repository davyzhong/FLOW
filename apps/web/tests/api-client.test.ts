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

  it("loads the dashboard only through the typed overview boundary", async () => {
    const payload = { state: "ready", metric_cards: [] };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(
      flowApi.getDashboard({
        period_view: "ytd",
        customer_segment_id: "158e0a75-4853-5f1a-94b1-da561ccdd70a",
        logistics_product_id: "f3aa874c-c0d5-5e2c-bf5b-d0e51a9c624c",
      }),
    ).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/dashboard/overview?period_view=ytd&customer_segment_id=158e0a75-4853-5f1a-94b1-da561ccdd70a&logistics_product_id=f3aa874c-c0d5-5e2c-bf5b-d0e51a9c624c",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
    expect(fetchMock.mock.calls[0]?.[0]).not.toContain("canonical");
    expect(fetchMock.mock.calls[0]?.[0]).not.toContain("metric-values");
  });
});
