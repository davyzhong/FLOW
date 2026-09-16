"use client";

// 模块落地页组件（S01 设计 §5.4 模块描述合同）。只呈现批准的模块描述：
// implemented 提供进入链接；designed 一律「规划中」，不渲染任何暗示已实现
// 能力的操作按钮（模块边界诚实约束，module-boundaries.spec 守护）。
//
// F1-2 新增：`functionEntries` prop 允许落地页携带「已上线功能入口」区块
// ——入口指向真实存在的路由，与 designed 模块卡严格分离，不违反边界诚实。

import Link from "next/link";
import "./module-landing.css";

export type ModuleDescriptor = {
  id: string;
  name: string;
  layer: "product" | "governance";
  status: "implemented" | "designed" | "gated";
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

const STATUS_LABELS: Record<ModuleDescriptor["status"], string> = {
  implemented: "已实现",
  designed: "规划中",
  gated: "受控开放",
};

export type FunctionEntry = { href: string; label: string; description: string };

export function ModuleLanding({
  title,
  subtitle,
  moduleIds,
  functionEntries,
}: {
  title: string;
  subtitle: string;
  moduleIds: string[];
  functionEntries?: FunctionEntry[];
}) {
  const modules = APPROVED_MODULES.filter((m) => moduleIds.includes(m.id));
  return (
    <section className="module-landing" aria-label={title}>
      <header className="module-landing__header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </header>
      {functionEntries && functionEntries.length > 0 ? (
        <div className="module-landing__functions" aria-label="已上线功能入口">
          <h2>已上线功能</h2>
          <ul>
            {functionEntries.map((entry) => (
              <li key={entry.href}>
                <Link href={entry.href}>
                  <strong>{entry.label}</strong>
                  <small>{entry.description}</small>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <ul className="module-landing__grid">
        {modules.map((m) => (
          <li
            key={m.id}
            id={`module-${m.id}`}
            className={`module-landing__card module-landing__card--${m.status}`}
          >
            <header>
              <strong>{m.name}</strong>
              <span className={`module-landing__status module-landing__status--${m.status}`}>
                {STATUS_LABELS[m.status]}
              </span>
            </header>
            <small>{LAYER_LABELS[m.layer]}</small>
            {m.status === "implemented" && m.entry ? (
              <Link href={m.entry.href} className="module-landing__entry">
                {m.entry.label}
              </Link>
            ) : (
              <p className="module-landing__planned">
                {m.status === "gated"
                  ? "该模块受控开放，需相应权限访问。"
                  : "该模块处于设计阶段，尚未提供可操作入口。"}
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
