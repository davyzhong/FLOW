"use client";

// F-DataTable：TanStack Table（headless）+ Tailwind 的 FlowDataTable。
// 能力：排序 / 分页 / dense 变体 / summary footer / 空态整表替换（Carbon）。
// 样式全部 Tailwind 工具类——不引入带样式表格库。

import * as React from "react";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";

import { Button } from "./button";
import { cn } from "../../lib/utils";

// 列 meta 扩展：label 用于排序按钮的 aria 文案
declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    label?: string;
  }
}

type RowData = unknown;

export type FlowDataTableProps<TData> = {
  columns: ColumnDef<TData, unknown>[];
  data: TData[];
  /** 行唯一键（默认用索引） */
  getRowId?: (row: TData, index: number) => string;
  /** Carbon 空态模式：无数据时整表替换为空态节点 */
  emptyState?: React.ReactNode;
  /** 列合计 footer：columnId → 汇总节点（仅对该列渲染 footer 单元格） */
  summary?: (rows: TData[]) => Record<string, React.ReactNode>;
  dense?: boolean;
  pageSize?: number;
  initialSorting?: SortingState;
  className?: string;
};

export function FlowDataTable<TData>({
  columns,
  data,
  getRowId,
  emptyState,
  summary,
  dense = false,
  pageSize = 20,
  initialSorting = [],
  className,
}: FlowDataTableProps<TData>) {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting);
  const [pagination, setPagination] = React.useState({ pageIndex: 0, pageSize });

  const table = useReactTable({
    data,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getRowId: getRowId ? (row, index) => getRowId(row, index) : undefined,
  });

  if (data.length === 0 && emptyState) {
    // Carbon 模式：空态替换整表（表头也是噪音）
    return <>{emptyState}</>;
  }

  const summaryRow = summary ? summary(table.getFilteredRowModel().rows.map((r) => r.original)) : null;
  const cellPad = dense ? "py-1 px-2" : "py-1.5 px-3";

  return (
    <div className={cn("w-full", className)}>
      <table className="w-full border-collapse text-[13px]">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const canSort = header.column.getCanSort();
                const dir = header.column.getIsSorted();
                return (
                  <th
                    key={header.id}
                    className="border border-line-5 bg-zebra px-3 py-1.5 text-left font-semibold text-muted"
                  >
                    {canSort ? (
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 hover:text-ink"
                        onClick={header.column.getToggleSortingHandler()}
                        aria-label={`按 ${String(header.column.columnDef.meta?.label ?? header.id)} 排序`}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        <span aria-hidden="true" className="text-[10px]">
                          {dir === "asc" ? "▲" : dir === "desc" ? "▼" : "↕"}
                        </span>
                      </button>
                    ) : (
                      flexRender(header.column.columnDef.header, header.getContext())
                    )}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="odd:bg-zebra/60 hover:bg-blue-soft/40">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className={cn("border border-line-5 px-3 align-top", cellPad)}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
        {summaryRow ? (
          <tfoot>
            <tr>
              {table.getVisibleFlatColumns().map((column) => (
                <td
                  key={column.id}
                  className="border border-line-5 bg-zebra px-3 py-1.5 font-semibold"
                >
                  {summaryRow[column.id] ?? null}
                </td>
              ))}
            </tr>
          </tfoot>
        ) : null}
      </table>
      {table.getPageCount() > 1 ? (
        <nav className="mt-2 flex items-center gap-3 text-xs text-muted" aria-label="表格分页">
          <Button
            size="sm"
            variant="outline"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            上一页
          </Button>
          <span>
            第 {table.getState().pagination.pageIndex + 1} / {table.getPageCount()} 页
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            下一页
          </Button>
        </nav>
      ) : null}
    </div>
  );
}
