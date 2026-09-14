import { AppShell } from "../../components/shell/app-shell";
import { StatementApp } from "../../components/statements/statement-app";

export const metadata = { title: "报表分析 | FLOW" };

export default function StatementsPage() {
  return (
    <AppShell>
      <StatementApp />
    </AppShell>
  );
}
