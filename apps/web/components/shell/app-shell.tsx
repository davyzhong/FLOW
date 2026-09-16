import type { ReactNode } from "react";

import { WorkflowNav } from "../dashboard/workflow-nav";
import "./app-shell.css";

export function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  // AUTH_TOKEN 启用时侧栏尾部提供唯一退出入口（/login 无 AppShell，不显示）。
  const showLogout = Boolean(process.env.AUTH_TOKEN);
  return (
    <div className="app-shell">
      <WorkflowNav showLogout={showLogout} />
      <main className="app-shell__main">{children}</main>
    </div>
  );
}
