// @vitest-environment node
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST as login } from "../app/api/auth/login/route";
import { POST as logout } from "../app/api/auth/logout/route";
import { GET, POST } from "../app/api/v1/[...path]/route";
import { proxy } from "../proxy";
import { authConfig, createSession, SESSION_COOKIE, validSession } from "../lib/auth/session";

beforeEach(() => { vi.stubEnv("AUTH_TOKEN", "private-api-token"); vi.stubEnv("FLOW_WEB_PASSWORD", "web-test-password"); });
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
const context = { params: Promise.resolve({ path: ["workspace"] }) };
const config = () => authConfig()!;
function request(path: string, password: string, origin = "http://localhost") {
  return new NextRequest(`http://localhost${path}`, { method: "POST", headers: { Origin: origin, "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ password }) });
}

it("logs in and grants the API only a signed session, never the backend token", async () => {
  const response = await login(request("/api/auth/login", "web-test-password"));
  expect(response.status).toBe(303);
  const cookie = response.cookies.get(SESSION_COOKIE)!;
  expect(cookie.value).not.toContain("private-api-token");
  expect(cookie.value).not.toContain("web-test-password");
  expect(response.headers.get("set-cookie")).toContain("HttpOnly");
  expect(response.headers.get("set-cookie")).toContain("SameSite=strict");
  const upstream = vi.fn().mockResolvedValue(Response.json({ ok: true })); vi.stubGlobal("fetch", upstream);
  const result = await GET(new NextRequest("http://localhost/api/v1/workspace", { headers: { Cookie: `${SESSION_COOKIE}=${cookie.value}`, Authorization: "Bearer attacker" } }), context);
  expect(result.status).toBe(200);
  expect(new Headers(upstream.mock.calls[0][1].headers).get("authorization")).toBe("Bearer private-api-token");
  expect(new Headers(upstream.mock.calls[0][1].headers).get("cookie")).toBeNull();
});
it("does not issue sessions for invalid passwords or cross-origin login", async () => {
  expect((await login(request("/api/auth/login", "wrong"))).cookies.get(SESSION_COOKIE)).toBeUndefined();
  expect((await login(request("/api/auth/login", "web-test-password", "https://other.test"))).status).toBe(403);
});
it("rejects tampering, expired sessions and credential rotation", () => {
  const value = createSession(config(), 1700000000000);
  expect(validSession(value, config(), 1700000000000)).toBe(true);
  expect(validSession(`${value.slice(0, -1)}${value.endsWith("0") ? "1" : "0"}`, config(), 1700000000000)).toBe(false);
  expect(validSession(value, config(), 1700030000000)).toBe(false);
  expect(validSession(value, { ...config(), password: "rotated" }, 1700000000000)).toBe(false);
});
it("blocks cross-origin writes even with a valid session", async () => {
  const upstream = vi.fn(); vi.stubGlobal("fetch", upstream);
  const result = await POST(new NextRequest("http://localhost/api/v1/workspace", { method: "POST", headers: { Cookie: `${SESSION_COOKIE}=${createSession(config())}`, Origin: "https://other.test" }, body: "{}" }), context);
  expect(result.status).toBe(403); expect(upstream).not.toHaveBeenCalled();
});
it("redirects unauthenticated pages but lets authenticated pages through", () => {
  expect(proxy(new NextRequest("http://localhost/reports")).headers.get("location")).toBe("http://localhost/login");
  expect(proxy(new NextRequest("http://localhost/reports", { headers: { Cookie: `${SESSION_COOKIE}=${createSession(config())}` } })).headers.get("location")).toBeNull();
});
it("sets Secure in production and clears the cookie on logout", async () => {
  vi.stubEnv("NODE_ENV", "production");
  vi.stubEnv("FLOW_WEB_ORIGIN", "http://localhost");
  expect((await login(request("/api/auth/login", "web-test-password"))).headers.get("set-cookie")).toContain("Secure");
  const response = await logout(request("/api/auth/logout", ""));
  expect(response.cookies.get(SESSION_COOKIE)?.value).toBe("");
  expect(response.headers.get("set-cookie")).toContain("Max-Age=0");
});
it("uses the configured public origin behind a reverse proxy", async () => {
  vi.stubEnv("FLOW_WEB_ORIGIN", "https://flow.example.com");
  const result = await login(new NextRequest("http://0.0.0.0:3000/api/auth/login", { method: "POST", headers: { Origin: "https://flow.example.com", "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ password: "web-test-password" }) }));
  expect(result.status).toBe(303);
  expect(result.headers.get("location")).toBe("https://flow.example.com/");
  expect(proxy(new NextRequest("http://0.0.0.0:3000/data")).headers.get("location")).toBe("https://flow.example.com/login");
});
