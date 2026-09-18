import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

// 借鉴 #21 行业参考包 v1.2：行业参考目录层的只读呈现。
const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047；2026-09-17 借鉴 #21 行业参考包扩展 v1.2",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { profitability: "盈利能力" },
  report_items: [],
  metrics: [
    {
      metric_code: "current_asset_ratio",
      name: "流动资产率",
      collection: "general",
      domain: "operation",
      definition: "流动资产占资产总额的比例。",
      formula_text: "流动资产 ÷ 资产总计",
      mpm: false,
      aliases: [],
      depends_on: [],
      source_cas: [],
      decompositions: [],
      alternative_calibers: [],
    },
  ],
  relations: [],
  industry_reference_packs: [
    {
      industry_id: "retail",
      name: "零售（含商业批发）",
      note: "实体运营型行业，死磕效率与周转。",
      financial_reference: {
        current_asset_ratio: "商业批发企业的流动资产率可达 90% 以上。",
      },
      ops_indicators: [
        { code: "same_store_sales_growth", name: "同店销售增长率", meaning: "排除新店因素后比较销售额增减。" },
      ],
      provenance: "ObsidianWiki processed/微信知识库/数据熊（借鉴 #21）",
    },
    {
      industry_id: "hotel",
      name: "酒店",
      note: "入住率与房价双轮驱动。",
      financial_reference: {},
      ops_indicators: [
        { code: "revpar", name: "每可售房收入（RevPAR）", meaning: "综合入住率和平均房价。" },
      ],
      provenance: "ObsidianWiki processed/微信知识库/数据熊（借鉴 #21）",
    },
  ],
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

describe("MetricLibraryApp 行业参考包（借鉴 #21）", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(LIBRARY), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        ),
      ),
    );
  });

  it("行业参考包 tab 渲染 packs：财务基准差异挂接指标编码、经营指标目录与来源", async () => {
    render(<MetricLibraryApp />);
    await screen.findByText("流动资产率");
    fireEvent.click(screen.getByRole("button", { name: "行业参考包" }));

    expect(screen.getByText("零售（含商业批发）")).toBeInTheDocument();
    expect(screen.getByText("商业批发企业的流动资产率可达 90% 以上。")).toBeInTheDocument();
    expect(screen.getByText("同店销售增长率")).toBeInTheDocument();
    expect(screen.getAllByText(/来源：ObsidianWiki/).length).toBeGreaterThanOrEqual(1);
    // financial_reference 为空的 pack 也正常渲染（酒店无财务差异标注）
    expect(screen.getByText("每可售房收入（RevPAR）")).toBeInTheDocument();
  });

  it("旧 API 响应缺 industry_reference_packs 字段时页面不崩", async () => {
    const legacy: Record<string, unknown> = { ...LIBRARY };
    delete legacy.industry_reference_packs;
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(legacy), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        ),
      ),
    );
    render(<MetricLibraryApp />);
    await screen.findByText("流动资产率");
    fireEvent.click(screen.getByRole("button", { name: "行业参考包" }));
    expect(screen.getByText(/暂无财报取数源/)).toBeInTheDocument();
  });
});
