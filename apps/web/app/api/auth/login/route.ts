import { NextRequest, NextResponse } from "next/server";
import { authConfig, publicOrigin, createSession, passwordMatches, sameOrigin, SESSION_COOKIE, sessionCookieOptions } from "../../../../lib/auth/session";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ error: "invalid_origin" }, { status: 403 });
  try {
    const config = authConfig();
    if (!config) return NextResponse.redirect(new URL("/", publicOrigin(request)), 303);
    const form = await request.formData();
    const password = form.get("password");
    if (typeof password !== "string" || !passwordMatches(password, config)) {
      return NextResponse.redirect(new URL("/login?error=invalid", publicOrigin(request)), 303);
    }
    const response = NextResponse.redirect(new URL("/", publicOrigin(request)), 303);
    response.cookies.set(SESSION_COOKIE, createSession(config), sessionCookieOptions());
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.json({ error: "auth_unavailable" }, { status: 503 });
  }
}
