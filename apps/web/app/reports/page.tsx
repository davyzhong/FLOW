import { ReportsCenter } from "../../components/reports/reports-center";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "报告中心 | FLOW" };

export default function ReportsPage() {
  return (
    <AppShell>
      <ReportsCenter />
    </AppShell>
  );
}
