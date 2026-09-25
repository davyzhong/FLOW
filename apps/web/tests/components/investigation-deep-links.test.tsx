import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InvestigationApp } from "../../components/investigation/investigation-app";
import { InvestigationsIndex } from "../../components/investigation/investigations-index";
import type { InvestigationContext } from "../../lib/api/client";

// 批次一 §2.2/§2.3：investigation 身份条四 ID 链接、检查行页内锚点、
// 列表标题链接 / 评分链接 / FlowDataTable rowHref。

const identity = {
  findingId: "5535b51a-f81f-5e6d-8ef2-fd4d2552f984",
  batchId: "934072b5-8f89-5f96-a498-c88b26483908",
  snapshotId: "87d9dfbb-0ac7-5dde-9675-537459961f15",
  runId: "639f2271-5816-51d4-8f5d-038b6d98e08c",
};

const context = {
  identity: {
    finding_id: identity.findingId,
    batch_id: identity.batchId,
    metric_snapshot_id: identity.snapshotId,
    analysis_run_id: identity.runId,
  },
  finding: {
    finding_id: identity.findingId,
    finding_type: "fulfillment_cost_increase",
    title: "履约成本增速超过收入增速，稀释经营利润",
    status: "candidate",
    impact_amount: "-11570000.0000",
    unit: "CNY",
    confidence: "0.9000",
    business_meaning: "运输外包涨价与低毛利业务扩张共同推高履约成本。",
    fact_statement: "履约成本率同比上升 1.6ppt，形成 -1157 万元影响。",
    comparison_basis: "prior_year",
    total_score: "87.000000",
    policy_version: "flow.analysis.logistics.v1",
    created_at: "2026-09-02T02:00:00Z",
  },
  result: null,
  metric: {
    metric_code: "direct_cost",
    metric_name: "履约成本",
    business_definition: "仓储、运输与其他直接成本合计",
    formula: "warehousing_cost + transportation_cost + other_direct_cost",
    unit: "CNY",
    definition_version: 1,
    engine_version: "flow-analysis/1",
    policy_id: "flow.analysis.logistics.v1",
    policy_set_hash: "448b390877b20090af02f6584e79a1c9796fe5ab0a5c7a6",
  },
  drivers: [],
  evidence: [
    {
      evidence_id: "e2",
      status: "pending",
      evidence_type: "business_confirmation",
      object_type: "source_record",
      object_id: "source-record:1950",
      note: null,
      evidence_digest: null,
    },
  ],
  reviews: [],
  quality_issues: [
    {
      severity: "blocking",
      code: "missing_column",
      message: "缺少必需列",
      acknowledged: false,
    },
  ],
  reconciliations: [
    {
      reconciliation_code: "operating_revenue_vs_financial",
      passed: false,
      expected_value: "48220000.00",
      actual_value: "47220000.00",
    },
  ],
  conclusion: {
    exists: false,
    verified_facts: "",
    analysis_judgment: "",
    open_questions: "",
    recommendation: "",
  },
  source_records: [],
  eligibility_blockers: ["evidence_pending", "conclusion_incomplete"],
} as unknown as InvestigationContext;

const query = {
  finding_id: identity.findingId,
  batch_id: identity.batchId,
  metric_snapshot_id: identity.snapshotId,
  analysis_run_id: identity.runId,
};

function renderInvestigation() {
  const load = vi.fn().mockResolvedValue(context);
  render(<InvestigationApp query={query} loadInvestigation={load} />);
  return load;
}

describe("investigation 身份条深链", () => {
  it("批次 / 快照 / 运行 ID 分别链接到数据页、报告中心与分析页", async () => {
    renderInvestigation();
    const receipt = await screen.findByRole("region", { name: "不可变分析上下文" });
    const links = within(receipt).getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain(`/data?batch=${identity.batchId}`);
    expect(hrefs).toContain(`/reports?snapshot=${identity.snapshotId}`);
    expect(hrefs).toContain("/analysis");
    // Finding ID 是当前页自身，不渲染链接
    expect(within(receipt).queryByRole("link", { name: identity.findingId })).toBeNull();
  });
});

describe("investigation 检查行页内锚点", () => {
  it("失败/阻断检查行链接到证据区与结论区，目标区带锚点 id", async () => {
    renderInvestigation();
    const checks = await screen.findByRole("region", { name: "口径与数据检查" });
    const links = within(checks).getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain("#investigation-evidence");
    expect(hrefs).toContain("#investigation-conclusion");
    expect(document.getElementById("investigation-evidence")).not.toBeNull();
    expect(document.getElementById("investigation-conclusion")).not.toBeNull();
    expect(document.getElementById("investigation-sources")).not.toBeNull();
  });
});

describe("investigations 列表链接化", () => {
  const finding = {
    finding_id: identity.findingId,
    title: "履约成本增速超过收入增速",
    status: "in_review",
    finding_type: "fulfillment_cost_increase",
    impact_amount: "-11570000.0000",
    comparison_basis: "prior_year",
    total_score: "87.000000",
    batch_id: identity.batchId,
    metric_snapshot_id: identity.snapshotId,
    analysis_run_id: identity.runId,
    created_at: "2026-09-02T02:00:00Z",
  };

  function stubList() {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ findings: [finding] }), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        ),
      ),
    );
  }

  it("标题单元格包调查链接、评分链接到 /analysis、整行带 rowHref", async () => {
    stubList();
    render(<InvestigationsIndex />);
    const titleLink = await screen.findByRole("link", { name: "履约成本增速超过收入增速" });
    const expected = `/investigations/${identity.findingId}?batch_id=${identity.batchId}&metric_snapshot_id=${identity.snapshotId}&analysis_run_id=${identity.runId}`;
    expect(titleLink).toHaveAttribute("href", expected);

    const scoreLink = screen.getByRole("link", { name: "87" });
    expect(scoreLink).toHaveAttribute("href", "/analysis");

    const row = titleLink.closest("tr");
    expect(row).toHaveAttribute("data-href", expected);
  });
});
