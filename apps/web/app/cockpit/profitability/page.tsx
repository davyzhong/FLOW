import type { Metadata } from "next";

import { CockpitProfitabilityPage } from "../../../components/cockpit/profitability-page";
import { AppShell } from "../../../components/shell/app-shell";

export const metadata: Metadata = { title: "盈利能力与杜邦分析 | FLOW 驾驶舱" };

export default function ProfitabilityPage() {
  return (
    <AppShell>
      <CockpitProfitabilityPage />
    </AppShell>
  );
}
