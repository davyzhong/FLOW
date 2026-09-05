import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StatementApp } from "../../components/statements/statement-app";

// 精简自顺丰 2026 一季报 P5 抽取值的 oracle 数据（单位：人民币千元）。
const REPORT_ID = "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b";
const LIST_RESPONSE = {
  reports: [
    {
      id: REPORT_ID,
      company_name: "顺丰控股",
      stock_code: "002352.SZ",
      report_kind: "一季报",
      period_label: "2026Q1",
      unit_note: "人民币千元",
      source_ref: "p5_samples/sf_002352/SF_2026_Q1_report.pdf",
      source_sha256: "a".repeat(64),
      statement_types: ["合并资产负债表", "合并利润表", "合并现金流量表"],
      line_item_count: 3,
      created_at: "2026-09-06T08:00:00+00:00",
    },
  ],
};
const DETAIL_RESPONSE = {
  ...LIST_RESPONSE.reports[0],
  sections: [
    {
      statement_type: "合并资产负债表",
      items: [
        { item_name: "流动资产：", sort_order: 0, value_end: null, value_begin: null, value_current: null, value_prior: null },
        { item_name: "货币资金", sort_order: 1, value_end: "16992297.0000", value_begin: "20969400.0000", value_current: null, value_prior: null },
        { item_name: "资产总计", sort_order: 2, value_end: "213797231.0000", value_begin: "217993046.0000", value_current: null, value_prior: null },
      ],
    },
    {
      statement_type: "合并利润表",
      items: [
        { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: "62432100.0000" },
        { item_name: "其中：营业成本", sort_order: 1, value_end: null, value_begin: null, value_current: "63956760.0000", value_prior: "54012300.0000" },
        { item_name: "三、营业利润（亏损以“－”号填列）", sort_order: 2, value_end: null, value_begin: null, value_current: "3399319.0000", value_prior: "2900000.0000" },
        { item_name: "四、利润总额（亏损总额以“－”号填列）", sort_order: 3, value_end: null, value_begin: null, value_current: "3473111.0000", value_prior: "2950000.0000" },
        { item_name: "减：所得税费用", sort_order: 4, value_end: null, value_begin: null, value_current: "822268.0000", value_prior: "700000.0000" },
        { item_name: "五、净利润（净亏损以“－”号填列）", sort_order: 5, value_end: null, value_begin: null, value_current: "2650843.0000", value_prior: "2017475.0000" },
      ],
    },
    {
      statement_type: "合并现金流量表",
      items: [
        { item_name: "经营活动产生的现金流量净额", sort_order: 0, value_end: null, value_begin: null, value_current: "3364929.0000", value_prior: "1200000.0000" },
        { item_name: "投资活动产生的现金流量净额", sort_order: 1, value_end: null, value_begin: null, value_current: "-6413514.0000", value_prior: "-5000000.0000" },
        { item_name: "筹资活动产生的现金流量净额", sort_order: 2, value_end: null, value_begin: null, value_current: "-909275.0000", value_prior: "-800000.0000" },
        { item_name: "加：期初现金及现金等价物余额", sort_order: 3, value_end: null, value_begin: null, value_current: "19959631.0000", value_prior: null },
        { item_name: "六、期末现金及现金等价物余额", sort_order: 4, value_end: null, value_begin: null, value_current: "15972294.0000", value_prior: null },
      ],
    },
  ],
};

function stubFetch(responses: Record<string, unknown>, ok = true) {
  return vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const path = String(input).replace(/^https?:\/\/[^/]+/, "");
      const match = Object.keys(responses).find((key) => path === key || path.startsWith(`${key}?`));
      const body = match ? responses[match] : undefined;
      return Promise.resolve(
        ok && body !== undefined
          ? new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } })
          : new Response(JSON.stringify({ detail: { code: "not_found", message: "不存在" } }), { status: 404 }),
      );
    }),
  );
}

describe("StatementApp", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("空态提示需要先导入抽取数据", async () => {
    stubFetch({ "/api/v1/statements": { reports: [] } });
    render(<StatementApp />);
    expect(await screen.findByText(/尚无已导入的财报/)).toBeInTheDocument();
  });

  it("加载后渲染 KPI、瀑布图与四表全量行项目", async () => {
    stubFetch({
      "/api/v1/statements": LIST_RESPONSE,
      [`/api/v1/statements/${REPORT_ID}`]: DETAIL_RESPONSE,
    });
    render(<StatementApp />);
    expect(await screen.findByText("顺丰控股")).toBeInTheDocument();
    const kpis = await screen.findAllByTestId("statement-kpi");
    expect(kpis.length).toBeGreaterThan(3);
    expect(screen.getByRole("img", { name: /利润形成瀑布图/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /期末资产构成环形图/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /现金流量三类活动净额柱状图/ })).toBeInTheDocument();
    // 瀑布图 KPI 数字来自同一抽取值：营业总收入 741.42 亿（74142121 千元）
    expect(screen.getByText("741.42 亿元")).toBeInTheDocument();
    // 四表原文表格渲染精确值
    expect(screen.getByTitle("16992297.0000")).toBeInTheDocument();
    expect(screen.getAllByTitle("2650843.0000").length).toBeGreaterThan(0);
  });

  it("接口失败时给出错误与重试", async () => {
    const fetchStub = vi.fn<(input?: RequestInfo | URL) => Promise<Response>>(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: { code: "boom", message: "后端异常" } }), { status: 500 }),
      ),
    );
    vi.stubGlobal("fetch", fetchStub);
    render(<StatementApp />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    const retry = screen.getByRole("button", { name: "重试" });
    fetchStub.mockImplementation((input: RequestInfo | URL) => {
      const path = String(input).replace(/^https?:\/\/[^/]+/, "");
      const body = path === `/api/v1/statements/${REPORT_ID}` ? DETAIL_RESPONSE : { reports: LIST_RESPONSE.reports };
      return Promise.resolve(
        new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } }),
      );
    });
    fireEvent.click(retry);
    expect(await screen.findByText("顺丰控股")).toBeInTheDocument();
  });
});
