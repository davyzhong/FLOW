import { AppShell } from "../../components/shell/app-shell";
import { ModuleLanding } from "../../components/modules/module-landing";

export default function PublicModulePage() {
  return (
    <AppShell>
      <ModuleLanding
        title="公开财报分析"
        subtitle="面向公开披露财报的确定性分析与报告（已实现）。"
        moduleIds={["public_analysis"]}
      />
    </AppShell>
  );
}
