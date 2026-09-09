"use client";

import { usePathname } from "next/navigation";

import { FlowIcon } from "./icons";

// 双轨产品结构（D045）：一套底座、两条轨道。数据接入两轨共用；
// 财务分析轨面向 Finance BP，经营分析轨面向经营/业务管理者。
const groups = [
  {
    label: "数据层",
    items: [["upload", "数据接入", "/data"]],
  },
  {
    label: "财务分析 · Finance BP",
    items: [
      ["dashboard", "经营总览", "/"],
      ["analysis", "分析与归因", "/investigations"],
      ["report", "四问工作台", "/analysis"],
      ["report", "报告与导出", "/reports"],
      ["chart", "报表分析", "/statements"],
      ["library", "指标库", "/metric-library"],
    ],
  },
  {
    label: "经营分析 · 业务管理",
    items: [["chart", "经营概览（演示）", "/operations"]],
  },
] as const;

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
