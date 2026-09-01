import type { NextRequest } from "next/server";

const apiInternalUrl = process.env.FLOW_API_INTERNAL_URL ?? "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const upstream = new URL(`/api/v1/${path.join("/")}`, apiInternalUrl);
  upstream.search = request.nextUrl.search;
  try {
    const response = await fetch(upstream, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    return new Response(response.body, {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return Response.json(
      { detail: { code: "upstream_unavailable", message: "FLOW API 暂时不可用" } },
      { status: 502 },
    );
  }
}
