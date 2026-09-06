"use client";

// 经营分析轨（D045）演示页：面向经营/业务管理者。
// 与财务分析轨共享同一已发布指标快照（数字同源），本页只做规模、结构与效率视角的
// 只读投影，不产生新的 Finding、不进入报告资格。
import { useCallback, useEffect, useState } from "react";

import { flowApi, type DashboardResponse } from "../../lib/api/client";
import { MarginMatrix } from "../dashboard/margin-matrix";
import { MetricGrid } from "../dashboard/metric-grid";
import { ProductPerformanceTable } from "../dashboard/product-performance-table";
import { TrendPanel } from "../dashboard/trend-panel";
import "./operations.css";

const OPS_METRICS = ["orders", "revenue", "revenue_per_order", "fulfillment_cost_rate"] as const;

type LoadState =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "empty"; message: string }
  | { kind: "loaded"; dashboard: DashboardResponse };

export function OperationsApp() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  const load = useCallback(() => {
    const controller = new AbortController();
    flowApi.getDashboard({}, controller.signal).then(
      (dashboard) => {
        if (controller.signal.aborted) return;
        if (dashboard.state === "empty") {
          setState({ kind: "empty", message: "当前没有已发布的经营数据，请先在数据层完成接入与发布。" });
        } else {
          setState({ kind: "loaded", dashboard });
        }
      },
      () => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      },
    );
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  return (
    <div className="operations-app">
      <header className="operations-header">
        <p className="operations-header__track">经营分析轨 · 演示（D045）</p>
        <h1>经营概览</h1>
        <p>
          面向经营/业务管理者的规模、结构与效率视角。数字与财务分析轨来自同一已发布指标快照，
          仅组织方式不同；本页为只读演示，不下钻证据、不生成报告。
        </p>
      </header>

      {state.kind === "loading" ? <p role="status">正在读取经营数据…</p> : null}
      {state.kind === "error" ? (
        <div role="alert" className="operations-state">
          <p>经营概览暂时无法加载</p>
          <button type="button" onClick={() => load()}>重试</button>
        </div>
      ) : null}
      {state.kind === "empty" ? <p className="operations-state">{state.message}</p> : null}

      {state.kind === "loaded" ? (
        <>
          <MetricGrid
            cards={state.dashboard.metric_cards.filter((card) =>
              (OPS_METRICS as readonly string[]).includes(card.metric_code),
            )}
          />

          <section className="operations-trend">
            <TrendPanel trends={state.dashboard.trends} />
          </section>

          <div className="operations-detail-grid">
            <ProductPerformanceTable table={state.dashboard.product_table} />
            <MarginMatrix matrix={state.dashboard.margin_matrix} />
          </div>
        </>
      ) : null}
    </div>
  );
}
