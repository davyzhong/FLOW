import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: {},
  report_items: [],
  metrics: [],
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

const COVERAGE = {
  dataset_id: "flow.p5_metric_coverage.v1",
  title: "P5 真实财报指标覆盖矩阵",
  generator: "scripts/p5_query_facts.py",
  generated_at: "2026-09-14T06:50:46",
  facts_source: "docs/implementation/p5/statement_facts.yaml",
  alias_map: "docs/implementation/p5/item_alias_map_v1.yaml",
  caliber_notes: ["avg 为（期末+期初）/2、prior 为上年同期列；单季数据未年化"],
  snapshots: [
    { company: "alibaba_9988", period: "FY2026", unit: "百万元", computable: 22, total: 40 },
    { company: "sf_002352", period: "2026Q1", unit: "千元", computable: 40, total: 40 },
  ],
  metrics: [
    {
      metric_code: "current_ratio",
      name: "流动比率",
      unit: "倍",
      cells: {
        "alibaba_9988 FY2026": { display: "1.28", missing: null },
        "sf_002352 2026Q1": { display: null, missing: "bs.cash" },
      },
    },
  ],
};

function stubFetch(log: string[]) {
  return vi.stubGlobal(
    "fetch",
    vi.fn<(input?: RequestInfo | URL) => Promise<Response>>((input?: RequestInfo | URL) => {
      const url = String(input ?? "");
      log.push(url);
      const respond = (body: unknown, status = 200) =>
        Promise.resolve(
          new Response(JSON.stringify(body), {
            status,
            headers: { "content-type": "application/json" },
          }),
        );
      if (url.endsWith("/api/v1/metric-library/coverage")) return respond(COVERAGE);
      if (url.endsWith("/api/v1/metric-library")) return respond(LIBRARY);
      return respond({ detail: { code: "not_found", message: "?" } }, 404);
    }),
  );
}

describe("MetricLibraryApp 真实财报覆盖矩阵（P5）", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("点击覆盖 tab 后拉取 coverage 数据集并渲染矩阵", async () => {
    const log: string[] = [];
    stubFetch(log);

    render(<MetricLibraryApp />);
    await screen.findByRole("button", { name: "真实财报覆盖" });
    fireEvent.click(screen.getByRole("button", { name: "真实财报覆盖" }));

    expect(await screen.findByText(/流动比率/)).toBeInTheDocument();
    expect(screen.getByText("阿里巴巴")).toBeInTheDocument();
    expect(screen.getByText("顺丰控股")).toBeInTheDocument();
    expect(screen.getByText("1.28")).toBeInTheDocument();
    expect(screen.getByText("缺 bs.cash")).toBeInTheDocument();
    expect(screen.getByText("22/40")).toBeInTheDocument();
    expect(screen.getByText(/flow\.p5_metric_coverage\.v1/)).toBeInTheDocument();
    expect(log.some((url) => url.endsWith("/api/v1/metric-library/coverage"))).toBe(true);
  });

  it("覆盖接口失败时给出错误与重试", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<(input?: RequestInfo | URL) => Promise<Response>>((input?: RequestInfo | URL) => {
        const url = String(input ?? "");
        const respond = (body: unknown, status = 200) =>
          Promise.resolve(
            new Response(JSON.stringify(body), {
              status,
              headers: { "content-type": "application/json" },
            }),
          );
        if (url.endsWith("/api/v1/metric-library")) return respond(LIBRARY);
        return respond({ detail: { code: "boom", message: "?" } }, 500);
      }),
    );

    render(<MetricLibraryApp />);
    fireEvent.click(await screen.findByRole("button", { name: "真实财报覆盖" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("覆盖矩阵暂时无法加载");
    expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument();
  });
});
