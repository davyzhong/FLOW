"use client";

import { usePathname } from "next/navigation";

import { FlowIcon } from "./icons";

// 三模块产品语义入口（S01 Task 2C）+ 旧路由兼容分组（Task 5 集成前保留可达，
// 待模块化重组后归位）。旧入口保持在兼容分组而非散落顶层。
const moduleGroups = [
  {
    label: "模块入口",
    items: [
      ["library", "公开财报分析", "/public"],
      ["report", "企业内部分析工作台", "/internal"],
      ["library", "专业治理底座", "/internal#governance"],
    ],
  },
] as const;

const legacyCompatGroup = {
  label: "旧路由兼容入口",
  items: [
    ["upload", "数据接入", "/data"],
    ["dashboard", "经营总览", "/"],
    ["analysis", "分析与归因", "/investigations"],
    ["report", "四问工作台", "/analysis"],
    ["report", "报告与导出", "/reports"],
    ["chart", "报表分析", "/statements"],
    ["library", "指标库", "/metric-library"],
    ["chart", "经营概览", "/operations"],
  ],
} as const;

const groups = [moduleGroups[0], legacyCompatGroup] as const;

function isActiveItem(pathname: string | null, target: string): boolean {
  const current = pathname ?? "";
  if (target === "/") return current === "/";
  return current === target || current.startsWith(`${target}/`);
}

export function WorkflowNav() {
  const pathname = usePathname();
  return (
    <aside className="workflow-rail">
      <nav aria-label="FLOW 工作流">
        <div className="workflow-rail__brand"><span>F</span><strong>FLOW</strong></div>
        {groups.map((group) => (
          <div className="workflow-rail__group" key={group.label}>
            <p className="workflow-rail__group-label">{group.label}</p>
            <ol>
              {group.items.map(([icon, label, target]) => {
                const isActive = isActiveItem(pathname, target);
                return (
                  <li key={label} className={isActive ? "is-active" : undefined}>
                    <a href={target} aria-current={isActive ? "page" : undefined}>
                      <FlowIcon name={icon} />
                      <span><strong>{label}</strong><small>{isActive ? "当前" : "进入"}</small></span>
                    </a>
                  </li>
                );
              })}
            </ol>
          </div>
        ))}
        <div className="workflow-rail__footer"><span className="status-dot" />已连接治理数据层</div>
      </nav>
    </aside>
  );
}
