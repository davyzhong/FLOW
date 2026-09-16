import type { SVGProps } from "react";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  FileText,
  LayoutDashboard,
  TriangleAlert,
  TrendingUp,
  Upload,
  type LucideProps,
} from "lucide-react";

// v2（2026-09-16）：图标收敛到 lucide-react（项目既有图标依赖，与 shadcn 体系一致）。
// 保持 name 字符串 API 不变，调用方零改动；如需新图标直接用 lucide 组件，不再扩此映射。
const registry = {
  upload: Upload,
  dashboard: LayoutDashboard,
  analysis: TrendingUp,
  report: FileText,
  chart: BarChart3,
  library: BookOpen,
  alert: TriangleAlert,
  arrow: ArrowRight,
} as const;

export function FlowIcon({ name, ...props }: SVGProps<SVGSVGElement> & { name: string }) {
  const Icon = registry[name as keyof typeof registry] ?? LayoutDashboard;
  return <Icon aria-hidden strokeWidth={1.8} {...(props as LucideProps)} />;
}
