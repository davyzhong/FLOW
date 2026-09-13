import { AppShell } from "../../components/shell/app-shell";
import { ModuleLanding } from "../../components/modules/module-landing";

export default function InternalModulePage() {
  return (
    <AppShell>
      <ModuleLanding
        title="企业内部分析"
        subtitle="企业内部分析工作台与专业治理底座（设计阶段，待内部数据授权）。"
        moduleIds={["internal_workbench", "professional_governance"]}
      />
    </AppShell>
  );
}
