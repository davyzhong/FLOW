import { describe, expect, it } from "vitest";

import { bufferedProxyResponse } from "../app/api/v1/[...path]/route";

describe("API proxy response buffering", () => {
  it("detaches the downstream response from the upstream body stream", async () => {
    const upstream = new Response(JSON.stringify({ state: "ready" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const upstreamBody = upstream.body;

    const downstream = await bufferedProxyResponse(upstream);

    expect(downstream.body).not.toBe(upstreamBody);
    expect(downstream.status).toBe(200);
    expect(downstream.headers.get("content-type")).toBe("application/json");
    await expect(downstream.json()).resolves.toEqual({ state: "ready" });
  });
});
