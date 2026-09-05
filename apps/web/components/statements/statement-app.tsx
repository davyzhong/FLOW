"use client";

// 报表分析：四表一注的图形化呈现。数据只来自 typed /api/v1/statements，
// 图形是同一冻结抽取值的投影（D043），本组件不做任何财务数字的重算修饰。
import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  FlowApiError,
  statementApi,
  type StatementReportDetail,
  type StatementReportList,
} from "../../lib/api/client";
import { WorkflowNav } from "../dashboard/workflow-nav";
import { DonutChart } from "./charts/donut-chart";
import { GroupedBarChart } from "./charts/grouped-bar-chart";
import { KpiCards } from "./charts/kpi-cards";
import { WaterfallChart } from "./charts/waterfall-chart";
import {
  buildAssetDonut,
  buildCapitalDonut,
  buildCashBridge,
  buildCashflowBars,
  buildIncomeWaterfall,
  buildKpis,
  columnLayout,
  formatRaw,
  getSection,
  toYi,
} from "./statement-view";
import "./statements.css";

type ListState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; reports: StatementReportList["reports"] };

type DetailState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; detail: StatementReportDetail };

function toMessage(error: unknown): string {
  if (error instanceof FlowApiError) {
    return `加载失败（${error.status} ${error.code}）`;
  }
  return error instanceof Error ? error.message : "未知错误";
}

