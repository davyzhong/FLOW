import { FlowIcon } from "./icons";

const items = [
  ["upload", "数据接入", "已发布"],
  ["dashboard", "经营总览", "当前"],
  ["analysis", "分析与归因", "4 条发现"],
  ["report", "报告与导出", "月报"],
] as const;

export function WorkflowNav() {
  return (
    <aside className="workflow-rail">
      <nav aria-label="FLOW 工作流">
        <div className="workflow-rail__brand"><span>F</span><strong>FLOW</strong></div>
        <ol>
          {items.map(([icon, label, meta], index) => (
            <li key={label} className={index === 1 ? "is-active" : undefined}>
              <a href={index === 1 ? "#overview" : `#workflow-${index}`} aria-current={index === 1 ? "page" : undefined}>
                <FlowIcon name={icon} />
                <span><strong>{label}</strong><small>{meta}</small></span>
              </a>
            </li>
          ))}
        </ol>
        <div className="workflow-rail__footer"><span className="status-dot" />已连接治理数据层</div>
      </nav>
    </aside>
  );
}
