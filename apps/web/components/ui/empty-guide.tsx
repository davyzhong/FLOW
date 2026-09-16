"use client";

// F-EmptyGuide（Carbon/Atlassian 空态标准）：解释为什么空 + 内嵌下一步动作。
// kind 三分类：first-use（首次使用）/ no-data（无数据）/ after-action（操作后为空）。
// 表格空态按 Carbon 模式整表替换——由调用方决定渲染位置。

import Link from "next/link";

import { cn } from "../../lib/utils";

export type EmptyGuideAction = { href: string; label: string };

export type EmptyGuideProps = {
  kind: "first-use" | "no-data" | "after-action";
  title: string;
  reason: string;
  actions?: EmptyGuideAction[];
  docHint?: string;
  className?: string;
};

const KIND_LABELS: Record<EmptyGuideProps["kind"], string> = {
  "first-use": "首次使用",
  "no-data": "暂无数据",
  "after-action": "操作完成",
};

export function EmptyGuide({ kind, title, reason, actions, docHint, className }: EmptyGuideProps) {
  return (
    <div
      role="status"
      data-kind={kind}
      className={cn(
        "rounded-lg border border-dashed border-line-3 bg-card px-6 py-8 text-center",
        className,
      )}
    >
      <p className="text-xs font-bold tracking-wider text-muted">{KIND_LABELS[kind]}</p>
      <p className="mt-1 text-base font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-muted">{reason}</p>
      {actions && actions.length > 0 ? (
        <p className="mt-4 flex items-center justify-center gap-3">
          {actions.map((action, index) => (
            <span key={action.href} className="flex items-center gap-3">
              {index > 0 ? <span aria-hidden="true">·</span> : null}
              <Link
                href={action.href}
                className="font-semibold text-info underline underline-offset-2"
              >
                {action.label}
              </Link>
            </span>
          ))}
        </p>
      ) : null}
      {docHint ? <p className="mt-3 text-xs text-muted">{docHint}</p> : null}
    </div>
  );
}
