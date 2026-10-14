import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ActionItemPanel } from "../../components/cockpit/action-panel";
import type { CockpitActionItemResponse } from "../../lib/api/client";

const item: CockpitActionItemResponse = {
  id: "item-1",
  finding_id: "f-1",
  snapshot_id: "s-1",
  title: "现金流背离专项说明",
  detail: "E5 对应行动项",
  created_by: "cockpit-cfo-a",
  created_at: "2026-10-14T00:00:00Z",
  acknowledgment: "audit_event",
};

describe("ActionItemPanel", () => {
  it("加载并展示行动项列表", async () => {
    const fetchActionItems = vi.fn().mockResolvedValue([item]);
    render(<ActionItemPanel fetchActionItems={fetchActionItems} acknowledgeActionItem={vi.fn()} />);
    expect(await screen.findByText("现金流背离专项说明")).toBeVisible();
    expect(screen.getByRole("button", { name: "确认" })).toBeVisible();
  });

  it("确认后显示审计凭证态且按钮消失（不改业务行的客户端镜像）", async () => {
    const fetchActionItems = vi.fn().mockResolvedValue([item]);
    const acknowledgeActionItem = vi.fn().mockResolvedValue({ ...item });
    render(
      <ActionItemPanel
        fetchActionItems={fetchActionItems}
        acknowledgeActionItem={acknowledgeActionItem}
      />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "确认" }));
    await waitFor(() =>
      expect(screen.getByText(/已确认（凭证入审计账本）/)).toBeVisible(),
    );
    expect(screen.queryByRole("button", { name: "确认" })).toBeNull();
    expect(acknowledgeActionItem).toHaveBeenCalledWith("item-1");
  });

  it("空列表展示引导文案", async () => {
    const fetchActionItems = vi.fn().mockResolvedValue([]);
    render(
      <ActionItemPanel fetchActionItems={fetchActionItems} acknowledgeActionItem={vi.fn()} />,
    );
    expect(await screen.findByText(/本期无行动项/)).toBeVisible();
  });

  it("加载失败展示错误与重试", async () => {
    const fetchActionItems = vi
      .fn()
      .mockRejectedValue(new Error("boom"));
    render(
      <ActionItemPanel fetchActionItems={fetchActionItems} acknowledgeActionItem={vi.fn()} />,
    );
    expect(await screen.findByRole("alert")).toBeVisible();
    expect(screen.getByRole("button", { name: "重试" })).toBeVisible();
  });
});
