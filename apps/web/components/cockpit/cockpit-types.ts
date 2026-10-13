/**
 * S01 CFO 驾驶舱 · 类型（单一真相源 = @flow/contracts）
 *
 * 契约纪律：
 * - 数值/趋势/结论/上下文类型全部取自 OpenAPI 生成的 contracts（勿重复定义）
 * - 本文件只补充「产品化语义」：极性枚举、管控状态枚举、请求态判别联合、筛选别名
 * - 所有上屏数字必须携带 snapshot_id（可追溯铁律），已在 contracts 层用必填字段约束
 */

import type {
  CockpitComparisons,
  CockpitConclusion,
  CockpitConclusionFinding,
  CockpitKpiCard,
  CockpitOverviewResponse,
  CockpitTrend,
  CockpitTrendSeries,
} from "../../lib/api/client";

export type {
  CockpitComparisons,
  CockpitConclusion,
  CockpitConclusionFinding,
  CockpitKpiCard,
  CockpitOverviewResponse,
  CockpitTrend,
  CockpitTrendSeries,
};

/** 指标极性：决定比较值着色方向（费用率下降是好事，不能一律「上升=绿」） */
export type CockpitPolarity = string;

/** 管控线状态：驱动 KPI 卡左边框状态色 */
export type CockpitControlStatus = string;

/** 总览页筛选：复用 dashboard 现有筛选契约（设计文档 §9-Q2 演进替换，不新增维度） */
export type CockpitFilters = import("../../lib/api/client").DashboardFilters;

/** 穿透档案：口径 → 来源 → 关联结论 → 历史 → 版本 */
export interface CockpitDrill {
  metricCode: string;
  title: string;
  value: string;
  unit: string;
  caliberNote?: string | null;
  snapshotId: string;
  comparisons: CockpitComparisons;
}

/** 五态（不可用不补零；unavailable 由组件层从 DashboardValue.status 判定） */
export type CockpitRequestState =
  | { kind: "loading" }
  | { kind: "error"; message?: string }
  | { kind: "empty" }
  | { kind: "loaded"; overview: CockpitOverviewResponse };
