import { describe, expect, it, vi } from "vitest";
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

// 批次一 §2.1/§2.2/§2.3：/reports?snapshot= 与 ?focus= 接收、互链链接。
describe("ReportsCenter 深链", () => {
  function stubFullCenter() {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/statements")) {
        return jsonResponse({
          reports: [
            {
              id: "report-1",
              company_name: "顺丰控股",
              stock_code: "002352.SZ",
              report_kind: "一季报",
              period_label: "2026Q1",
              unit_note: "人民币千元",
              source_ref: "p5_samples/sf.pdf",
              source_sha256: null,
              statement_types: [],
              line_item_count: 3,
              created_at: "2026-09-06T08:00:00+00:00",
            },
          ],
        });
      }
      if (url.endsWith("/publishing/snapshots")) {
        return jsonResponse({
          snapshots: [
            SNAPSHOT,
            { ...SNAPSHOT, id: "snap-2", metric_snapshot_id: "ms-2", title: "2026-07 经营月报", version: 2 },
          ],
        });
      }
      if (url.endsWith("/publishing/freeze-candidates")) {
        return jsonResponse({
          candidates: [
            {
              metric_snapshot_id: "ms-candidate-1",
              batch_id: "batch-1",
              period_label: "2026-08",
              version: 3,
              approved_findings: 2,
              created_at: "2026-09-03T09:00:00+08:00",
            },
          ],
        });
      }
      if (url.endsWith("/operations/snapshots")) return jsonResponse({ snapshots: [OPERATIONS_SNAPSHOT] });
      if (url.includes("/attempts")) return jsonResponse({ attempts: [] });
      return jsonResponse({ detail: { code: "not_found", message: "unknown" } }, 404);
    });
    vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);
  }

  it("?snapshot= 初始选中对应报告快照（按 id 或 metric_snapshot_id 匹配）", async () => {
    stubFullCenter();
    render(<ReportsCenter initialSnapshot="snap-2" />);
    const radio = await screen.findByRole("radio", { name: /2026-07 经营月报/ });
    expect(radio).toBeChecked();
    expect(screen.queryByText(/未找到快照/)).not.toBeInTheDocument();
  });

  it("?focus= 初始选中冻结候选的指标快照", async () => {
    stubFullCenter();
    render(<ReportsCenter initialFocus="ms-candidate-1" />);
    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("ms-candidate-1"));
    expect(screen.queryByText(/未找到指标快照/)).not.toBeInTheDocument();
  });

  it("快照参数不存在时显式提示，不静默忽略", async () => {
    stubFullCenter();
    render(<ReportsCenter initialSnapshot="missing-snapshot" />);
    expect(await screen.findByText(/未找到快照「missing-snapshot」/)).toBeInTheDocument();
  });

  it("客观财报条目追加「查看分析」、经营快照行链回经营分析、冻结提示链回 Investigation", async () => {
    stubFullCenter();
    render(<ReportsCenter />);
    const analyze = await screen.findByRole("link", { name: "查看分析" });
    expect(analyze).toHaveAttribute("href", "/statements?report=report-1");
    const backToOps = await screen.findByRole("link", { name: "在经营分析中查看" });
    expect(backToOps).toHaveAttribute("href", "/operations?report=statement-1");
    expect(screen.getByRole("link", { name: "Investigation 流程" })).toHaveAttribute(
      "href",
      "/investigations",
    );
  });
});
