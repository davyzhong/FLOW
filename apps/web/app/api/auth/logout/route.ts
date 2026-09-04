import { NextRequest, NextResponse } from "next/server";
import { publicOrigin, sameOrigin, SESSION_COOKIE, sessionCookieOptions } from "../../../../lib/auth/session";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ error: "invalid_origin" }, { status: 403 });
  const response = NextResponse.redirect(new URL("/login", publicOrigin(request)), 303);
  response.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions(), maxAge: 0 });
  response.headers.set("Cache-Control", "no-store");
  return response;
}
