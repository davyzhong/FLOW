"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  statementApi,
  type OperationsOverview,
  type PublicOperatingPeriodList,
  type StatementReportList,
} from "../../lib/api/client";
import { EmptyGuide } from "../ui/empty-guide";
import { metricEntryHref, reportsSnapshotHref } from "../../lib/deep-links";
import "./operations-overview.css";

const DIRECTION_LABEL: Record<string, string> = {
  negative: "关注",
  warning: "提示复核",
};

const ASSURANCE_LABEL: Record<string, string> = {
  audited: "经审计",
  unaudited: "未经审计",
  management_disclosure: "管理层披露",
};

function themeUnavailableMessage(reason: string | null | undefined): string {
  switch (reason) {
    case "internal_data_required":
      return `待内部数据（${reason}）——当前周期尚未提供用户与渠道事实；完成授权和接入后启用。`;
    case "segment_disclosure_missing":
      return `公开报告未披露分部数据（${reason}）；收入结构暂不可计算，不从总体收入推算。`;
    case "segment_period_not_available":
      return `当前公司/期间没有可用的分部披露（${reason}）；不跨期间借用数据。`;
    case "statement_report_required":
      return `该主题需要完整财务报表（${reason}）；当前公开披露范围不含完整报表。`;
    default:
      return `当前主题不可用（原因码：${reason ?? "unspecified"}）；缺失不补造。`;
  }
}

const PERCENT_METRICS = new Set([
  "gross_margin",
  "net_margin",
  "debt_asset_ratio",
  "revenue_growth",
  "net_profit_growth",
  "operating_profit_growth",
  "revenue_yoy",
  "net_profit_yoy",
  "segment_revenue_yoy",
  "adjusted_net_profit_margin",
  "adjusted_ebitda_margin",
  "business_line_share.china_logistics",
  "business_line_share.international_logistics",
  "business_line_share.technology_and_other_services",
  "dupont_three_factor",
]);

const MULTIPLE_METRICS = new Set([
  "current_ratio",
  "ocf_to_net_profit",
  "inventory_turnover",
  "ar_turnover",
  "ap_turnover",
  "current_asset_turnover",
]);

const PRESERVE_DISCLOSURE_PRECISION = new Set([
  "international_parcels",
  "china_orders_fulfilled",
  "adjusted_net_profit",
  "adjusted_ebitda",
]);

function formatMetricValue(entryId: string, rawValue: string): string {
  // 经营事实可能带有百万件/百万元等单位，但当前 typed payload 未向前端提供 unit；
  // 未注册单位的原始披露值保持原样，避免四舍五入改变披露精度或造成单位误读。
  if (PRESERVE_DISCLOSURE_PRECISION.has(entryId)) return rawValue;
  const value = Number(rawValue);
  if (!Number.isFinite(value)) return rawValue;
  const isRatio = PERCENT_METRICS.has(entryId) || MULTIPLE_METRICS.has(entryId) || entryId === "dso_days";
  const formatted = new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: isRatio ? 2 : 0,
    maximumFractionDigits: 2,
  }).format(PERCENT_METRICS.has(entryId) ? value * 100 : value);
  if (PERCENT_METRICS.has(entryId)) return `${formatted}%`;
  if (MULTIPLE_METRICS.has(entryId)) {
    return `${formatted}${entryId === "current_ratio" || entryId === "ocf_to_net_profit" ? " 倍" : " 次"}`;
  }
  if (entryId === "dso_days") return `${formatted} 天`;
  return formatted;
}

type LoadState =
  | { status: "idle" }
  | { status: "ready" }
  | { status: "error"; message: string };

type FreezeInfo = {
  snapshot_id: string;
  version: number;
  payload_hash: string;
};

type AnalysisContext =
  | { kind: "report"; reportId: string }
  | { kind: "public"; stockCode: string; periodLabel: string };

function parseAnalysisContext(value: string): AnalysisContext | null {
  const [kind, first, second] = value.split(":");
  if (kind === "report" && first && !second) {
    return { kind, reportId: first };
  }
  if (kind === "public" && first && second) {
    return { kind, stockCode: first, periodLabel: second };
  }
  return null;
}

