import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";

export const metadata: Metadata = { title: "资产负债 | FLOW 驾驶舱" };

export default function BalanceSheetPage() {
  return (
    <AppShell>
      <CockpitModulePage
        moduleId="balance-sheet"
        title="资产负债"
      />
    </AppShell>
  );
}
