import type { DashboardFilters, DashboardResponse } from "../../lib/api/client";

export function DashboardHeader({
  dashboard,
  onFiltersChange,
}: {
  dashboard: DashboardResponse;
  onFiltersChange?: (filters: DashboardFilters) => void;
}) {
  const active = dashboard.active_filters;
  const dimensions = dashboard.filter_options.dimensions;
  const current: DashboardFilters = {
    period_view: active.period_view,
    organization_id: active.organization_id,
    customer_segment_id: active.customer_segment_id,
    logistics_product_id: active.logistics_product_id,
    region_id: active.region_id,
  };
  const change = (key: keyof DashboardFilters, value: string) =>
    onFiltersChange?.({ ...current, [key]: value || undefined });
  return (
    <header className="dashboard-header" id="overview">
      <div>
        <p className="eyebrow">FINANCE BUSINESS PARTNER · 经营总览</p>
        <h2>集团经营驾驶舱</h2>
        <p className="dashboard-header__context">截至 {dashboard.context.as_of_month} · 物流与供应链业务</p>
      </div>
      <div className="dashboard-filters" aria-label="驾驶舱筛选器">
        <label>期间
          <select aria-label="期间" value={active.period_view} onChange={(event) => change("period_view", event.target.value)}>
            <option value="month">本月</option><option value="ytd">年初至今</option>
          </select>
        </label>
        {dimensions.map((dimension) => {
          const key = `${dimension.dimension}_id` as keyof DashboardFilters;
          const value = current[key] ?? "";
          return (
            <label key={dimension.dimension}>{dimension.label}
              <select aria-label={dimension.label} value={value} onChange={(event) => change(key, event.target.value)}>
                <option value="">全部</option>
                {dimension.options.map((option) => <option value={option.id} key={option.id}>{option.name}</option>)}
              </select>
            </label>
          );
        })}
      </div>
    </header>
  );
}
