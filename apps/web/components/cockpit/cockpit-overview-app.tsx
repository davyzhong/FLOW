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

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import "./cockpit.css";

import { flowApi, type CockpitModuleResponse, type CockpitProfitabilityResponse, type DashboardResponse } from "../../lib/api/client";
import { ActionItemPanel } from "./action-panel";
import { CockpitConclusionBar, CockpitDrillDrawer } from "./drill-drawer";
import { CockpitFilterBar } from "./cockpit-filter-bar";
import { CockpitKpiGrid } from "./kpi-card";
import { CockpitOverviewSourcePanel, CockpitOverviewVisuals, type CockpitOverviewSupplements } from "./cockpit-overview-visuals";
import type {
  CockpitDrill,
  CockpitFilters,
  CockpitOverviewResponse,
  CockpitRequestState,
  CockpitTrendSeries,
} from "./cockpit-types";

const defaultLoadSupplement = async (signal: AbortSignal): Promise<CockpitOverviewSupplements> => {
  const [profitability, cashflow, expenses] = await Promise.allSettled([
    flowApi.getCockpitProfitability(signal),
    flowApi.getCockpitModule("cashflow", signal),
    flowApi.getCockpitModule("expenses", signal),
  ]);
  const failures: string[] = [];
  if (profitability.status === "rejected") failures.push("盈利能力");
  if (cashflow.status === "rejected") failures.push("现金流");
  if (expenses.status === "rejected") failures.push("费用分析");
  return {
    profitability: profitability.status === "fulfilled" ? profitability.value as CockpitProfitabilityResponse : null,
    cashflow: cashflow.status === "fulfilled" ? cashflow.value as CockpitModuleResponse : null,
    expenses: expenses.status === "fulfilled" ? expenses.value as CockpitModuleResponse : null,
    failures,
  };
};

const defaultLoad = (
  filters: CockpitFilters,
  signal: AbortSignal,
): Promise<CockpitOverviewResponse> => flowApi.getCockpitOverview(filters, signal);

