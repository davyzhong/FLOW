import { AppShell } from "../../components/shell/app-shell";
import {
  ModuleLanding,
  type FunctionEntry,
} from "../../components/modules/module-landing";

export const metadata = { title: "公开财报分析 | FLOW" };

const FUNCTION_ENTRIES: FunctionEntry[] = [
  {
    href: "/statements",
    label: "报表分析",
    description: "已入库财报的四表可视化与逐行溯源",
  },
  {
    href: "/metric-library",
    label: "指标库",
    description: "指标字典、口径与公式（含执行绑定）",
  },
];

export default function PublicModulePage() {
  return (
    <AppShell>
      <ModuleLanding
        title="公开财报分析"
        subtitle="面向公开披露财报的确定性分析：数字全部来自确定性引擎，可逐行溯源到原文页码。"
        moduleIds={["public_analysis"]}
        functionEntries={FUNCTION_ENTRIES}
      />
    </AppShell>
  );
}
