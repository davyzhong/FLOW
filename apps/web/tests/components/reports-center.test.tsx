import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

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
const OPERATIONS_SNAPSHOT = {
  id: "ops-snap-1",
  statement_report_id: "statement-1",
  version: 1,
  company_name: "菜鸟智慧物流网络",
  stock_code: "CAINIAO",
  period_label: "FY2023",
  payload_hash: "c".repeat(64),
  created_at: "2026-09-12T09:00:00+08:00",
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

  it("registers operations reports and publishes PPTX/XLSX through append-only attempts", async () => {
    const operationsAttempt = { ...ATTEMPT, attempt_id: "ops-attempt-1", format: "xlsx" };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/statements")) return jsonResponse({ reports: [] });
      if (url.endsWith("/operations/snapshots")) {
        return jsonResponse({ snapshots: [OPERATIONS_SNAPSHOT] });
      }
      if (url.endsWith("/operations/snapshots/ops-snap-1/attempts")) {
        return jsonResponse({ report_snapshot_id: "ops-snap-1", attempts: [operationsAttempt] });
      }
      if (url.endsWith("/operations/overview/statement-1/publish") && method === "POST") {
        expect(String(init?.body)).toContain('"pptx"');
        expect(String(init?.body)).toContain('"xlsx"');
        return jsonResponse({
          report_snapshot_id: "ops-snap-1",
          outcomes: { pptx: "succeeded", xlsx: "succeeded" },
        });
      }
      if (url.endsWith("/publishing/snapshots")) return jsonResponse({ snapshots: [] });
      if (url.endsWith("/publishing/freeze-candidates")) return jsonResponse({ candidates: [] });
      return jsonResponse({ detail: { code: "not_found", message: "unknown" } }, 404);
    });
    vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

    render(<ReportsCenter />);
    expect(await screen.findByText(/菜鸟智慧物流网络 · FY2023 · v1/)).toBeInTheDocument();
    expect(screen.getByText("经营报告产物历史（append-only）")).toBeInTheDocument();
    expect((await screen.findAllByText("XLSX")).length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getByRole("button", { name: "生成经营报告产物" }));
    await vi.waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([input]) =>
          String(input).endsWith("/operations/overview/statement-1/publish"),
        ),
      ).toBe(true),
    );
  });
});

it.each(["pptx", "xlsx", "html", "pdf"])("downloads %s with its extension when upstream filename is absent", async (format) => {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/download")) return new Response(new Uint8Array([0, 1, 255]));
    if (url.endsWith("/attempts")) return jsonResponse({ attempts: [{ ...ATTEMPT, format }] });
    return jsonResponse({ snapshots: [SNAPSHOT] });
  }));
  Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:report") });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
  let filename = "";
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function(this: HTMLAnchorElement) {
    filename = this.download;
  });
  render(<ReportsCenter />);
  fireEvent.click(await screen.findByRole("button", { name: "下载" }));
  await vi.waitFor(() => expect(filename).toMatch(new RegExp(`\\.${format}$`)));
  click.mockRestore();
});
