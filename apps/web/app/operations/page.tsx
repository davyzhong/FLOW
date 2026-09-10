import { AppShell } from "../../components/shell/app-shell";
import { OperationsOverviewApp } from "../../components/operations/operations-overview";

export const metadata = { title: "经营概览 | FLOW" };

export default function OperationsPage() {
  return (
    <AppShell>
      <OperationsOverviewApp />
    </AppShell>
  );
}
