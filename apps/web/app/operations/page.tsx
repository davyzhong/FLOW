import { AppShell } from "../../components/shell/app-shell";
import { OperationsApp } from "../../components/operations/operations-app";

export const metadata = { title: "经营概览 | FLOW" };

export default function OperationsPage() {
  return (
    <AppShell>
      <OperationsApp />
    </AppShell>
  );
}
