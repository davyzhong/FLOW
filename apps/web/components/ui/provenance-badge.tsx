"use client";

// F-Provenance：数据点级溯源徽标 + 悬停溯源卡（Stripe 式完整性交互）。
// page/page_anchor 来自迁移 0029 的 statement_line_item 列；
// 无溯源数据时渲染「—」——不伪造定位。

import { cn } from "../../lib/utils";

export type ProvenanceProps = {
  page: number | null;
  anchor: string | null;
  /** 原文相对路径（如 docs/knowledge-base/.../xxx.pdf），用于卡片展示 */
  sourceRef?: string | null;
  className?: string;
};

const ANCHOR_LABELS: Record<string, string> = {
  strong: "行名+数值同页",
  weak: "仅数值同页",
};

export function ProvenanceBadge({ page, anchor, sourceRef, className }: ProvenanceProps) {
  if (page === null || page === undefined) {
    return (
      <span
        className={cn("inline-block text-xs text-muted", className)}
        title="该行暂无页码定位（不伪造溯源）"
      >
        —
      </span>
    );
  }
  const anchorLabel = anchor ? ANCHOR_LABELS[anchor] ?? anchor : "未知锚定";
  return (
    <span className={cn("group relative inline-block", className)}>
      <button
        type="button"
        className="cursor-help rounded border border-line-4 px-1.5 py-0.5 text-xs text-muted hover:border-blue hover:text-blue"
        aria-label={`溯源：原文第 ${page} 页（${anchorLabel}）`}
      >
        p{page}
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 hidden w-64 -translate-x-1/2 rounded-md border border-line-3 bg-card p-3 text-left text-xs text-ink shadow-md group-hover:block"
      >
        <span className="block font-semibold">数据点溯源</span>
        <span className="mt-1 block">
          原文页码：<strong>第 {page} 页</strong>
        </span>
        <span className="block">锚定方式：{anchorLabel}</span>
        {sourceRef ? (
          <span className="mt-1 block break-all text-muted">来源：{sourceRef}</span>
        ) : null}
      </span>
    </span>
  );
}
