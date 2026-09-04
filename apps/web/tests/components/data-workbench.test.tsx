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
const WARNINGS = [1, 2].map((index) => ({
  id: `issue-${index}`, severity: "warning", code: `warning_${index}`,
  message: `警告 ${index}`, evidence: "原始值含空格", repair_suggestion: "核实原始凭证",
  sheet_name: "运营明细", source_row: index + 2, source_column: "C", acknowledged: false,
}));
const IMPORT_VERSION = { id: "import-1", status: "ready", is_published: false,
  issues: [], reconciliations: [], next_allowed_actions: ["publish"] };
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
  quality_issues: { blocking: 0, warning: 0 },
  reconciliation: { passed: 3, failed: 0 },
};

function mockFetchForHappyPath(options: { warnings?: boolean; blocked?: boolean; required?: boolean } = {}) {
  const acknowledged = new Set<string>();
  let validated = 0;
  const version = () => ({ ...IMPORT_VERSION,
    status: options.blocked && validated === 1 ? "blocked" : "ready",
    issues: options.blocked && validated === 1 ? [{ ...WARNINGS[0], severity: "blocking" }] :
      options.warnings ? WARNINGS.map((issue) => ({ ...issue, acknowledged: acknowledged.has(issue.id) })) : [],
    reconciliations: [{ code: "revenue_total", passed: true, expected_value: "100", actual_value: "100", details: {} }],
    next_allowed_actions: options.blocked && validated === 1 ? ["create_correction"] : ["acknowledge_warnings", "publish"],
  });
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.endsWith("/api/v1/intake/batches") && method === "POST") {
      return jsonResponse(BATCH, 201);
    }
    if (url.endsWith("/sources") && method === "POST") {
      return jsonResponse(SOURCE, 201);
    }
    if (url.endsWith("/mapping-proposals") && method === "POST") {
      return jsonResponse(options.required ? { ...MAPPING, sheets: [{ ...MAPPING.sheets[0], unresolved_required_fields: ["currency"] }] } : MAPPING, 201);
    }
    if (url.endsWith("/overrides") && method === "POST") {
      return jsonResponse({ ...MAPPING, id: "mapping-2", sequence: 2 }, 201);
    }
    if (url.endsWith("/confirm") && method === "POST") {
      return jsonResponse({ ...MAPPING, id: url.split("/").at(-2), confirmed_by: "finance.bp@example.com" }, 200);
    }
    if (url.endsWith("/validate") && method === "POST") {
      validated += 1;
      return jsonResponse(version(), 201);
    }
    if (url.endsWith("/versions")) return jsonResponse({ batch_id: BATCH.id, versions: [version()] });
    if (url.endsWith("/acknowledge")) {
      const issueId = url.split("/").at(-2)!;
      const body = JSON.parse(String(init?.body));
      if (!body.reason.trim()) return jsonResponse({}, 422);
      acknowledged.add(issueId);
      return jsonResponse({ quality_issue_id: issueId });
    }
    if (url.includes("/cleaning-summary")) {
      return jsonResponse(SUMMARY);
    }
    if (url.endsWith("/publish") && method === "POST") {
      if (version().issues.some((issue) => issue.severity === "blocking" || !issue.acknowledged)) {
        return jsonResponse({ detail: { code: "blocked", message: "质量问题未处理" } }, 409);
      }
      return jsonResponse({ ...version(), status: "published", is_published: true }, 200);
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
async function uploadAndValidate() {
  fireEvent.change(screen.getByLabelText("选择文件"), { target: { files: [makeXlsxFile()] } });
  fireEvent.click(await screen.findByRole("button", { name: "确认映射并校验" }));
  await screen.findByText("清洗与校验结果");
}

it("sends the uploaded source SHA when overriding mapping", async () => {
  vi.stubGlobal("fetch", mockFetchForHappyPath());
  render(<DataWorkbench />);
  fireEvent.change(screen.getByLabelText("选择文件"), { target: { files: [makeXlsxFile()] } });
  fireEvent.change(await screen.findByLabelText("覆盖 fact_operating_actual.revenue 的源表头"), { target: { value: "营业收入" } });
  fireEvent.click(screen.getByRole("button", { name: "确认映射并校验" }));
  await screen.findByText("清洗与校验结果");
  const call = vi.mocked(fetch).mock.calls.find(([url]) => String(url).endsWith("/overrides"))!;
  expect(JSON.parse(String(call[1]?.body))).toMatchObject({ source_file_id: SOURCE.id, source_sha256: SOURCE.sha256 });
  const validation = vi.mocked(fetch).mock.calls.find(([url]) => String(url).endsWith("/validate"))!;
  expect(JSON.parse(String(validation[1]?.body))).toMatchObject({ mapping_version_id: "mapping-2" });
});

it("requires a reason for every warning and refreshes server state before publishing", async () => {
  vi.stubGlobal("fetch", mockFetchForHappyPath({ warnings: true }));
  render(<DataWorkbench />);
  await uploadAndValidate();
  const publish = screen.getByRole("button", { name: "发布此导入版本" });
  expect(publish).toBeDisabled();
  expect(screen.getAllByText(/核实原始凭证/)).toHaveLength(2);
  expect(screen.getByText(/运营明细.*3.*C/)).toBeInTheDocument();
  expect(screen.getByText(/revenue_total/)).toBeInTheDocument();
  for (const index of [1, 2]) {
    const confirm = screen.getByRole("button", { name: `确认警告 issue-${index}` });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByLabelText(`警告 issue-${index} 确认原因`), { target: { value: "已核对凭证" } });
    fireEvent.click(confirm);
    await waitFor(() => expect(screen.queryByRole("button", { name: `确认警告 issue-${index}` })).not.toBeInTheDocument());
    if (index === 1) expect(publish).toBeDisabled();
  }
  expect(vi.mocked(fetch).mock.calls.filter(([url]) => String(url).endsWith("/versions"))).toHaveLength(2);
  expect(publish).toBeEnabled();
  fireEvent.click(publish);
  expect(await screen.findByText("导入版本已发布")).toBeInTheDocument();
});

