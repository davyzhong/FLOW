import { AppShell } from "../../components/shell/app-shell";
import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

export const metadata = { title: "指标库 | FLOW" };

export default function MetricLibraryPage() {
  return (
    <AppShell>
      <MetricLibraryApp />
    </AppShell>
  );
}
