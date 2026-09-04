import type { NextRequest } from "next/server";
import { authConfig, sameOrigin, SESSION_COOKIE, validSession } from "../../../../lib/auth/session";

const apiInternalUrl = process.env.FLOW_API_INTERNAL_URL ?? "http://127.0.0.1:8000";

type RouteContext = { params: Promise<{ path: string[] }> };

export async function bufferedProxyResponse(response: Response): Promise<Response> {
  const body = await response.arrayBuffer();
  const headers = new Headers({
    "content-type": response.headers.get("content-type") ?? "application/json",
  });
  for (const name of ["content-disposition", "cache-control", "x-content-type-options"]) {
    const value = response.headers.get(name);
    if (value) headers.set(name, value);
  }
  return new Response(body, {
    status: response.status,
    headers,
  });
}

async function forward(request: NextRequest, context: RouteContext): Promise<Response> {
  let authorization = request.headers.get("authorization");
  try {
    const config = authConfig();
    if (config) {
      if (!validSession(request.cookies.get(SESSION_COOKIE)?.value, config)) {
        return Response.json({ detail: { code: "unauthorized", message: "请先登录" } }, { status: 401 });
      }
      if (!["GET", "HEAD"].includes(request.method) && !sameOrigin(request)) {
        return Response.json({ detail: { code: "invalid_origin", message: "请求来源无效" } }, { status: 403 });
      }
      authorization = `Bearer ${config.token}`;
    }
  } catch {
    return Response.json({ detail: { code: "auth_unavailable", message: "登录配置不完整" } }, { status: 503 });
  }
  const { path } = await context.params;
  const upstream = new URL(`/api/v1/${path.join("/")}`, apiInternalUrl);
  upstream.search = request.nextUrl.search;
  const contentType = request.headers.get("content-type") ?? "application/json";
  const isRead = request.method === "GET" || request.method === "HEAD";
  try {
    // multipart（文件上传）必须整体转发：request.text() 会破坏二进制边界
    const body = isRead
      ? undefined
      : contentType.includes("multipart/form-data")
        ? await request.formData()
        : await request.text();
    const response = await fetch(upstream, {
      method: request.method,
      headers: {
        Accept: "application/json",
        ...(authorization ? { Authorization: authorization } : {}),
        ...(isRead || body instanceof FormData ? {} : { "Content-Type": contentType }),
      },
      body,
      cache: "no-store",
    });
    return bufferedProxyResponse(response);
  } catch {
    return Response.json(
      { detail: { code: "upstream_unavailable", message: "FLOW API 暂时不可用" } },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext): Promise<Response> {
  return forward(request, context);
}

export async function POST(request: NextRequest, context: RouteContext): Promise<Response> {
  return forward(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext): Promise<Response> {
  return forward(request, context);
}
