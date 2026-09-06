import type { ReactNode } from "react";

import { WorkflowNav } from "../dashboard/workflow-nav";
import "./app-shell.css";

export function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="app-shell">
      <WorkflowNav />
      <main className="app-shell__main">{children}</main>
    </div>
  );
}
