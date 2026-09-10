import { DashboardApp } from "../components/dashboard/dashboard-app";
import { AppShell } from "../components/shell/app-shell";

export default function HomePage() {
  return (
    <AppShell>
      <DashboardApp />
    </AppShell>
  );
}
