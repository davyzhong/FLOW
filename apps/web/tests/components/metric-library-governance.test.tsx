import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

const METRIC = {
  metric_code: "roe",
  name: "净资产收益率",
  entry_id: "entry-1",
  status: "effective",
  execution_kind: "facts",
  collection: "general",
  domain: "profitability",
  definition: "净利润与平均净资产之比。",
  formula_text: "净利润 ÷ 平均净资产 × 100%",
  mpm: false,
  aliases: [],
  depends_on: [],
  source_cas: [],
  decompositions: [],
  alternative_calibers: [],
};

const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { profitability: "盈利能力" },
  report_items: [],
  metrics: [METRIC],
  relations: [],
  accounting: {
    dataset_id: "flow.accounting_foundation.v1",
    status: "effective",
    known_gaps: [],
    categories: [],
    accounts: [],
    superseded_notes: [],
    standards: [],
    entry_templates: [],
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function stubFetch(log: { method: string; url: string; body?: unknown }[]) {
  return vi.stubGlobal(
    "fetch",
    vi.fn<(input?: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
      (input?: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input ?? "");
        const method = init?.method ?? "GET";
        let body: unknown;
        if (typeof init?.body === "string") body = JSON.parse(init.body);
        log.push({ method, url, body });
        if (url.endsWith("/api/v1/metric-library")) return Promise.resolve(jsonResponse(LIBRARY));
        if (url.includes("/metric-library/events")) {
          return Promise.resolve(
            jsonResponse({
              events: [
                {
                  id: "evt-1",
                  metric_code: "roe",
                  version: 2,
                  action: "draft",
                  operator: "finance-bp",
                  reason: "更新基准",
                  created_at: "2026-09-07T08:00:00+00:00",
                },
              ],
            }),
          );
        }
        if (url.includes("/drafts") || url.includes("/activate") || url.includes("/retire")) {
          return Promise.resolve(jsonResponse({ ok: true }));
        }
        return Promise.resolve(jsonResponse({ detail: { code: "not_found", message: "?" } }, 404));
      },
    ),
  );
}

async function openGovernanceTab() {
  render(<MetricLibraryApp />);
  await screen.findByText("净资产收益率");
  fireEvent.click(screen.getByRole("button", { name: "治理记录" }));
}

describe("MetricLibraryApp 治理操作（C06）", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("发起草稿修订：校验必填、提交正确载荷并刷新事件流", async () => {
    const log: { method: string; url: string; body?: unknown }[] = [];
    stubFetch(log);
    await openGovernanceTab();

    // 必填校验：空操作者直接拒绝，不发请求
    fireEvent.click(screen.getByRole("button", { name: "创建草稿" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("操作者与理由均为必填");

    fireEvent.change(screen.getByLabelText("操作者"), { target: { value: "finance-bp" } });
    fireEvent.change(screen.getByLabelText("理由"), { target: { value: "更新基准值来源" } });
    fireEvent.change(screen.getByLabelText("变更内容 JSON"), {
      target: { value: '{"benchmark": "国资委 2025"}' },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建草稿" }));

    await waitFor(() =>
      expect(
        log.find((entry) => entry.url.includes("/entries/entry-1/drafts")),
      ).toMatchObject({
        method: "POST",
        body: {
          operator: "finance-bp",
          reason: "更新基准值来源",
          changes: { benchmark: "国资委 2025" },
        },
      }),
    );
    expect(await screen.findByText(/已创建草稿：roe/)).toBeInTheDocument();
    expect(await screen.findByText("draft")).toBeInTheDocument();
    expect(screen.getByText("finance-bp")).toBeInTheDocument();
  });

  it("非法 JSON 被行内拦截，不发出请求", async () => {
    const log: { method: string; url: string; body?: unknown }[] = [];
    stubFetch(log);
    await openGovernanceTab();

    fireEvent.change(screen.getByLabelText("操作者"), { target: { value: "finance-bp" } });
    fireEvent.change(screen.getByLabelText("理由"), { target: { value: "x" } });
    fireEvent.change(screen.getByLabelText("变更内容 JSON"), { target: { value: "{oops" } });
    fireEvent.click(screen.getByRole("button", { name: "创建草稿" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("合法的 JSON 对象");
    expect(log.filter((entry) => entry.method === "POST")).toHaveLength(0);
  });

  it("激活与退役调用对应端点并提示结果", async () => {
    const log: { method: string; url: string; body?: unknown }[] = [];
    stubFetch(log);
    await openGovernanceTab();

    fireEvent.change(screen.getByLabelText("操作者"), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText("理由"), { target: { value: "季度评审通过" } });
    fireEvent.click(screen.getByRole("button", { name: "激活" }));
    expect(await screen.findByText(/已激活：roe/)).toBeInTheDocument();
    expect(log.find((entry) => entry.url.includes("/entries/entry-1/activate"))).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "退役" }));
    expect(await screen.findByText(/已退役：roe/)).toBeInTheDocument();
    expect(log.find((entry) => entry.url.includes("/entries/entry-1/retire"))).toBeTruthy();
  });
});
