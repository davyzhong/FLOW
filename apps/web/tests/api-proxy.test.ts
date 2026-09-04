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

it("preserves download metadata and exact bytes through the proxy", async () => {
  const bytes = new Uint8Array([0, 80, 75, 255, 10]);
  const result = await bufferedProxyResponse(new Response(bytes, {
    headers: {
      "content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "content-disposition": 'attachment; filename="flow-report-v1.pptx"',
      "cache-control": "no-store", "x-content-type-options": "nosniff",
      "set-cookie": "upstream-secret=hidden",
    },
  }));
  expect(result.headers.get("content-disposition")).toBe('attachment; filename="flow-report-v1.pptx"');
  expect(result.headers.get("cache-control")).toBe("no-store");
  expect(result.headers.get("x-content-type-options")).toBe("nosniff");
  expect(result.headers.get("set-cookie")).toBeNull();
  expect(new Uint8Array(await result.arrayBuffer())).toEqual(bytes);
});
