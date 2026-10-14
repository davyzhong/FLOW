import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";

export const metadata: Metadata = { title: "财务风险 | FLOW 驾驶舱" };

export default function 财务风险Page() {
  return (
    <AppShell>
      <CockpitModulePage moduleId="risk" title="财务风险" />
    </AppShell>
  );
}
