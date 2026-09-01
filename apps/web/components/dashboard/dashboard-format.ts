import type { DashboardResponse } from "../../lib/api/client";

export function dashboardStateMessage(
  state: DashboardResponse["state"],
): string {
  switch (state) {
    case "empty":
      return "尚无可展示的经营数据";
    case "stale":
      return "数据已陈旧，请检查最新发布批次";
    case "degraded":
      return "部分分析面板已降级";
    case "error":
      return "经营驾驶舱暂时无法加载";
    case "ready":
      return "已发布经营数据";
  }
}
