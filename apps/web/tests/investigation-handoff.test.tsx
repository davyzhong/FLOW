import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import InvestigationPage from "../app/investigations/[findingId]/page";

const context = {
  findingId: "5535b51a-f81f-5e6d-8ef2-fd4d2552f984",
  batchId: "934072b5-8f89-5f96-a498-c88b26483908",
  snapshotId: "87d9dfbb-0ac7-5dde-9675-537459961f15",
  runId: "639f2271-5816-51d4-8f5d-038b6d98e08c",
};

describe("Investigation handoff", () => {
  it("retains every immutable dashboard context identity", async () => {
    const page = await InvestigationPage({
      params: Promise.resolve({ findingId: context.findingId }),
      searchParams: Promise.resolve({
        batch_id: context.batchId,
        metric_snapshot_id: context.snapshotId,
        analysis_run_id: context.runId,
      }),
    });
    render(page);

    expect(screen.getByRole("heading", { name: "经营调查上下文" })).toBeVisible();
    const receipt = screen.getByRole("region", { name: "不可变分析上下文" });
    for (const identity of Object.values(context)) {
      expect(receipt).toHaveTextContent(identity);
    }
    expect(screen.getByText("调查工作台将在下一阶段展开")).toBeVisible();
    expect(screen.getByRole("link", { name: "返回经营驾驶舱" })).toHaveAttribute("href", "/");
  });
});