export function OperationsOverviewApp({
  initialReportId = null,
}: {
  /** ?report={statement_report_id} 深链：命中时初始选中；不存在时显式提示并回退默认 */
  initialReportId?: string | null;
}) {
  const [reports, setReports] = useState<StatementReportList["reports"]>([]);
  const [publicPeriods, setPublicPeriods] = useState<
    PublicOperatingPeriodList["periods"]
  >([]);
  const [selectedContext, setSelectedContext] = useState<string>("");
  const [reportMiss, setReportMiss] = useState<string | null>(null);
  const [overview, setOverview] = useState<OperationsOverview | null>(null);
  const [freezeInfo, setFreezeInfo] = useState<FreezeInfo | null>(null);
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    Promise.allSettled([
      statementApi.listReports(controller.signal),
      statementApi.listPublicOperatingPeriods(controller.signal),
    ]).then(([reportResult, publicResult]) => {
      if (cancelled) return;
      const nextReports = reportResult.status === "fulfilled" ? reportResult.value.reports : [];
      const nextPublicPeriods =
        publicResult.status === "fulfilled" ? publicResult.value.periods : [];
      setReports(nextReports);
      setPublicPeriods(nextPublicPeriods);
      // 深链优先：?report= 命中则选中对应财报；未命中显式提示并回退默认上下文
      if (initialReportId) {
        if (nextReports.some((report) => report.id === initialReportId)) {
          setSelectedContext(`report:${initialReportId}`);
          return;
        }
        setReportMiss(initialReportId);
      }
      if (nextReports.length > 0) {
        setSelectedContext((current) => current || `report:${nextReports[0].id}`);
      } else if (nextPublicPeriods.length > 0) {
        const first = nextPublicPeriods[0];
        setSelectedContext(
          (current) => current || `public:${first.stock_code}:${first.period_label}`,
        );
      } else {
        const error =
          reportResult.status === "rejected" ? reportResult.reason : publicResult.status === "rejected" ? publicResult.reason : null;
        if (cancelled) return;
        setState(error
          ? {
              status: "error",
              message: error instanceof FlowApiError ? error.message : "加载分析数据失败",
            }
          : { status: "ready" });
      }
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [initialReportId]);

  useEffect(() => {
    const context = parseAnalysisContext(selectedContext);
    if (!context) return;
    let cancelled = false;
    const controller = new AbortController();
    const request =
      context.kind === "report"
        ? statementApi.fetchOperationsOverview(context.reportId, controller.signal)
        : statementApi.fetchPublicOperatingOverview(
            context.stockCode,
            context.periodLabel,
            controller.signal,
          );
    request
      .then((body) => {
        if (cancelled) return;
        setOverview(body);
        setFreezeInfo(null);
        setState({ status: "ready" });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message: error instanceof FlowApiError ? error.message : "加载经营概览失败",
        });
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [selectedContext]);

  const context = parseAnalysisContext(selectedContext);
  const selectedReportId = context?.kind === "report" ? context.reportId : "";
  const selectedPublicPeriod =
    context?.kind === "public"
      ? publicPeriods.find(
          (period) =>
            period.stock_code === context.stockCode &&
            period.period_label === context.periodLabel,
        )
      : undefined;

  const freeze = useCallback(async () => {
    if (!selectedReportId) return;
    setBusy(true);
    try {
      const result = await statementApi.freezeOperationsOverview(selectedReportId);
      setFreezeInfo({
        snapshot_id: result.snapshot_id,
        version: result.version,
        payload_hash: result.payload_hash,
      });
    } catch (error: unknown) {
      setState({
        status: "error",
        message: error instanceof FlowApiError ? error.message : "冻结失败",
      });
    } finally {
      setBusy(false);
    }
  }, [selectedReportId]);

  return (
    <section aria-labelledby="operations-heading" className="ops-overview">
      <h1 id="operations-heading">经营分析概览</h1>
      <p className="ops-overview__intro">
        六主题结果层概览（L1 财报口径）；内部数据主题如实标注待授权，缺失不补造。
      </p>

      {state.status === "idle" ? (
        <p role="status" className="ops-overview__loading">
          正在读取经营分析概览…
        </p>
      ) : null}
      <div className="ops-overview__controls">
        <div className="flow-field">
          <label htmlFor="operations-context">分析数据与期间</label>
          <select
          id="operations-context"
          value={selectedContext}
          onChange={(event) => {
            setSelectedContext(event.target.value);
            setReportMiss(null);
          }}
        >
          {reports.length === 0 && publicPeriods.length === 0 ? (
            <option value="">（暂无可用分析数据）</option>
          ) : null}
          {reports.length > 0 ? (
            <optgroup label="完整财报">
              {reports.map((report) => (
                <option key={report.id} value={`report:${report.id}`}>
                  {report.company_name} · {report.period_label} · 完整财报
                </option>
              ))}
            </optgroup>
          ) : null}
          {publicPeriods.length > 0 ? (
            <optgroup label="公开经营披露">
              {publicPeriods.map((period) => (
                <option
                  key={`${period.stock_code}:${period.period_label}`}
                  value={`public:${period.stock_code}:${period.period_label}`}
                >
                  {period.company_name} · {period.period_label} · 公开经营披露
                  {period.is_stub ? "（未经审计）" : ""}
                </option>
              ))}
            </optgroup>
          ) : null}
          </select>
        </div>
        {selectedReportId ? (
          <>
            <button type="button" className="flow-btn flow-btn--primary" disabled={busy} onClick={freeze}>
              冻结概览
            </button>
            {overview ? (
              <>
                <a
                  className="flow-btn"
                  href={statementApi.operationsOverviewHtmlUrl(selectedReportId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  查看 HTML 报告
                </a>
                <a
                  className="flow-btn"
                  href={statementApi.operationsOverviewPdfUrl(selectedReportId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  下载 PDF
                </a>
                <a className="flow-btn" href={statementApi.operationsOverviewXlsxUrl(selectedReportId)}>
                  下载 Excel
                </a>
                <a className="flow-btn" href={statementApi.operationsOverviewPptxUrl(selectedReportId)}>
                  下载 PPT
                </a>
              </>
            ) : null}
          </>
        ) : null}
      </div>

      {selectedPublicPeriod ? (
        <p className="ops-overview__context-note">
          公开经营披露 · {ASSURANCE_LABEL[selectedPublicPeriod.assurance] ?? selectedPublicPeriod.assurance}
          ；该期间没有完整财报，当前仅提供可追溯的只读经营事实，不支持冻结与报告导出。
        </p>
      ) : null}

      {reportMiss ? (
        <p role="status" className="ops-overview__context-note">
          未找到财报「{reportMiss}」（report 参数不存在或已下线），已显示第一份可用分析数据。
        </p>
      ) : null}

      {state.status === "error" ? (
        <p role="alert" className="ops-overview__error flow-error">
          {state.message}
        </p>
      ) : null}

      {state.status === "ready" && reports.length === 0 && publicPeriods.length === 0 ? (
        <EmptyGuide
          kind="no-data"
          title="暂无可用经营分析数据"
          reason="导入完整财报或等待公开经营披露数据接入后，才能生成当前期间的经营分析。"
          actions={[
            { href: "/data", label: "前往数据接入" },
            { href: "/public", label: "查看公开经营分析" },
          ]}
        />
      ) : null}

      {freezeInfo ? (
        <p role="status" className="ops-overview__freeze">
          已冻结：版本 {freezeInfo.version} · 快照{" "}
          <Link href={reportsSnapshotHref(freezeInfo.snapshot_id)} title="在报告中心查看该快照">
            {freezeInfo.snapshot_id}
          </Link>{" "}
          · 指纹 {freezeInfo.payload_hash.slice(0, 16)}…
        </p>
      ) : null}

      {overview ? (
        <>
          {overview.management_watch.length > 0 ? (
            <>
              <h2>管理关注（≤3 条，提示复核）</h2>
              <ul className="ops-overview__watch" aria-label="管理关注">
                {overview.management_watch.map((item) => (
                  <li key={item.code} data-direction={item.direction}>
                    <span className="ops-overview__tag">
                      {DIRECTION_LABEL[item.direction] ?? item.direction}
                    </span>
                    {item.metric_code ? (
                      <a
                        href={`/metric-library?focus=${encodeURIComponent(item.metric_code)}`}
                        className="ops-overview__watch-link"
                      >
                        {item.message}（查看指标 →）
                      </a>
                    ) : (
                      item.message
                    )}
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          <h2>六主题概览</h2>
          <div className="ops-overview__themes">
            {overview.themes.map((theme) => (
              <section
                key={theme.theme_id}
                aria-labelledby={`ops-theme-${theme.theme_id}`}
                className="ops-overview__theme"
                data-status={theme.status}
              >
                <h3 id={`ops-theme-${theme.theme_id}`}>{theme.name}</h3>
                {theme.status === "not_applicable" ? (
                  <p className="ops-overview__muted">
                    {themeUnavailableMessage(theme.reason)}
                  </p>
                ) : (
                  <ul>
                    {theme.metrics.map((metric) => (
                      <li key={metric.entry_id}>
                        <Link
                          className="ops-overview__metric-name"
                          href={metricEntryHref(metric.entry_id)}
                          title="在指标库中查看口径定义"
                        >
                          {metric.name}
                        </Link>
                        {metric.status === "computed" ? (
                          <span className="ops-overview__metric-value">
                            <strong title={`精确值：${metric.value}`}>
                              {formatMetricValue(metric.entry_id, metric.value ?? "")}
                            </strong>
                            {metric.basis ? (
                              <small> 基准：{metric.basis}</small>
                            ) : null}
                            {metric.caliber_note ? (
                              <small className="ops-overview__caliber">
                                {" "}
                                口径：{metric.caliber_note}
                              </small>
                            ) : null}
                            {metric.source === "operating_fact" ? (
                              <small className="ops-overview__evidence">
                                {metric.period_label} ·{" "}
                                {ASSURANCE_LABEL[metric.assurance] ?? metric.assurance}
                                <br />
                                来源：{metric.source_ref}
                                {metric.source_page ? ` · 第 ${metric.source_page} 页` : ""}
                                {metric.source_sha256
                                  ? ` · ${metric.source_sha256.slice(0, 16)}…`
                                  : ""}
                              </small>
                            ) : null}
                          </span>
                        ) : (
                          <span className="ops-overview__muted">
                            暂不可算（{metric.reason}）
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>

          <p className="ops-overview__scope">
            范围说明：本概览只承载客观事实与可复算的确定性信号；原因推断与行动建议
            不在客观报告范围（主观内容需证据门槛）。
          </p>
        </>
      ) : null}
    </section>
  );
}
