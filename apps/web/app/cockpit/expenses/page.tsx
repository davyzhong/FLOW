import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";

export const metadata: Metadata = { title: "费用分析 | FLOW 驾驶舱" };

export default function 费用分析Page() {
  return (
    <AppShell>
      <CockpitModulePage moduleId="expenses" title="费用分析" />
    </AppShell>
  );
}
