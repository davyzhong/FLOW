import type { ReactElement } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StatementApp } from "../../components/statements/statement-app";
import { createFlowQueryClient } from "../../lib/api/query-client";

function renderWithClient(ui: ReactElement) {
  return render(<QueryClientProvider client={createFlowQueryClient()}>{ui}</QueryClientProvider>);
}

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
    renderWithClient(<StatementApp />);
    expect(await screen.findByText(/尚无已导入的财报/)).toBeInTheDocument();
  });

  it("加载后渲染 KPI、瀑布图与四表全量行项目", async () => {
    stubFetch({
      "/api/v1/statements": LIST_RESPONSE,
      [`/api/v1/statements/${REPORT_ID}`]: DETAIL_RESPONSE,
    });
    renderWithClient(<StatementApp />);
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

  it("接口失败时给出错误与重试", async () => {    const fetchStub = vi.fn<(input?: RequestInfo | URL) => Promise<Response>>(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: { code: "boom", message: "后端异常" } }), { status: 500 }),
      ),
    );
    vi.stubGlobal("fetch", fetchStub);
    renderWithClient(<StatementApp />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    const retry = screen.getByRole("button", { name: "重试" });
    fetchStub.mockImplementation((input?: RequestInfo | URL) => {
      const path = String(input ?? "").replace(/^https?:\/\/[^/]+/, "");
      const body = path === `/api/v1/statements/${REPORT_ID}` ? DETAIL_RESPONSE : { reports: LIST_RESPONSE.reports };
      return Promise.resolve(
        new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } }),
      );
    });
    fireEvent.click(retry);
    expect(await screen.findByText("顺丰控股")).toBeInTheDocument();
  });

  // 精简自阿里巴巴 FY2026 业绩公告 P5 抽取值的 oracle 数据（单位：人民币百万元，IFRS 繁体行名）。
  const IFRS_REPORT_ID = "1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809";
  const IFRS_DETAIL = {
    id: IFRS_REPORT_ID,
    company_name: "阿里巴巴",
    stock_code: "9988.HK",
    report_kind: "年报",
    period_label: "FY2026",
    unit_note: "人民币百万元（每股数据除外）",
    source_ref: "p5_samples/alibaba_9988/BABA_FY2026_annual_results.pdf",
    source_sha256: "b".repeat(64),
    statement_types: ["合并资产负债表", "合并利润表", "合并现金流量表"],
    line_item_count: 3,
    created_at: "2026-09-13T08:00:00+00:00",
    sections: [
      {
        statement_type: "合并利润表",
        items: [
          { item_name: "收入", sort_order: 0, value_end: null, value_begin: null, value_current: "1023670.0000", value_prior: "996347.0000" },
          { item_name: "營業成本", sort_order: 1, value_end: null, value_begin: null, value_current: "-616136.0000", value_prior: "-598285.0000" },
          { item_name: "產品開發費用", sort_order: 2, value_end: null, value_begin: null, value_current: "-66533.0000", value_prior: "-57151.0000" },
          { item_name: "銷售和市場費用", sort_order: 3, value_end: null, value_begin: null, value_current: "-245023.0000", value_prior: "-144021.0000" },
          { item_name: "一般及行政費用", sort_order: 4, value_end: null, value_begin: null, value_current: "-33082.0000", value_prior: "-44239.0000" },
          { item_name: "無形資產攤銷及減值", sort_order: 5, value_end: null, value_begin: null, value_current: "-5079.0000", value_prior: "-6336.0000" },
          { item_name: "商譽減值", sort_order: 6, value_end: null, value_begin: null, value_current: "-9515.0000", value_prior: "-6171.0000" },
          { item_name: "經營利潤（虧損）", sort_order: 7, value_end: null, value_begin: null, value_current: "50150.0000", value_prior: "140905.0000" },
          { item_name: "扣除所得稅及權益法核算的投資損益前的利潤", sort_order: 8, value_end: null, value_begin: null, value_current: "129387.0000", value_prior: "155455.0000" },
          { item_name: "所得稅費用", sort_order: 9, value_end: null, value_begin: null, value_current: "-30045.0000", value_prior: "-35445.0000" },
          { item_name: "權益法核算的投資損益", sort_order: 10, value_end: null, value_begin: null, value_current: "2785.0000", value_prior: "5966.0000" },
          { item_name: "淨利潤", sort_order: 11, value_end: null, value_begin: null, value_current: "102127.0000", value_prior: "125976.0000" },
          { item_name: "歸屬於阿里巴巴集團股東的淨利潤", sort_order: 12, value_end: null, value_begin: null, value_current: "97955.0000", value_prior: "118586.0000" },
        ],
      },
      {
        statement_type: "合并资产负债表",
        items: [
          { item_name: "現金及現金等價物", sort_order: 0, value_end: "131530.0000", value_begin: "145487.0000", value_current: null, value_prior: null },
          { item_name: "商譽", sort_order: 1, value_end: "283000.0000", value_begin: "203000.0000", value_current: null, value_prior: null },
          { item_name: "資產總額", sort_order: 2, value_end: "1910000.0000", value_begin: "1804000.0000", value_current: null, value_prior: null },
          { item_name: "流動負債總額", sort_order: 3, value_end: "476000.0000", value_begin: "435000.0000", value_current: null, value_prior: null },
          { item_name: "負債總額", sort_order: 4, value_end: "783000.0000", value_begin: "714000.0000", value_current: null, value_prior: null },
          { item_name: "權益總額", sort_order: 5, value_end: "1127000.0000", value_begin: "1090000.0000", value_current: null, value_prior: null },
        ],
      },
      {
        statement_type: "合并现金流量表",
        items: [
          { item_name: "經營活動產生的現金流量淨額", sort_order: 0, value_end: null, value_begin: null, value_current: "76213.0000", value_prior: "163509.0000" },
          { item_name: "投資活動所用現金流量淨額", sort_order: 1, value_end: null, value_begin: null, value_current: "-120000.0000", value_prior: "-90000.0000" },
          { item_name: "融資活動所用現金流量淨額", sort_order: 2, value_end: null, value_begin: null, value_current: "-50000.0000", value_prior: "-60000.0000" },
          { item_name: "期初現金及現金等價物", sort_order: 3, value_end: null, value_begin: null, value_current: "145487.0000", value_prior: null },
          { item_name: "期末現金及現金等價物", sort_order: 4, value_end: null, value_begin: null, value_current: "131530.0000", value_prior: null },
        ],
      },
    ],
  };

  it("IFRS 繁体行名与百万元单位：KPI、瀑布、环形与现金桥全部渲染且缩放正确", async () => {
    stubFetch({
      "/api/v1/statements": { reports: [{ ...IFRS_DETAIL, sections: undefined }] },
      [`/api/v1/statements/${IFRS_REPORT_ID}`]: IFRS_DETAIL,
    });
    renderWithClient(<StatementApp />);
    expect(await screen.findByText("阿里巴巴")).toBeInTheDocument();
    const kpis = await screen.findAllByTestId("statement-kpi");
    expect(kpis.length).toBeGreaterThan(3);
    // 百万元 → 亿元：1,023,670 百万 = 10,236.70 亿；不是 10.24（千元缩放）。
    expect(screen.getByText("10,236.70 亿元")).toBeInTheDocument();
    // IFRS 利润瀑布、资产构成环形、现金流柱状与现金桥
    expect(screen.getByRole("img", { name: /利润形成瀑布图/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /期末资产构成环形图/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /现金流量三类活动净额柱状图/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /期初到期末的现金变动桥/ })).toBeInTheDocument();
    // 四表原文表格渲染精确值（悬停 title）
    expect(screen.getAllByTitle("1023670.0000").length).toBeGreaterThan(0);
  });
});

