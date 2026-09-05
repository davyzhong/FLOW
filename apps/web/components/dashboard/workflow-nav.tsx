"use client";

import { usePathname } from "next/navigation";

import { FlowIcon } from "./icons";

const items = [
  ["upload", "数据接入", "/data"],
  ["dashboard", "经营总览", "/"],
  ["analysis", "分析与归因", "/investigations"],
  ["report", "报告与导出", "/reports"],
  ["chart", "报表分析", "/statements"],
] as const;

export function WorkflowNav() {
  const pathname = usePathname();
  return (
    <aside className="workflow-rail">
      <nav aria-label="FLOW 工作流">
        <div className="workflow-rail__brand"><span>F</span><strong>FLOW</strong></div>
        <ol>
          {items.map(([icon, label, target]) => {
            const isActive = pathname === target;
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
        <div className="workflow-rail__footer"><span className="status-dot" />已连接治理数据层</div>
      </nav>
    </aside>
  );
}
