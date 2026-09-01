import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InvestigationApp } from "../components/investigation/investigation-app";
import type { InvestigationContext } from "../lib/api/client";

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
  result: {
    analysis_result_id: "3f1c7f5e-0000-0000-0000-000000000001",
    playbook_code: "fulfillment_cost_rve",
    playbook_version: 1,
    status: "complete",
    comparison_basis: "prior_year",
    impact_amount: "-11570000.0000",
    unit: "CNY",
    reconciliation_difference: "0.0000",
    reconciliation_tolerance: "0.0100",
    source_record_count: 3072,
    degradation_code: null,
    degradation_message: null,
  },
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
  drivers: [
    {
      position: 1,
      driver_code: "rate_effect",
      calculation_method: "Rate × Volume",
      contribution_amount: "-7800000.0000",
      contribution_ratio: "0.6742",
    },
    {
      position: 2,
      driver_code: "volume_effect",
      calculation_method: "Volume effect",
      contribution_amount: "-3770000.0000",
      contribution_ratio: "0.3258",
    },
  ],
  evidence: [
    {
      evidence_id: "e1",
      status: "verified",
      evidence_type: "metric_value",
      object_type: "metric",
      object_id: "metric-snapshot:snap",
      note: null,
      evidence_digest: null,
    },
    {
      evidence_id: "e2",
      status: "pending",
      evidence_type: "business_confirmation",
      object_type: "source_record",
      object_id: "source-record:1950",
      note: "待商务审批单归档",
      evidence_digest: null,
    },
  ],
  reviews: [
    {
      sequence: 1,
      reviewer: "陈晨",
      decision: "evidence_rejected",
      comment: "口径存疑",
      created_at: "2026-09-02T02:10:00Z",
    },
  ],
  quality_issues: [
    {
      severity: "warning",
      code: "header_offset",
      message: "表头存在一行偏移",
      acknowledged: true,
    },
  ],
  reconciliations: [
    {
      reconciliation_code: "operating_revenue_vs_financial",
      passed: true,
      expected_value: "48220000.00",
      actual_value: "48220000.00",
    },
  ],
  conclusion: {
    exists: false,
    verified_facts: "",
    analysis_judgment: "",
    open_questions: "",
    recommendation: "",
  },
  source_records: [
    {
      fact_id: "f1",
      month_key: 202607,
      labels: { 客户: "战略客户A", 物流产品: "运输", 区域: "华东" },
      values: { 收入: "3820000.0000", 运输成本: "1260000.0000" },
      source_file_name: "2026年7月供应链经营分析.xlsx",
      sheet_name: "业务明细",
      source_row: 1950,
      source_column: "*",
    },
  ],
  eligibility_blockers: ["finding_not_submitted", "evidence_pending", "conclusion_incomplete"],
} as unknown as InvestigationContext;

const query = {
  finding_id: identity.findingId,
  batch_id: identity.batchId,
  metric_snapshot_id: identity.snapshotId,
  analysis_run_id: identity.runId,
};

describe("Investigation handoff", () => {
  it("retains every immutable dashboard context identity", async () => {
    const load = vi.fn().mockResolvedValue(context);
    render(<InvestigationApp query={query} loadInvestigation={load} />);

    const receipt = await screen.findByRole("region", { name: "不可变分析上下文" });
    for (const value of Object.values(identity)) {
      expect(receipt).toHaveTextContent(value);
    }
    expect(load).toHaveBeenCalledWith(query, expect.anything());
  });

  it("projects drivers, checks, lineage and blocked-approval state", async () => {
    const load = vi.fn().mockResolvedValue(context);
    render(<InvestigationApp query={query} loadInvestigation={load} />);

    expect(
      await screen.findByRole("heading", {
        name: "履约成本增速超过收入增速，稀释经营利润",
        level: 1,
      }),
    ).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("region", { name: "驱动计算明细" })).toHaveTextContent(
      "Rate × Volume",
    );
    expect(screen.getByRole("region", { name: "口径与数据检查" })).toHaveTextContent(
      "尚不可进入正式报告",
    );
    expect(screen.getByRole("region", { name: "口径与数据检查" })).toHaveTextContent(
      "存在待确认证据",
    );
    const records = screen.getByRole("region", { name: "关键源记录" });
    expect(records).toHaveTextContent("业务明细!R1950");
    expect(records).toHaveTextContent("2026-07");
    expect(screen.getByRole("region", { name: "证据复核" })).toHaveTextContent("待确认");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "提交复核" })).toBeEnabled();
    });
    expect(screen.queryByRole("button", { name: "批准签发" })).toBeNull();
  });
});