it("returns blocked imports to mapping, including unresolved required fields, then revalidates", async () => {
  vi.stubGlobal("fetch", mockFetchForHappyPath({ blocked: true, required: true }));
  render(<DataWorkbench />);
  fireEvent.change(screen.getByLabelText("选择文件"), { target: { files: [makeXlsxFile()] } });
  expect(await screen.findByLabelText("覆盖 fact_operating_actual.currency 的源表头")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "确认映射并校验" }));
  expect(await screen.findByRole("button", { name: "发布此导入版本" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "返回修改映射" }));
  fireEvent.change(screen.getByLabelText("覆盖 fact_operating_actual.revenue 的源表头"), { target: { value: "营业收入" } });
  fireEvent.click(screen.getByRole("button", { name: "确认映射并校验" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "发布此导入版本" })).toBeEnabled());
  expect(vi.mocked(fetch).mock.calls.filter(([url]) => String(url).endsWith("/validate"))).toHaveLength(2);
});

it.each([
  ["not ready", { status: "validating" }],
  ["publish not allowed", { next_allowed_actions: ["validate"] }],
  ["blocking issue despite ready status", { issues: [{ ...WARNINGS[0], severity: "blocking", acknowledged: true }] }],
  ["failed reconciliation", { reconciliations: [{ code: "total", passed: false, expected_value: "100", actual_value: "90", details: {} }] }],
])("does not publish when %s", async (_name, override) => {
  const original = mockFetchForHappyPath();
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (String(input).endsWith("/validate")) return jsonResponse({ ...IMPORT_VERSION, ...override });
    return original(input, init);
  }));
  render(<DataWorkbench />);
  await uploadAndValidate();
  const publish = screen.getByRole("button", { name: "发布此导入版本" });
  expect(publish).toBeDisabled();
  fireEvent.click(publish);
  expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url).endsWith("/publish"))).toBe(false);
});

it("keeps publication blocked if acknowledged warning state cannot be refreshed", async () => {
  const original = mockFetchForHappyPath({ warnings: true });
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (String(input).endsWith("/versions")) return jsonResponse({}, 503);
    return original(input, init);
  }));
  render(<DataWorkbench />);
  await uploadAndValidate();
  fireEvent.change(screen.getByLabelText("警告 issue-1 确认原因"), { target: { value: "已核实" } });
  fireEvent.click(screen.getByRole("button", { name: "确认警告 issue-1" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("状态刷新失败");
  expect(screen.getByRole("button", { name: "发布此导入版本" })).toBeDisabled();
});
