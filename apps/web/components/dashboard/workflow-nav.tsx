"use client";

import { usePathname } from "next/navigation";

import { FlowIcon } from "./icons";

// 两级信息架构（前端整体优化 F1-1）：模块 → 页面，每条入口都落到有内容的
// 真实页面；不再有「旧路由兼容入口」这类未完成信息架构的暴露。
// 约束（e2e 双守护）：navigation.spec 要求每个交互路由在导航中恰有 1 个
// plain href 入口；module-boundaries.spec 要求 /internal#governance 锚点存在。
const moduleGroups = [
  {
    label: "公开财报分析",
    items: [
      ["library", "模块总览", "/public"],
      ["chart", "报表分析", "/statements"],
      ["library", "指标库", "/metric-library"],
    ],
  },
  {
    label: "内部经营分析",
    items: [
      ["report", "工作台总览", "/internal"],
      ["dashboard", "经营总览", "/"],
      ["upload", "数据接入", "/data"],
      ["analysis", "调查归因", "/investigations"],
      ["report", "四问工作台", "/analysis"],
      ["report", "报告与导出", "/reports"],
      ["chart", "经营概览", "/operations"],
    ],
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
        {moduleGroups.map((group) => (
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
