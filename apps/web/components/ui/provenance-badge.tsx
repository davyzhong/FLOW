"use client";

// F-Provenance：数据点级溯源徽标 + 悬停溯源卡（Stripe 式完整性交互）。
// page/page_anchor 来自迁移 0029 的 statement_line_item 列；
// 无溯源数据时渲染「—」——不伪造定位。

import { useEffect, useRef, useState, type ReactNode } from "react";

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

function anchorLabelOf(anchor: string | null): string {
  return anchor ? ANCHOR_LABELS[anchor] ?? anchor : "未知锚定";
}

/** 数值单元格级溯源：触发器即调用方 children（数值本体），hover 展示完整卡。
 *  无页码定位时原样渲染 children——不伪造溯源。
 *  键盘/触屏路径：每行的「p{page}」徽标（ProvenanceBadge）可聚焦、可点击
 *  展开；数值单元格不加 tabIndex（避免一张表数百个停止点）。 */
export function ProvenanceHover({
  page,
  anchor,
  sourceRef,
  value,
  unit,
  children,
  className,
}: ProvenanceProps & {
  /** 披露原值（未换算字符串），卡片中优先展示 */
  value?: string | null;
  /** 披露单位（如「人民币千元」） */
  unit?: string | null;
  children: ReactNode;
}) {
  if (page === null || page === undefined) {
    return <span className={cn("inline-block", className)}>{children}</span>;
  }
  return (
    <span className={cn("group relative inline-block w-full", className)}>
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 hidden w-64 -translate-x-1/2 rounded-md border border-line-3 bg-card p-3 text-left text-xs text-ink shadow-md group-hover:block"
      >
        {value ? (
          <span className="block">
            披露原值：<strong className="tabular-nums">{value}</strong>
            {unit ? <span className="text-muted">（{unit}）</span> : null}
          </span>
        ) : null}
        <span className={value ? "mt-1 block" : "block"}>
          原文页码：<strong>第 {page} 页</strong>
        </span>
        <span className="block">锚定方式：{anchorLabelOf(anchor)}</span>
        {sourceRef ? (
          <span className="mt-1 block break-all text-muted">来源：{sourceRef}</span>
        ) : null}
      </span>
    </span>
  );
}

export function ProvenanceBadge({ page, anchor, sourceRef, className }: ProvenanceProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLSpanElement | null>(null);

  // 点击外部关闭（键盘 Tab 离开由 onBlur 兜底）。
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

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
    <span className={cn("group relative inline-block", className)} ref={rootRef}>
      <button
        type="button"
        className="cursor-help rounded border border-line-4 px-1.5 py-0.5 text-xs text-muted hover:border-blue hover:text-blue"
        aria-label={`溯源：原文第 ${page} 页（${anchorLabel}）`}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        onBlur={() => setOpen(false)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
        }}
      >
        p{page}
      </button>
      <span
        role="tooltip"
        className={`pointer-events-none absolute bottom-full left-1/2 z-20 w-64 -translate-x-1/2 rounded-md border border-line-3 bg-card p-3 text-left text-xs text-ink shadow-md ${
          open ? "block" : "hidden"
        } group-hover:block group-focus-within:block`}
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
