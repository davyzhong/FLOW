"use client";

/**
 * S01 CFO 驾驶舱 · 总览页容器（批次 A）
 *
 * 设计依据：设计文档 §5.1 集团总览 + §7 五态。
 * 执行序：filters → load → 五态渲染。
 * 与既有 DashboardApp 的差异：
 * - 三基准 KPI 卡（同比/环比/行业分位）+ 口径注 + 穿透
 * - 经营结论条（服务端生成，可溯源 Finding）
 * - 演示数据源全局标注
 * - 趋势面板（手写 SVG，零新依赖）
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import { flowApi } from "../../lib/api/client";
import { CockpitConclusionBar, CockpitDrillDrawer } from "./drill-drawer";
import { CockpitFilterBar } from "./cockpit-filter-bar";
import { CockpitKpiGrid } from "./kpi-card";
import type {
  CockpitDrill,
  CockpitFilters,
  CockpitOverviewResponse,
  CockpitRequestState,
  CockpitTrendSeries,
} from "./cockpit-types";
import { CockpitTrendPanel } from "./trend-panel";

const defaultLoad = (
  filters: CockpitFilters,
  signal: AbortSignal,
): Promise<CockpitOverviewResponse> => flowApi.getCockpitOverview(filters, signal);

function queryString(filters: CockpitFilters): string {
  const query = new URLSearchParams();
  for (const key of [
    "period_view",
    "organization_id",
    "customer_segment_id",
    "logistics_product_id",
    "region_id",
  ] as const) {
    const value = filters[key];
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  }
  return query.toString();
}

export function CockpitOverviewApp({
  load = defaultLoad,
  initialFilters = {},
}: {
  load?: (
    filters: CockpitFilters,
    signal: AbortSignal,
  ) => Promise<CockpitOverviewResponse>;
  initialFilters?: CockpitFilters;
}) {
  const [filters, setFilters] = useState<CockpitFilters>(initialFilters);
  const [request, setRequest] = useState<CockpitRequestState>({ kind: "loading" });
  const [drill, setDrill] = useState<CockpitDrill | null>(null);
  const [requestKey, setRequestKey] = useState(0);
  const serialized = useMemo(() => queryString(filters), [filters]);

  useEffect(() => {
    const controller = new AbortController();
    // 不在 effect 内同步 setState（lint: cascading renders）；loading 态由
    // filters/requestKey 变化时在事件侧或由首次初始态覆盖。
    load(filters, controller.signal).then(
      (overview) => {
        if (controller.signal.aborted) return;
        setRequest(
          overview.state === "empty" || (overview.kpi_cards ?? []).length === 0
            ? { kind: "empty" }
            : { kind: "loaded", overview },
        );
      },
      () => {
        if (!controller.signal.aborted) setRequest({ kind: "error" });
      },
    );
    return () => controller.abort();
  }, [filters, load, requestKey]);

  const onFilterChange = useCallback((next: CockpitFilters) => {
    setRequest({ kind: "loading" });
    setFilters(next);
  }, []);

  useEffect(() => {
    const location = serialized
      ? `?${serialized}`
      : window.location.pathname;
    window.history.replaceState(null, "", location);
  }, [serialized]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrill(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const retry = useCallback(() => {
    setRequestKey((v) => v + 1);
  }, []);

  if (request.kind === "loading") {
    return (
      <div className="cockpit">
        <CockpitFilterBar
          filters={filters}
          onChange={onFilterChange}
          disabled
        />
        <div className="cockpit cockpit--state" role="status" aria-live="polite">
          <p>正在加载驾驶舱数据…</p>
        </div>
      </div>
    );
  }

  if (request.kind === "error") {
    return (
      <div className="cockpit">
        <CockpitFilterBar filters={filters} onChange={onFilterChange} />
        <div className="cockpit cockpit--state cockpit--error" role="alert">
          <p>驾驶舱数据加载失败。</p>
          <button type="button" onClick={retry}>
            重试
          </button>
        </div>
      </div>
    );
  }

  if (request.kind === "empty") {
    return (
      <div className="cockpit">
        <CockpitFilterBar filters={filters} onChange={onFilterChange} />
        <div className="cockpit cockpit--state cockpit--empty" data-testid="cockpit-empty">
          <p>当前筛选条件下没有可展示的经营数据。</p>
          <p className="cockpit__hint">可调整上方筛选条件后重试；本系统不补零、不造数。</p>
        </div>
      </div>
    );
  }

  const { overview } = request;
  const trendSeries: CockpitTrendSeries[] = (overview.trends ?? []).flatMap(
    (t) => t.series ?? [],
  );

  return (
    <div className="cockpit" data-state={overview.state}>
      <CockpitFilterBar
        filters={filters}
        onChange={onFilterChange}
        sourceNotice={overview.source_notice}
      />
      {overview.source_notice ? (
        <p className="cockpit__notice" data-testid="cockpit-source-notice">
          {overview.source_notice}
        </p>
      ) : null}

      <header className="cockpit__head">
        <h1>集团财务总览</h1>
        <p className="cockpit__meta">
          截至 {overview.context.as_of_month} · 快照 {overview.context.metric_snapshot_id?.slice(0, 8) ?? "—"} ·
          指标集 {overview.context.metric_definition_set_id?.slice(0, 8) ?? "—"}
        </p>
      </header>

      <CockpitKpiGrid cards={overview.kpi_cards ?? []} onDrill={setDrill} />

      {trendSeries.length > 0 ? (
        <section className="cockpit__trends" aria-label="趋势">
          <div className="section-heading">
            <div>
              <span>02</span>
              <h3>趋势</h3>
            </div>
            <small>只读已冻结事实，不重算</small>
          </div>
          <div className="trend-grid">
            {trendSeries.map((series) => (
              <CockpitTrendPanel key={series.key} series={series} />
            ))}
          </div>
        </section>
      ) : null}

      <CockpitConclusionBar
        text={overview.conclusion.text}
        findings={overview.conclusion.findings ?? []}
        tone={overview.conclusion.tone}
      />

      <CockpitDrillDrawer drill={drill} onClose={() => setDrill(null)} />
    </div>
  );
}
