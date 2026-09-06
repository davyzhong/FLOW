import { InvestigationsIndex } from "../../components/investigation/investigations-index";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "分析与归因 | FLOW" };

export default function InvestigationsIndexPage() {
  return (
    <AppShell>
      <InvestigationsIndex />
    </AppShell>
  );
}