// 批次一 §2.1/§2.2：/statements?report={report_id} 初始选中 + 更正记录页内锚点。
describe("StatementApp 深链", () => {
  const SECOND_ID = "2b3c4d5e-6f70-8192-a3b4-c5d6e7f8091a";
  const SECOND_SUMMARY = {
    ...LIST_RESPONSE.reports[0],
    id: SECOND_ID,
    company_name: "圆通速递",
    period_label: "2026Q1",
  };
  const SECOND_DETAIL = { ...DETAIL_RESPONSE, id: SECOND_ID, company_name: "圆通速递" };

  it("?report= 命中时初始选中对应财报而非默认第一条", async () => {
    stubFetch({
      "/api/v1/statements": { reports: [LIST_RESPONSE.reports[0], SECOND_SUMMARY] },
      [`/api/v1/statements/${SECOND_ID}`]: SECOND_DETAIL,
    });
    renderWithClient(<StatementApp initialReportId={SECOND_ID} />);
    expect(await screen.findByText("圆通速递")).toBeInTheDocument();
    const tabs = screen.getByRole("navigation", { name: "财报选择" });
    const second = screen.getByRole("button", { name: /圆通速递/ });
    expect(second).toHaveAttribute("aria-pressed", "true");
    expect(tabs).toBeInTheDocument();
  });

  it("?report= 不存在时显式提示并回退到第一份财报", async () => {
    stubFetch({
      "/api/v1/statements": LIST_RESPONSE,
      [`/api/v1/statements/${REPORT_ID}`]: DETAIL_RESPONSE,
    });
    renderWithClient(<StatementApp initialReportId="missing-report-id" />);
    expect(await screen.findByText(/未找到财报/)).toBeInTheDocument();
    expect(await screen.findByText("顺丰控股")).toBeInTheDocument();
  });

  it("四表行带 DOM 锚点 id，更正记录条目链接到对应行", async () => {
    stubFetch({
      "/api/v1/statements": LIST_RESPONSE,
      [`/api/v1/statements/${REPORT_ID}`]: DETAIL_RESPONSE,
      [`/api/v1/statements/${REPORT_ID}/corrections`]: {
        corrections: [
          {
            id: "corr-1",
            statement_type: "合并利润表",
            item_name: "一、营业总收入",
            column_key: "value_current",
            old_value: "1.0000",
            new_value: "74142121.0000",
            operator: "finance.bp",
            reason: "补录披露值",
            created_at: "2026-09-06T09:00:00+00:00",
          },
        ],
      },
    });
    renderWithClient(<StatementApp />);
    // 更正记录链接随 ReportDetail 渲染出现，找到它即说明四表已挂载
    const anchor = await screen.findByRole("link", { name: /合并利润表.*一、营业总收入/ });
    expect(anchor).toHaveAttribute("href", "#stmt-row-合并利润表-一、营业总收入");
    expect(
      document.getElementById("stmt-row-合并利润表-一、营业总收入"),
    ).not.toBeNull();
  });
});
