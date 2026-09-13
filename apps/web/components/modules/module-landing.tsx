"use client";

// Task 2C：模块落地页组件（S01 设计 §5.4 模块描述合同的同字节静态 fixture）。
// 只呈现批准的模块描述：implemented 提供进入链接；designed 一律「规划中」，
// 不渲染任何暗示已实现能力的操作按钮。

import Link from "next/link";
import "./module-landing.css";

export type ModuleDescriptor = {
  id: string;
  name: string;
  layer: "product" | "governance";
  status: "implemented" | "designed";
  entry?: { href: string; label: string };
};

// 与 docs/superpowers/specs/2026-09-13-flow-three-agent-parallel-orchestration-design.md §5.4 同源
export const APPROVED_MODULES: ModuleDescriptor[] = [
  {
    id: "public_analysis",
    name: "公开财报分析",
    layer: "product",
    status: "implemented",
    entry: { href: "/statements", label: "进入公开财报分析" },
  },
  {
    id: "internal_workbench",
    name: "企业内部分析工作台",
    layer: "product",
    status: "designed",
  },
  {
    id: "professional_governance",
    name: "专业治理底座",
    layer: "governance",
    status: "designed",
  },
];

const LAYER_LABELS: Record<ModuleDescriptor["layer"], string> = {
  product: "产品层",
  governance: "治理层",
};

export function ModuleLanding({
  title,
  subtitle,
  moduleIds,
}: {
  title: string;
  subtitle: string;
  moduleIds: string[];
}) {
  const modules = APPROVED_MODULES.filter((m) => moduleIds.includes(m.id));
  return (
    <section className="module-landing" aria-label={title}>
      <header className="module-landing__header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </header>
      <ul className="module-landing__grid">
        {modules.map((m) => (
          <li key={m.id} className={`module-landing__card module-landing__card--${m.status}`}>
            <header>
              <strong>{m.name}</strong>
              <span className={`module-landing__status module-landing__status--${m.status}`}>
                {m.status === "implemented" ? "已实现" : "规划中"}
              </span>
            </header>
            <small>{LAYER_LABELS[m.layer]}</small>
            {m.status === "implemented" && m.entry ? (
              <Link href={m.entry.href} className="module-landing__entry">
                {m.entry.label}
              </Link>
            ) : (
              <p className="module-landing__planned">
                该模块处于设计阶段，尚未提供可操作入口。
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
