import { FlowIcon } from "./icons";

const items = [
  ["upload", "数据接入", "/data"],
  ["dashboard", "经营总览", "/"],
  ["analysis", "分析与归因", "/investigations"],
  ["report", "报告与导出", "/reports"],
] as const;

export function WorkflowNav() {
  return (
    <aside className="workflow-rail">
      <nav aria-label="FLOW 工作流">
        <div className="workflow-rail__brand"><span>F</span><strong>FLOW</strong></div>
        <ol>
          {items.map(([icon, label, target], index) => (
            <li key={label} className={index === 1 ? "is-active" : undefined}>
              <a href={target} aria-current={index === 1 ? "page" : undefined}>
                <FlowIcon name={icon} />
                <span><strong>{label}</strong><small>{target === "/" ? "当前" : "进入"}</small></span>
              </a>
            </li>
          ))}
        </ol>
        <div className="workflow-rail__footer"><span className="status-dot" />已连接治理数据层</div>
      </nav>
    </aside>
  );
}
