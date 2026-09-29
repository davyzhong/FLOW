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

import type { CockpitFilters } from "./cockpit-types";

const PERIOD_VIEWS = [
  { value: "ytd", label: "累计" },
  { value: "month", label: "当月" },
] as const;

export function CockpitFilterBar({
  filters,
  onChange,
  disabled,
  sourceNotice,
}: {
  filters: CockpitFilters;
  onChange: (next: CockpitFilters) => void;
  disabled?: boolean;
  /** 演示/公开期提示：预算类基准不可用时显示 */
  sourceNotice?: string | null;
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

      <label className="cp-filters__item">
        <span>组织口径</span>
        <input
          type="text"
          placeholder="组织 ID（留空=全部）"
          defaultValue={filters.organization_id ?? ""}
          disabled={disabled}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if ((filters.organization_id ?? "") !== v) {
              set({ organization_id: v === "" ? null : v });
            }
          }}
          aria-label="组织口径筛选"
        />
      </label>

      <label className="cp-filters__item">
        <span>客户群</span>
        <input
          type="text"
          placeholder="客户群 ID"
          defaultValue={filters.customer_segment_id ?? ""}
          disabled={disabled}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if ((filters.customer_segment_id ?? "") !== v) {
              set({ customer_segment_id: v === "" ? null : v });
            }
          }}
          aria-label="客户群筛选"
        />
      </label>

      <label className="cp-filters__item">
        <span>产品</span>
        <input
          type="text"
          placeholder="产品 ID"
          defaultValue={filters.logistics_product_id ?? ""}
          disabled={disabled}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if ((filters.logistics_product_id ?? "") !== v) {
              set({ logistics_product_id: v === "" ? null : v });
            }
          }}
          aria-label="产品筛选"
        />
      </label>

      <label className="cp-filters__item">
        <span>区域</span>
        <input
          type="text"
          placeholder="区域 ID"
          defaultValue={filters.region_id ?? ""}
          disabled={disabled}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if ((filters.region_id ?? "") !== v) {
              set({ region_id: v === "" ? null : v });
            }
          }}
          aria-label="区域筛选"
        />
      </label>

      <p className="cp-filters__hint">
        币种与对比基准属内部期功能
        {sourceNotice ? ` · ${sourceNotice}` : ""}
      </p>
    </div>
  );
}
