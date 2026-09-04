import { NextRequest, NextResponse } from "next/server";
import { authConfig, publicOrigin, SESSION_COOKIE, validSession } from "./lib/auth/session";

export function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (path === "/login" || path.startsWith("/api/") || path.startsWith("/_next/") || path === "/favicon.ico") {
    return NextResponse.next();
  }
  try {
    const config = authConfig();
    if (!config || validSession(request.cookies.get(SESSION_COOKIE)?.value, config)) return NextResponse.next();
    return NextResponse.redirect(new URL("/login", publicOrigin(request)));
  } catch {
    return new NextResponse("登录配置不完整，请联系管理员。", { status: 503 });
  }
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
