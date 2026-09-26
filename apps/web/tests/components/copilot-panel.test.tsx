import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CopilotPanel } from "../../components/investigation/copilot-panel";
import type { InvestigationContext } from "../../lib/api/client";

// 批次二 §3.3：copilot citations 点击定位 —— evidence/driver 页内锚点（对象在本页才链接），
// batch/snapshot/metric/finding 跨页深链，未识别格式保持纯文本。

const context = {
  drivers: [
    {
      driver_code: "fuel_price",
      calculation_method: "油耗 × 油价",
      contribution_amount: "-3200000.0000",
      contribution_ratio: "0.2766",
    },
  ],
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
} as unknown as InvestigationContext;

const query = { finding_id: "f-1", batch_id: null, metric_snapshot_id: null, analysis_run_id: null };

const ANSWER = {
  interaction_id: "ia-1",
  outcome: "answered",
  answer: {
    facts: [
      {
        text: "履约成本上升主要由油价驱动。",
        citations: [
          "evidence:e2",
          "evidence:ghost",
          "driver:f-1:fuel_price",
          "driver:f-1:ghost_driver",
          "batch:b-1",
          "snapshot:ms-1",
          "metric:direct_cost",
          "finding:f-1",
          "unknown-format",
        ],
      },
    ],
    judgments: [],
    hypotheses: [],
    questions: [],
    degradation: "none",
  },
};

function stubCopilot() {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify(ANSWER), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    ),
  );
}

describe("CopilotPanel citations 定位（批次二）", () => {
  it("evidence/driver 引用链到页内锚点，实体类引用链到深链，未知对象保持纯文本", async () => {
    stubCopilot();
    render(<CopilotPanel context={context} query={query} />);
    fireEvent.click(screen.getByRole("button", { name: "生成结构化解读" }));
    await waitFor(() => expect(screen.getByTestId("copilot-answer")).toBeInTheDocument());

    // 本页存在的证据 → 页内锚点
    expect(screen.getByRole("link", { name: "evidence:e2" })).toHaveAttribute(
      "href",
      "#evidence-e2",
    );
    // 本页不存在的证据 → 纯文本（诚实约束）
    expect(screen.queryByRole("link", { name: "evidence:ghost" })).toBeNull();
    expect(screen.getByText("evidence:ghost")).toBeInTheDocument();
    // 本页存在的驱动 → 驱动明细行锚点
    expect(screen.getByRole("link", { name: "driver:f-1:fuel_price" })).toHaveAttribute(
      "href",
      "#driver-fuel_price",
    );
    expect(screen.queryByRole("link", { name: "driver:f-1:ghost_driver" })).toBeNull();
    // 实体类引用 → 跨页深链（目标页负责未命中显式提示）
    expect(screen.getByRole("link", { name: "batch:b-1" })).toHaveAttribute(
      "href",
      "/data?batch=b-1",
    );
    expect(screen.getByRole("link", { name: "snapshot:ms-1" })).toHaveAttribute(
      "href",
      "/reports?snapshot=ms-1",
    );
    expect(screen.getByRole("link", { name: "metric:direct_cost" })).toHaveAttribute(
      "href",
      "/metric-library?focus=direct_cost",
    );
    expect(screen.getByRole("link", { name: "finding:f-1" })).toHaveAttribute(
      "href",
      "/investigations/f-1",
    );
    // 未识别格式 → 纯文本
    expect(screen.queryByRole("link", { name: "unknown-format" })).toBeNull();
    expect(screen.getByText("unknown-format")).toBeInTheDocument();
  });
});
