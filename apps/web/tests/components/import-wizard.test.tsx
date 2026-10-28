import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ImportWizard } from "../../components/data/import-wizard";
import { flowApi } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => ({
  flowApi: {
    listImporterDatasets: vi.fn(),
    importerCockpit: vi.fn(),
    deleteImporterDataset: vi.fn(),
    uploadImporterDataset: vi.fn(),
  },
}));

const mocked = vi.mocked(flowApi);

function uploadRejected() {
  return {
    ok: false as const,
    errors: [
      { row: "2", column: "会计期间", message: "[科目余额表 · 第 2 行 · 会计期间] 会计期间须为 YYYY-MM 格式（如 2025-01）" },
      { row: "0", column: "期末余额", message: "[科目余额表 · 表级 · 期末余额] 期末借贷不平衡：借方合计 12000 ≠ 贷方合计 55555" },
    ],
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(mocked.listImporterDatasets).mockResolvedValue({ datasets: [] });
  vi.mocked(mocked.importerCockpit).mockResolvedValue({
    dataset_id: "ds-1",
    periods: ["2025-01"],
    account_count: 2,
    kpi: [
      { code: "total_assets", label: "资产总计", value: "12000", unit: "CNY" },
      { code: "total_liabilities", label: "负债总计", value: "12000", unit: "CNY" },
      { code: "total_equity", label: "权益总计", value: "0", unit: "CNY" },
      { code: "net_profit", label: "本期净利润", value: "0", unit: "CNY" },
      { code: "debt_ratio", label: "资产负债率", value: "1.0000", unit: "ratio" },
    ],
    identity_check: { formula: "资产总计 − 负债总计 − 权益总计", value: "0", passed: true },
    source_note: "导入账套只读校验视图。",
  });
});

describe("ImportWizard", () => {
  it("空态：显示两步引导与暂无数据集", async () => {
    render(<ImportWizard />);
    expect(screen.getByText(/第一步 · 下载模板/)).toBeTruthy();
    expect(await screen.findByText("暂无导入数据集。")).toBeTruthy();
  });

  it("校验失败：逐行展示错误且整批拒绝", async () => {
    vi.mocked(mocked.uploadImporterDataset).mockResolvedValue(uploadRejected());
    render(<ImportWizard />);
    const fileInput = screen.getByLabelText(/模板文件/);
    const file = new File(["x"], "bad.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByText("校验并导入"));
    await waitFor(() => screen.getByText("校验未通过（整批拒绝）"));
    expect(screen.getByText(/期末借贷不平衡/)).toBeTruthy();
    expect(screen.getByText(/YYYY-MM/)).toBeTruthy();
  });

  it("导入成功：展示概览 KPI 与勾稽通过", async () => {
    vi.mocked(mocked.uploadImporterDataset).mockResolvedValue({
      ok: true as const,
      dataset_id: "ds-1",
      trial_balance_rows: 2,
      income_statement_rows: 0,
      bank_statement_rows: 0,
      balance_summary: { 期末借方合计: "12000", 期末贷方合计: "12000" },
    });
    render(<ImportWizard />);
    const fileInput = screen.getByLabelText(/模板文件/);
    const file = new File(["x"], "ok.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByText("校验并导入"));
    await waitFor(() => screen.getByText("导入成功"));
    expect(screen.getByText("资产总计")).toBeTruthy();
    expect(screen.getAllByText("12000").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("勾稽校验（资产总计 − 负债总计 − 权益总计）")).toBeTruthy();
    expect(screen.getByText("通过", { exact: true })).toBeTruthy();
    await waitFor(() => expect(mocked.listImporterDatasets).toHaveBeenCalledTimes(2));
  });

  it("数据集列表：展示并支持删除", async () => {
    vi.mocked(mocked.listImporterDatasets).mockResolvedValue({
      datasets: [
        { id: "ds-9", name: "2025 账套", created_at: "2026-10-28T09:00:00", source_filename: "a.xlsx" },
      ],
    });
    vi.mocked(mocked.deleteImporterDataset).mockResolvedValue({ ok: true, deleted: "ds-9" });
    vi.mocked(mocked.listImporterDatasets)
      .mockResolvedValueOnce({
        datasets: [
          { id: "ds-9", name: "2025 账套", created_at: "2026-10-28T09:00:00", source_filename: "a.xlsx" },
        ],
      })
      .mockResolvedValueOnce({ datasets: [] });
    render(<ImportWizard />);
    expect(await screen.findByText(/2025 账套/)).toBeTruthy();
    fireEvent.click(screen.getByText("删除"));
    await waitFor(() => expect(mocked.deleteImporterDataset).toHaveBeenCalledWith("ds-9"));
    await waitFor(() =>
      expect(screen.queryByText(/2025 账套/)).toBeNull(),
    );
  });
});
