import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { OperationsOverviewApp } from "../../components/operations/operations-overview";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const REPORTS = {
  reports: [
    {
      id: "report-1",
      company_name: "顺丰控股",
      stock_code: "002352.SZ",
      report_kind: "一季报",
      period_label: "2026Q1",
      status: "published",
      unit_note: "人民币万元",
      version: 1,
      created_at: "2026-09-01T09:00:00+08:00",
    },
  ],
};

const OVERVIEW = {
  report_id: "report-1",
  catalog_id: "flow.analysis.objective_finance.v1",
  themes: [
    {
      theme_id: "profit_quality",
      name: "盈利质量",
      availability: "financial_report",
      status: "available",
      reason: null,
      metrics: [
        {
          entry_id: "dupont_three_factor",
          name: "杜邦三分解（净利润总额口径 · 期末权益 · 未年化）",
          status: "computed",
          value: "0.1600",
          basis: "本期归一化事实",
          caliber_note: "净利润总额口径",
          reason: null,
          source: "d01_entry",
        },
        {
          entry_id: "gross_margin",
          name: "毛利率",
          status: "computed",
          value: "0.3200",
          basis: "本期归一化事实（财报直接口径）",
          caliber_note: "is.gross_profit ÷ is.revenue",
          reason: null,
          source: "fact_direct",
        },
      ],
    },
    {
      theme_id: "users_channels",
      name: "用户与渠道",
      availability: "internal_process",
      status: "not_applicable",
      reason: "internal_data_required",
      metrics: [],
    },
  ],
  management_watch: [
    {
      code: "cash_content_below_one",
      message: "净利润现金含量 0.6000，经营现金流低于净利润",
      direction: "negative",
    },
  ],
  facts_available: ["is.revenue"],
};

describe("OperationsOverviewApp", () => {
  it("renders six-theme facts, management watch, honest N/A, and freezes", async () => {
    const freezeSpy = vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toContain("/operations/overview/report-1/freeze");
      return jsonResponse({
        snapshot_id: "snap-ops-1",
        version: 1,
        report_type: "operations_overview",
        payload_hash: "h".repeat(64),
      });
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") return freezeSpy(input);
      if (url.endsWith("/statements")) return jsonResponse(REPORTS);
      if (url.includes("/operations/overview/")) return jsonResponse(OVERVIEW);
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OperationsOverviewApp />);

    await waitFor(() => {
      expect(screen.getByText("六主题概览")).toBeTruthy();
    });
    // 事实卡片：值 + 基准 + 口径（借鉴 #1/#2）
    expect(screen.getByText("0.1600")).toBeTruthy();
    expect(screen.getByText(/口径：净利润总额口径/)).toBeTruthy();
    // 诚实 N/A
    expect(screen.getByText(/待内部数据（internal_data_required）/)).toBeTruthy();
    // 管理关注 ≤3 带方向
    expect(screen.getByText(/净利润现金含量 0.6000/)).toBeTruthy();
    // 范围说明（#9 客观部分）
    expect(screen.getByText(/不在客观报告范围/)).toBeTruthy();

    // 冻结按钮 → 显示快照信息
    fireEvent.click(screen.getByRole("button", { name: "冻结概览" }));
    await waitFor(() => {
      expect(screen.getByText(/已冻结：版本 1/)).toBeTruthy();
    });
  });
});
