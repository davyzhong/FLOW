"use client";

// 报表分析：四表一注的图形化呈现。数据只来自 typed /api/v1/statements，
// 图形是同一冻结抽取值的投影（D043），本组件不做任何财务数字的重算修饰。
// 视觉走报告风：hero（红顶 + kicker + 大标题）+ KPI 卡带 + verdict 条。
// 注意：导航由 AppShell 统一提供（page.tsx 层），本组件不再重复渲染。
import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  FlowApiError,
  statementApi,
  type StatementReportDetail,
  type StatementReportList,
} from "../../lib/api/client";
import type { ColumnDef } from "@tanstack/react-table";
import { FlowDataTable } from "../ui/flow-data-table";
import { ProvenanceBadge } from "../ui/provenance-badge";
import type { StatementLine as StatementLineResponse } from "../../lib/api/client";
import { ReviewPanel } from "./review-panel";
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
  yiScale,
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
  const scale = yiScale(detail.unit_note);

  // F-DataTable 迁移：列定义含溯源卡列（page_number/page_anchor 数据来自
  // 迁移 0029，值列保持亿元换算与精确原值悬停）。
  const columnDefs: ColumnDef<StatementLineResponse, unknown>[] = [
    {
      accessorKey: "item_name",
      header: "项目",
      meta: { label: "项目" },
      cell: (info) => <span>{info.getValue<string>()}</span>,
    },
    ...columns.map(
      (column): ColumnDef<StatementLineResponse, unknown> => ({
        accessorKey: column.key,
        header: column.label,
        meta: { label: column.label },
        cell: (info) => {
          const exact = info.getValue<string | null>();
          const numeric = toYi(exact, scale);
          return (
            <span className="block text-right tabular-nums" title={exact ?? undefined}>
              {numeric === null ? "" : formatRaw(numeric)}
            </span>
          );
        },
      }),
    ),
    {
      id: "provenance",
      header: "页",
      enableSorting: false,
      meta: { label: "页" },
      cell: (info) => {
        const line = info.row.original;
        return (
          <ProvenanceBadge
            page={line.page_number ?? null}
            anchor={line.page_anchor ?? null}
            sourceRef={detail.source_ref}
          />
        );
      },
    },
  ];

  return (
    <details className="stmt-section" open>
      <summary>
        {statementType}
        <small>
          {section.items.length} 行 · 表中数值为亿元（披露单位 {detail.unit_note}，悬停查看精确原值）
        </small>
      </summary>
      <div className="stmt-table-wrap">
        <div role="region" aria-label={statementType}>
          <FlowDataTable
            columns={columnDefs}
            data={section.items}
            getRowId={(line) => `${line.sort_order}-${line.item_name}`}
            dense
            pageSize={50}
          />
        </div>
      </div>
    </details>
  );
}

function ReportDetail({
  detail,
  onChanged,
}: {
  detail: StatementReportDetail;
  onChanged: () => void;
}) {
  const kpis = buildKpis(detail);
  const waterfall = buildIncomeWaterfall(detail);
  const assetDonut = buildAssetDonut(detail);
  const capitalDonut = buildCapitalDonut(detail);
  const cashflow = buildCashflowBars(detail);
  const cashBridge = buildCashBridge(detail);
  // 自动拼装一条本报告速览（红竖线结论条）：只标维度，不复述 KPI 数值（避免与卡片重复）
  const hasIncome = kpis.some((k) => k.label === "营业总收入" || k.label === "营业收入" || k.label === "收入");
  const hasProfit = kpis.some((k) => k.label === "归母净利润" || k.label === "净利润");
  const hasOcf = kpis.some((k) => k.label === "经营现金流" || k.label === "经营活动产生的现金流量净额");
  const summary = [
    hasIncome ? "收入规模" : null,
    hasProfit ? "盈利水平" : null,
    hasOcf ? "经营现金流" : null,
  ].filter(Boolean);
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
      {summary.length > 0 ? (
        <div className="stmt-verdict" role="note">
          <b>本报告速览：</b>
          已抽取 <b>{summary.join("、")}</b> {summary.length} 个核心维度（见上方 KPI 卡带），
          利润瀑布 / 资产构成 / 资本结构 / 现金流活动以同一抽取值图形化呈现。
          详细勾稽与四表原文见下方表格，所有数值均可悬停查看精确原值。
        </div>
      ) : null}
      <section className="stmt-tables" aria-label="四表原文">
        <h3>四表原文（抽取值）</h3>
        {detail.sections.map((section) => (
          <StatementTable key={section.statement_type} detail={detail} statementType={section.statement_type} />
        ))}
      </section>
      <ReviewPanel detail={detail} onChanged={onChanged} />
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
          <ReportDetail
            detail={detailState.detail}
            onChanged={() => setRequestKey((key) => key + 1)}
          />
        ) : null}
      </>
    );
  }

  return (
    <div className="statements-app">
      <header className="stmt-hero">
        <div className="stmt-hero__kicker">报表分析 · 数据驱动决策 ｜ 财务创造价值</div>
        <h1 className="stmt-hero__title">
          公开财报<em>图形化</em>分析
        </h1>
        <p className="stmt-hero__lede">
          公开财报反向解析的图形化呈现（D041/D043）：同一抽取值的表格与图形投影，
          数字可溯源至披露原文，不在展示层重算。来源标注 + SHA-256 摘要，保证每一次展示都对应到原 PDF。
        </p>
      </header>
      {body}
    </div>
  );
}
