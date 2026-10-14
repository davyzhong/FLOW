import type { Metadata } from "next";

import { AppShell } from "../../../components/shell/app-shell";
import { CockpitModulePage } from "../../../components/cockpit/module-page";

export const metadata: Metadata = { title: "集团合并 | FLOW 驾驶舱" };

export default function 集团合并Page() {
  return (
    <AppShell>
      <CockpitModulePage moduleId="consolidation" title="集团合并" />
    </AppShell>
  );
}