function StatementTable({
  detail,
  statementType,
}: {
  detail: StatementReportDetail;
  statementType: string;
}) {
  const section = getSection(detail, statementType);
  if (!section) return null;
  const columns = columnLayout(section);
  return (
    <details className="stmt-section" open>
      <summary>
        {statementType}
        <small>{section.items.length} 行 · 单位 {detail.unit_note}</small>
      </summary>
      <div className="stmt-table-wrap">
        <table aria-label={statementType}>
          <thead>
            <tr>
              <th scope="col">项目</th>
              {columns.map((column) => (
                <th scope="col" key={column.key} className="is-num">
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.items.map((line) => (
              <tr key={`${line.sort_order}-${line.item_name}`}>
                <td>{line.item_name}</td>
                {columns.map((column) => {
                  const exact = line[column.key];
                  const numeric = toYi(exact);
                  return (
                    <td key={column.key} className="is-num" title={exact ?? undefined}>
                      {numeric === null ? "" : formatRaw(numeric)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

function ReportDetail({ detail }: { detail: StatementReportDetail }) {
  const kpis = buildKpis(detail);
  const waterfall = buildIncomeWaterfall(detail);
  const assetDonut = buildAssetDonut(detail);
  const capitalDonut = buildCapitalDonut(detail);
  const cashflow = buildCashflowBars(detail);
  const cashBridge = buildCashBridge(detail);
  return (
    <div className="stmt-detail">
      <header className="stmt-detail__header">
        <h2>
          {detail.company_name}
          <span className="stmt-meta">
            {detail.stock_code} · {detail.period_label} {detail.report_kind} · 单位 {detail.unit_note}
          </span>
        </h2>
        <p className="stmt-source">
          来源：<code>{detail.source_ref}</code>
          {detail.source_sha256 ? <code className="stmt-sha">SHA-256 {detail.source_sha256.slice(0, 12)}…</code> : null}
        </p>
      </header>
      {kpis.length ? <KpiCards items={kpis} /> : null}
      {waterfall ? (
        <section className="stmt-chart-card">
          <h3>利润形成瀑布（本期，亿元）</h3>
          <WaterfallChart
            items={waterfall}
            unitLabel="亿元"
            ariaLabel="利润形成瀑布图，从营业收入到净利润"
          />
        </section>
      ) : null}
      {assetDonut || capitalDonut ? (
        <div className="stmt-chart-row">
          {assetDonut ? (
            <section className="stmt-chart-card">
              <h3>资产构成（期末，亿元）</h3>
              <DonutChart items={assetDonut} unitLabel="亿元" ariaLabel="期末资产构成环形图" />
            </section>
          ) : null}
          {capitalDonut ? (
            <section className="stmt-chart-card">
              <h3>资本结构（期末，亿元）</h3>
              <DonutChart items={capitalDonut} unitLabel="亿元" ariaLabel="期末资本结构环形图" />
            </section>
          ) : null}
        </div>
      ) : null}
      {cashflow ? (
        <section className="stmt-chart-card">
          <h3>现金流量三活动净额（亿元）</h3>
          <GroupedBarChart
            items={cashflow}
            currentLabel="本期"
            priorLabel="上期"
            unitLabel="亿元"
            ariaLabel="现金流量三类活动净额柱状图，本期与上期对比"
          />
        </section>
      ) : null}
      {cashBridge ? (
        <section className="stmt-chart-card">
          <h3>现金桥：期初 → 期末（亿元）</h3>
          <WaterfallChart items={cashBridge} unitLabel="亿元" ariaLabel="期初到期末的现金变动桥" />
        </section>
      ) : null}
      <section className="stmt-tables" aria-label="四表原文">
        <h3>四表原文（抽取值）</h3>
        {detail.sections.map((section) => (
          <StatementTable key={section.statement_type} detail={detail} statementType={section.statement_type} />
        ))}
      </section>
    </div>
  );
}

export function StatementApp() {
  const [listState, setListState] = useState<ListState>({ kind: "loading" });
  const [detailState, setDetailState] = useState<DetailState>({ kind: "idle" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [requestKey, setRequestKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    statementApi
      .listReports(controller.signal)
      .then((reports) => setListState({ kind: "loaded", reports: reports.reports }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setListState({ kind: "error", message: toMessage(error) });
      });
    return () => controller.abort();
  }, [requestKey]);

  const activeId =
    listState.kind === "loaded" && listState.reports.length
      ? (selectedId ?? listState.reports[0].id)
      : null;

  useEffect(() => {
    if (!activeId) return;
    const controller = new AbortController();
    statementApi
      .getReport(activeId, controller.signal)
      .then((detail) => setDetailState({ kind: "loaded", detail }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setDetailState({ kind: "error", message: toMessage(error) });
      });
    return () => controller.abort();
  }, [activeId, requestKey]);

  const retry = useCallback(() => {
    setSelectedId(null);
    setDetailState({ kind: "idle" });
    setListState({ kind: "loading" });
    setRequestKey((key) => key + 1);
  }, []);

  const selectReport = useCallback((reportId: string) => {
    setSelectedId(reportId);
    setDetailState({ kind: "loading" });
  }, []);

  let body: ReactNode;
  if (listState.kind === "loading") {
    body = <p role="status" className="stmt-status">正在加载财报列表…</p>;
  } else if (listState.kind === "error") {
    body = (
      <div role="alert" className="stmt-status is-error">
        <p>{listState.message}</p>
        <button type="button" onClick={retry}>重试</button>
      </div>
    );
  } else if (listState.reports.length === 0) {
    body = (
      <div role="status" className="stmt-status">
        <p>尚无已导入的财报。请先运行 P5 抽取并执行 scripts/seed_statement_reports.py 导入。</p>
        <button type="button" onClick={retry}>刷新</button>
      </div>
    );
  } else {
    const currentId = activeId ?? listState.reports[0].id;
    body = (
      <>
        <nav className="stmt-report-tabs" aria-label="财报选择">
          {listState.reports.map((report) => (
            <button
              key={report.id}
              type="button"
              className={report.id === currentId ? "is-active" : undefined}
              aria-pressed={report.id === currentId}
              onClick={() => selectReport(report.id)}
            >
              <strong>{report.company_name}</strong>
              <span>
                {report.period_label} {report.report_kind}
              </span>
            </button>
          ))}
        </nav>
        {detailState.kind === "loading" ? (
          <p role="status" className="stmt-status">正在加载报表数据…</p>
        ) : detailState.kind === "error" ? (
          <div role="alert" className="stmt-status is-error">
            <p>{detailState.message}</p>
            <button type="button" onClick={retry}>重试</button>
          </div>
        ) : detailState.kind === "loaded" ? (
          <ReportDetail detail={detailState.detail} />
        ) : null}
      </>
    );
  }

  return (
    <div className="statements-layout">
      <WorkflowNav />
      <main className="stmt-main">
        <header className="stmt-page-header">
          <h1>报表分析</h1>
          <p>
            公开财报反向解析的图形化呈现（D041/D043）：同一抽取值的表格与图形投影，
            数字可溯源至披露原文，不在展示层重算。
          </p>
        </header>
        {body}
      </main>
    </div>
  );
}
