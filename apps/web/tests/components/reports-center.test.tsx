import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ReportsCenter } from "../../components/reports/reports-center";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const SNAPSHOT = {
  id: "snap-1",
  metric_snapshot_id: "ms-1",
  version: 1,
  title: "2026-08 经营月报",
  created_at: "2026-09-03T09:00:00+08:00",
};
const ATTEMPT = {
  attempt_id: "attempt-1",
  sequence: 1,
  format: "html",
  status: "succeeded",
  stored_object_id: "obj-1",
  error_message: null,
  size_bytes: 1024,
  content_type: "text/html; charset=utf-8",
  created_at: "2026-09-03T09:05:00+08:00",
  download_available: true,
  stored_sha256: "b".repeat(64),
};

describe("ReportsCenter", () => {
  it("loads snapshots, publishes selected formats, and exposes downloads", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/publishing/snapshots") && method === "GET") {
        return jsonResponse({ snapshots: [SNAPSHOT] });
      }
      if (url.includes("/attempts") && method === "GET") {
        return jsonResponse({ report_snapshot_id: SNAPSHOT.id, attempts: [ATTEMPT] });
      }
      if (url.endsWith("/publish") && method === "POST") {
        expect(String(init?.body)).toContain('"html"');
        return jsonResponse({ report_snapshot_id: SNAPSHOT.id, outcomes: { html: "succeeded" } });
      }
      return jsonResponse({ detail: { code: "not_found", message: "unknown" } }, 404);
    });
    vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

    render(<ReportsCenter />);
    expect(await screen.findByText("报告快照")).toBeInTheDocument();
    expect(screen.getByText(/2026-08 经营月报/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "生成选中格式" }));
    expect(
      await screen.findByText(/产物历史/),
    ).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "下载" })).toBeInTheDocument();
    expect(screen.getByText("succeeded")).toBeInTheDocument();
  });
});
