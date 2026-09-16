import { AppShell } from "../../components/shell/app-shell";
import {
  ModuleLanding,
  type FunctionEntry,
} from "../../components/modules/module-landing";

export const metadata = { title: "企业内部分析 | FLOW" };

// F1-2：designed 模块卡保持诚实状态；上方新增「已上线功能入口」真实区块，
// 消灭「点不进来/看不到功能」的断头路（入口全部指向已实现路由）。
const FUNCTION_ENTRIES: FunctionEntry[] = [
  {
    href: "/",
    label: "经营总览",
    description: "核心指标、毛利桥与趋势（需已发布快照）",
  },
  {
    href: "/data",
    label: "数据接入",
    description: "标准工作簿上传、映射确认与导入",
  },
  {
    href: "/investigations",
    label: "调查归因",
    description: "Findings 调查、证据核验与结论",
  },
  {
    href: "/analysis",
    label: "四问工作台",
    description: "经营四问逐项下钻",
  },
  {
    href: "/reports",
    label: "报告与导出",
    description: "报告快照冻结与多格式发布",
  },
  {
    href: "/operations",
    label: "经营概览",
    description: "公开经营披露的六主题概览",
  },
  {
    href: "/metric-library",
    label: "指标库",
    description: "指标字典、治理草稿与依赖图",
  },
];

export default function InternalModulePage() {
  return (
    <AppShell>
      <div id="governance">
        <ModuleLanding
          title="企业内部分析"
          subtitle="当前已上线的内部经营分析功能入口如下；月度周期工作台等专业模块处于设计阶段（待内部数据授权）。"
          moduleIds={["internal_workbench", "professional_governance"]}
          functionEntries={FUNCTION_ENTRIES}
        />
      </div>
    </AppShell>
  );
}