const defaultLoadFilterOptions = (signal: AbortSignal) => flowApi.getDashboard({}, signal);

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
  loadSupplement = defaultLoadSupplement,
  loadFilterOptions = defaultLoadFilterOptions,
  initialFilters = {},
}: {
  load?: (
    filters: CockpitFilters,
    signal: AbortSignal,
  ) => Promise<CockpitOverviewResponse>;
  initialFilters?: CockpitFilters;
  loadSupplement?: (signal: AbortSignal) => Promise<CockpitOverviewSupplements>;
  loadFilterOptions?: (signal: AbortSignal) => Promise<DashboardResponse>;
}) {
  const [filters, setFilters] = useState<CockpitFilters>(initialFilters);
  const [request, setRequest] = useState<CockpitRequestState>({ kind: "loading" });
  const [drill, setDrill] = useState<CockpitDrill | null>(null);
  const [supplements, setSupplements] = useState<CockpitOverviewSupplements | null>(null);
  const [supplementsLoading, setSupplementsLoading] = useState(true);
  const [filterDimensions, setFilterDimensions] = useState<DashboardResponse["filter_options"]["dimensions"]>([]);
  const [requestKey, setRequestKey] = useState(0);
  const serialized = useMemo(() => queryString(filters), [filters]);

  useEffect(() => {
    const controller = new AbortController();
    loadSupplement(controller.signal).then(
      (result) => {
        if (controller.signal.aborted) return;
        setSupplements(result);
        setSupplementsLoading(false);
      },
      () => {
        if (!controller.signal.aborted) {
          setSupplements({ profitability: null, cashflow: null, expenses: null, failures: ["披露补充"] });
          setSupplementsLoading(false);
        }
      },
    );
    return () => controller.abort();
  }, [loadSupplement]);

  useEffect(() => {
    const controller = new AbortController();
    loadFilterOptions(controller.signal).then(
      (dashboard) => { if (!controller.signal.aborted) setFilterDimensions(dashboard.filter_options.dimensions); },
      () => { if (!controller.signal.aborted) setFilterDimensions([]); },
    );
    return () => controller.abort();
  }, [loadFilterOptions]);

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

  useEffect(() => {
    const onPopState = () => {
      const params = new URLSearchParams(window.location.search);
      const next: CockpitFilters = {};
      for (const key of ["period_view", "organization_id", "customer_segment_id", "logistics_product_id", "region_id"] as const) {
        const value = params.get(key);
        if (!value) continue;
        if (key === "period_view") {
          if (value === "month" || value === "ytd") next.period_view = value;
        } else {
          Object.assign(next, { [key]: value });
        }
      }
      setRequest({ kind: "loading" });
      setFilters(next);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const changeFilters = useCallback((next: CockpitFilters) => {
    const query = queryString(next);
    window.history.pushState(null, "", query ? `?${query}` : window.location.pathname);
    setRequest({ kind: "loading" });
    setFilters(next);
  }, []);

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
          key={serialized}
          filters={filters}
          dimensions={filterDimensions}
          onChange={changeFilters}
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
        <CockpitFilterBar key={serialized} filters={filters} dimensions={filterDimensions} onChange={changeFilters} />
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
        <CockpitFilterBar key={serialized} filters={filters} dimensions={filterDimensions} onChange={changeFilters} />
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
      <header className="cockpit__head">
        <div className="cockpit__title-group">
          <p className="cockpit__eyebrow">FLOW / FINANCE INTELLIGENCE</p>
          <div className="cockpit__title-line">
            <h1>集团财务总览</h1>
            {overview.source_notice ? (
              <span
                className="cockpit__source-badge"
                data-testid="cockpit-source-notice"
                title={overview.source_notice}
                aria-label={`数据标记：${overview.source_notice}`}
              >
                {overview.source_notice.includes("演示") ? "演示数据" : "数据来源已标注"}
              </span>
            ) : null}
          </div>
          <p className="cockpit__deck">从财务视角，快速把握经营表现、关键驱动与待跟进事项。</p>
        </div>
        <p className="cockpit__meta">
          截至 {overview.context.as_of_month} · 快照 {overview.context.metric_snapshot_id?.slice(0, 8) ?? "—"} ·
          指标集 {overview.context.metric_definition_set_id?.slice(0, 8) ?? "—"}
        </p>
      </header>

      <CockpitFilterBar
        key={serialized}
        filters={filters}
        dimensions={filterDimensions}
        onChange={changeFilters}
      />
      {overview.data_status.freshness_status === "stale" || overview.state === "stale" ? (
        <p className="cockpit__stale-notice" role="status" data-testid="cockpit-stale-notice">
          数据快照已过期；当前显示最近一次已发布结果，数据截止 {overview.context.as_of_month}。
        </p>
      ) : null}

      <CockpitKpiGrid cards={overview.kpi_cards ?? []} trends={trendSeries} onDrill={setDrill} />
      <CockpitOverviewVisuals overview={overview} supplements={supplements} loading={supplementsLoading} />

      <CockpitConclusionBar
        text={overview.conclusion.text}
        findings={overview.conclusion.findings ?? []}
        tone={overview.conclusion.tone}
      />

      <div className="cockpit__closeout-grid">
        <ActionItemPanel
          fetchActionItems={() => flowApi.getCockpitActionItems()}
          createActionItem={(payload) => flowApi.createCockpitActionItem(payload)}
          findings={overview.conclusion.findings ?? []}
          snapshotId={overview.context.metric_snapshot_id ?? undefined}
          acknowledgeActionItem={(itemId) =>
            flowApi.acknowledgeCockpitActionItem(itemId)
          }
        />
        <CockpitOverviewSourcePanel overview={overview} supplements={supplements} />
      </div>

      {/* 批次 D：问数入口——导航至四问工作台（确定性检索引用 QA） */}
      <section aria-label="问数入口" className="ask-entry">
        <Link href="/analysis" className="ask-entry__link">
          问数 → 进入四问工作台
        </Link>
        <p className="ask-entry__note">
          基于冻结事实的确定性检索引用问答；LLM 通道另行裁决（D054）。
        </p>
      </section>

      <CockpitDrillDrawer drill={drill} onClose={() => setDrill(null)} />
    </div>
  );
}
