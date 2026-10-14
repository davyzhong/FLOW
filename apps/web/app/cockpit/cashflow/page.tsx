import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";

export const metadata: Metadata = { title: "现金流 | FLOW 驾驶舱" };

export default function 现金流Page() {
  return (
    <AppShell>
      <CockpitModulePage moduleId="cashflow" title="现金流" />
    </AppShell>
  );
}
