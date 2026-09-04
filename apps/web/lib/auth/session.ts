import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";

export const SESSION_COOKIE = "flow_session";
export const SESSION_SECONDS = 8 * 60 * 60;

type AuthConfig = { token: string; password: string };
export function authConfig(): AuthConfig | null {
  const token = process.env.AUTH_TOKEN ?? "";
  const password = process.env.FLOW_WEB_PASSWORD ?? "";
  if (!token && !password) return null;
  if (!token || !password || (process.env.NODE_ENV === "production" && !process.env.FLOW_WEB_ORIGIN)) {
    throw new Error("Incomplete web authentication configuration");
  }
  return { token, password };
}

function signature(payload: string, config: AuthConfig): string {
  // Bind sessions to both credentials so rotating either invalidates existing cookies.
  return createHmac("sha256", JSON.stringify([config.token, config.password]))
    .update(`flow-web-session:v1:${payload}`).digest("hex");
}

function equal(left: string, right: string): boolean {
  const a = Buffer.from(left); const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function passwordMatches(value: string, config: AuthConfig): boolean {
  // Hash first to compare fixed-length values even when password lengths differ.
  return equal(signature(value, config), signature(config.password, config));
}

export function createSession(config: AuthConfig, now = Date.now()): string {
  const payload = `${Math.floor(now / 1000) + SESSION_SECONDS}.${randomBytes(24).toString("hex")}`;
  return `${payload}.${signature(payload, config)}`;
}

export function validSession(value: string | undefined, config: AuthConfig, now = Date.now()): boolean {
  if (!value || !/^\d{10}\.[a-f0-9]{48}\.[a-f0-9]{64}$/.test(value)) return false;
  const [expires, nonce, mac] = value.split(".");
  const seconds = Math.floor(now / 1000);
  if (Number(expires) <= seconds || Number(expires) > seconds + SESSION_SECONDS) return false;
  return equal(mac, signature(`${expires}.${nonce}`, config));
}

export function publicOrigin(request: NextRequest): string {
  const configured = process.env.FLOW_WEB_ORIGIN;
  if (!configured) return request.nextUrl.origin;
  const url = new URL(configured);
  if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("Invalid public web origin");
  }
  return url.origin;
}

export function sameOrigin(request: NextRequest): boolean {
  return request.headers.get("origin") === publicOrigin(request);
}

export function sessionCookieOptions() {
  return { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict" as const, path: "/", maxAge: SESSION_SECONDS };
}
