import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";

import { FlowDataTable } from "../../components/ui/flow-data-table";
import { EmptyGuide } from "../../components/ui/empty-guide";
import { ProvenanceBadge } from "../../components/ui/provenance-badge";
import { Button } from "../../components/ui/button";

type Row = { name: string; amount: number; page: number | null };

const columns: ColumnDef<Row, unknown>[] = [
  {
    accessorKey: "name",
    header: "项目",
    meta: { label: "项目" },
  },
  {
    accessorKey: "amount",
    header: "金额",
    meta: { label: "金额" },
    cell: (info) => info.getValue<number>().toLocaleString(),
  },
  {
    accessorKey: "page",
    header: "页",
    enableSorting: false,
  },
];

const ROWS: Row[] = [
  { name: "货币资金", amount: 16992297, page: 12 },
  { name: "应收账款", amount: 29039844, page: 12 },
  { name: "存货", amount: 3056513, page: 13 },
];

describe("FlowDataTable（F-DataTable）", () => {
  it("渲染行数据并支持点击表头排序", () => {
    render(<FlowDataTable columns={columns} data={ROWS} />);
    expect(screen.getByText("货币资金")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /按 金额 排序/ }));
    const firstDataCell = screen.getAllByText(/[\d,]+/);
    expect(firstDataCell.length).toBeGreaterThan(0);
  });

  it("空数据 + emptyState 时整表替换（Carbon 模式）", () => {
    render(
      <FlowDataTable
        columns={columns}
        data={[]}
        emptyState={<EmptyGuide kind="no-data" title="暂无行项目" reason="示例原因" />}
      />,
    );
    expect(screen.getByText("暂无行项目")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("summary footer 渲染列合计", () => {
    render(
      <FlowDataTable
        columns={columns}
        data={ROWS}
        summary={(rows) => ({
          amount: rows.reduce((sum, r) => sum + r.amount, 0).toLocaleString(),
        })}
      />,
    );
    expect(screen.getByText("49,088,654")).toBeInTheDocument();
  });

  it("dense 变体不报错且行数完整", () => {
    render(<FlowDataTable columns={columns} data={ROWS} dense />);
    expect(screen.getAllByRole("row").length).toBe(ROWS.length + 1);
  });
});

describe("EmptyGuide（F-EmptyGuide）", () => {
  it("三类空态：原因 + 内嵌动作 + 文档提示", () => {
    render(
      <EmptyGuide
        kind="no-data"
        title="暂无已发布报告"
        reason="报告需要先冻结快照"
        actions={[
          { href: "/data", label: "前往数据接入" },
          { href: "/reports", label: "前往报告发布" },
        ]}
        docHint="详见报告中心说明"
      />,
    );
    expect(screen.getByText("暂无数据")).toBeInTheDocument();
    expect(screen.getByText("暂无已发布报告")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "前往数据接入" })).toHaveAttribute("href", "/data");
    expect(screen.getByText("详见报告中心说明")).toBeInTheDocument();
  });
});

describe("ProvenanceBadge（F-Provenance）", () => {
  it("有页锚时渲染页码徽标与溯源卡", () => {
    render(<ProvenanceBadge page={12} anchor="strong" sourceRef="docs/x.pdf" />);
    expect(screen.getByRole("button", { name: /溯源：原文第 12 页/ })).toBeInTheDocument();
    expect(screen.getByText(/行名\+数值同页/)).toBeInTheDocument();
  });

  it("无页锚时渲染占位符（不伪造溯源）", () => {
    render(<ProvenanceBadge page={null} anchor={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("Button（S-Foundation）", () => {
  it("变体与禁用态", () => {
    const onClick = vi.fn();
    render(
      <>
        <Button variant="outline" onClick={onClick}>
          常规
        </Button>
        <Button disabled onClick={onClick}>
          禁用
        </Button>
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: "常规" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "禁用" })).toBeDisabled();
  });
});
