"use client";

/**
 * S01 CFO 驾驶舱 · 全局筛选条（批次 A）
 *
 * 设计依据：设计文档 §4.1 全局框架 + §5「期间 / 组织口径 / 币种 / 累计当月 / 对比基准」。
 * 硬约束：
 * - 筛选状态进 URL（可分享/可回链），与既有 dashboard 契约一致；
 * - 切换企业/组织口径必须重新校验权限（越权返回 403，不返回空数据）；
 * - 对比基准含「预算」时若预算未就绪则该选项置灰 + 说明（不假装可用）。
 */

import type { DashboardResponse } from "../../lib/api/client";
import type { CockpitFilters } from "./cockpit-types";

const PERIOD_VIEWS = [
  { value: "ytd", label: "累计" },
  { value: "month", label: "当月" },
] as const;

const DIMENSIONS = [
  { dimension: "organization", field: "organization_id", label: "组织口径", ariaLabel: "组织口径筛选" },
  { dimension: "customer_segment", field: "customer_segment_id", label: "客户群", ariaLabel: "客户群筛选" },
  { dimension: "logistics_product", field: "logistics_product_id", label: "产品", ariaLabel: "产品筛选" },
  { dimension: "region", field: "region_id", label: "区域", ariaLabel: "区域筛选" },
] as const;

export function CockpitFilterBar({
  filters,
  dimensions,
  onChange,
  disabled,
}: {
  filters: CockpitFilters;
  dimensions: DashboardResponse["filter_options"]["dimensions"];
  onChange: (next: CockpitFilters) => void;
  disabled?: boolean;
}) {
  const set = (patch: Partial<CockpitFilters>) => onChange({ ...filters, ...patch });

  return (
    <div className="cp-filters" data-testid="cockpit-filters" aria-label="驾驶舱全局筛选">
      <label className="cp-filters__item">
        <span>期间</span>
        <select
          value={filters.period_view ?? "ytd"}
          disabled={disabled}
          onChange={(e) => set({ period_view: e.target.value as "ytd" | "month" })}
        >
          {PERIOD_VIEWS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </label>

      {DIMENSIONS.map(({ dimension, field, label, ariaLabel }) => {
        const optionGroup = dimensions.find((entry) => entry.dimension === dimension);
        const options = optionGroup?.options ?? [];
        const active = filters[field];
        return (
          <label className="cp-filters__item" key={dimension}>
            <span>{label}</span>
            <select
              value={active ?? ""}
              disabled={disabled}
              aria-label={ariaLabel}
              onChange={(event) => set({ [field]: event.target.value || null })}
            >
              <option value="">全部{label}</option>
              {active && !options.some((option) => option.id === active) ? (
                <option value={active}>当前 ID（选项不可用）</option>
              ) : null}
              {options.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}
            </select>
          </label>
        );
      })}

      <p className="cp-filters__hint">
        币种与预算对比适用于内部经营数据
      </p>
    </div>
  );
}
