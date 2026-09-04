// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST } from "../app/api/v1/[...path]/route";

const context = { params: Promise.resolve({ path: ["workspace"] }) };
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

describe("protected API proxy", () => {
  it("rejects anonymous requests before contacting the protected API", async () => {
    vi.stubEnv("AUTH_TOKEN", "private-api-token");
    vi.stubEnv("FLOW_WEB_PASSWORD", "web-test-password");
    const upstream = vi.fn(); vi.stubGlobal("fetch", upstream);
    const result = await GET(new NextRequest("http://localhost/api/v1/workspace"), context);
    expect(result.status).toBe(401);
    expect(upstream).not.toHaveBeenCalled();
  });
  it("fails closed with incomplete authentication configuration", async () => {
    vi.stubEnv("AUTH_TOKEN", "private-api-token"); vi.stubEnv("FLOW_WEB_PASSWORD", "");
    const upstream = vi.fn(); vi.stubGlobal("fetch", upstream);
    expect((await GET(new NextRequest("http://localhost/api/v1/workspace"), context)).status).toBe(503);
    expect(upstream).not.toHaveBeenCalled();
  });
  it("preserves incoming bearer credentials in open local development", async () => {
    vi.stubEnv("AUTH_TOKEN", ""); vi.stubEnv("FLOW_WEB_PASSWORD", "");
    const upstream = vi.fn().mockResolvedValue(Response.json({ ok: true })); vi.stubGlobal("fetch", upstream);
    await POST(new NextRequest("http://localhost/api/v1/workspace", { method: "POST", headers: { Authorization: "Bearer caller", "Content-Type": "application/json" }, body: "{}" }), context);
    expect(new Headers(upstream.mock.calls[0][1].headers).get("authorization")).toBe("Bearer caller");
  });
});
it("requires a public origin for protected production deployments", async () => {
  vi.stubEnv("NODE_ENV", "production"); vi.stubEnv("AUTH_TOKEN", "private-api-token");
  vi.stubEnv("FLOW_WEB_PASSWORD", "web-test-password"); vi.stubEnv("FLOW_WEB_ORIGIN", "");
  expect((await GET(new NextRequest("http://localhost/api/v1/workspace"), context)).status).toBe(503);
});
