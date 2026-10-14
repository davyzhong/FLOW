import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";
import { flowApi } from "../../../lib/api/client";

export const metadata: Metadata = { title: "营运资金 | FLOW 驾驶舱" };

export default function WorkingCapitalPage() {
  return (
    <AppShell>
      <CockpitModulePage
        moduleId="working-capital"
        title="营运资金"
        fetcher={(signal) => flowApi.getCockpitModule("working-capital", signal)}
      />
    </AppShell>
  );
}
