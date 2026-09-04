import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DataWorkbench } from "../../components/data/data-workbench";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const BATCH = { id: "batch-1", name: "8月报告", status: "draft" };
const SOURCE = { id: "source-1", sha256: "a".repeat(64), size_bytes: 1024 };
const MAPPING = {
  id: "mapping-1",
  sequence: 1,
  confirmed_by: null,
  confidence_summary: { high: 2 },
  unresolved_sheet_ids: [],
  sheets: [
    {
      source_sheet: "运营明细",
      target_sheet_id: "fact_operating_actual",
      unresolved_required_fields: [],
      fields: [
        {
          target_field_id: "revenue",
          source_header: "收入金额",
          source_column: "C",
          method: "stable_field_id",
          confidence: "high",
        },
        {
          target_field_id: "order_count",
          source_header: "订单数",
          source_column: "D",
          method: "display_name",
          confidence: "medium",
        },
      ],
    },
  ],
};
const IMPORT_VERSION = { id: "import-1", status: "ready", is_published: false };
const SUMMARY = {
  status: "ready",
  totals: { raw_values: 120, transformed_values: 24, records: 12 },
  transform_rules: [
    {
      rule_id: "trim_text",
      rule_version: 3,
      applied_count: 24,
      samples: [{ sheet_name: "运营明细", source_row: 2 }],
    },
  ],
  quality_issues: { blocking: 0, warning: 2 },
  reconciliation: { passed: 3, failed: 0 },
};

function mockFetchForHappyPath() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.includes("/api/v1/intake/batches") && method === "POST") {
      return jsonResponse(BATCH, 201);
    }
    if (url.endsWith("/sources") && method === "POST") {
      return jsonResponse(SOURCE, 201);
    }
    if (url.endsWith("/mapping-proposals") && method === "POST") {
      return jsonResponse(MAPPING, 201);
    }
    if (url.endsWith("/overrides") && method === "POST") {
      return jsonResponse({ ...MAPPING, id: "mapping-2", sequence: 2 }, 201);
    }
    if (url.endsWith("/confirm") && method === "POST") {
      return jsonResponse({ ...MAPPING, confirmed_by: "finance.bp@example.com" }, 200);
    }
    if (url.endsWith("/validate") && method === "POST") {
      return jsonResponse(IMPORT_VERSION, 201);
    }
    if (url.includes("/cleaning-summary")) {
      return jsonResponse(SUMMARY);
    }
    if (url.endsWith("/publish") && method === "POST") {
      return jsonResponse({ ...IMPORT_VERSION, status: "published", is_published: true }, 200);
    }
    return jsonResponse({ detail: { code: "not_found", message: "unknown" } }, 404);
  }) as unknown as typeof fetch;
}

function makeXlsxFile(): File {
  return new File([new Uint8Array([0x50, 0x4b])], "external.xlsx", {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}

describe("DataWorkbench", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetchForHappyPath());
  });

  it("renders the five stages with 准备 active and a template download action", () => {
    render(<DataWorkbench />);
    const stages = screen.getByLabelText("工作流阶段");
    expect(stages).toBeInTheDocument();
    expect(screen.getByText(/准备/)).toHaveAttribute("aria-current", "step");
    expect(screen.getByRole("button", { name: "下载 FLOW 标准模板" })).toBeInTheDocument();
  });

  it("walks upload → mapping → cleaning → publish from a chosen file", async () => {
    render(<DataWorkbench />);
    const input = screen.getByLabelText("选择文件");
    fireEvent.change(input, { target: { files: [makeXlsxFile()] } });

    expect(await screen.findByRole("table", {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText(/映射确认/)).toHaveAttribute("aria-current", "step");
    expect(screen.getByText("收入金额")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "确认映射并校验" }));
    expect(await screen.findByText("清洗与校验结果")).toBeInTheDocument();
    expect(screen.getByText(/原始值 120/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "发布此导入版本" }));
    expect(await screen.findByText("导入版本已发布")).toBeInTheDocument();
  });

  it("keeps the publish button keyboard-operable and announces published state", async () => {
    render(<DataWorkbench />);
    const input = screen.getByLabelText("选择文件");
    fireEvent.change(input, { target: { files: [makeXlsxFile()] } });
    fireEvent.click(await screen.findByRole("button", { name: "确认映射并校验" }));
    const publish = await screen.findByRole("button", { name: "发布此导入版本" });
    fireEvent.click(publish);
    expect(await screen.findByRole("status")).toHaveTextContent("导入版本已发布");
  });

  it("surfaces upload failures with an alert", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () => jsonResponse({ detail: { code: "rejected" } }, 500),
      ) as unknown as typeof fetch,
    );
    render(<DataWorkbench />);
    const input = screen.getByLabelText("选择文件");
    fireEvent.change(input, { target: { files: [makeXlsxFile()] } });
    const alert = await screen.findByRole(
      "alert",
      {},
      { timeout: 3000 },
    );
    expect(alert.textContent).toContain("500");
  });
});