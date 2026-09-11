"use client";

import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  statementApi,
  type OperationsOverview,
  type PublicOperatingPeriodList,
  type StatementReportList,
} from "../../lib/api/client";
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

const THEME_NOTE: Record<string, string> = {
  revenue_structure: "分部/产品线披露接入后启用（缺失不补造）",
  users_channels: "内部运营数据授权后启用",
};

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

export function OperationsOverviewApp() {
  const [reports, setReports] = useState<StatementReportList["reports"]>([]);
  const [publicPeriods, setPublicPeriods] = useState<
    PublicOperatingPeriodList["periods"]
  >([]);
  const [selectedContext, setSelectedContext] = useState<string>("");
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
        setState({
          status: "error",
          message: error instanceof FlowApiError ? error.message : "加载财报列表失败",
        });
      }
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

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

      <div className="ops-overview__controls">
        <label htmlFor="operations-context">分析数据与期间</label>
        <select
          id="operations-context"
          value={selectedContext}
          onChange={(event) => setSelectedContext(event.target.value)}
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
        {selectedReportId ? (
          <>
            <button type="button" disabled={busy} onClick={freeze}>
              冻结概览
            </button>
            {overview ? (
              <>
                <a
                  href={statementApi.operationsOverviewHtmlUrl(selectedReportId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  查看 HTML 报告
                </a>
                <a
                  href={statementApi.operationsOverviewPdfUrl(selectedReportId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  下载 PDF
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

      {state.status === "error" ? (
        <p role="alert" className="ops-overview__error">
          {state.message}
        </p>
      ) : null}

      {freezeInfo ? (
        <p role="status" className="ops-overview__freeze">
          已冻结：版本 {freezeInfo.version} · 快照 {freezeInfo.snapshot_id} · 指纹{" "}
          {freezeInfo.payload_hash.slice(0, 16)}…
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
                    {item.message}
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
                    待内部数据（{theme.reason}）——披露缺失与内部数据缺口如实标注，
                    不推测填补。
                    {THEME_NOTE[theme.theme_id]
                      ? ` ${THEME_NOTE[theme.theme_id]}。`
                      : null}
                  </p>
                ) : (
                  <ul>
                    {theme.metrics.map((metric) => (
                      <li key={metric.entry_id}>
                        <span className="ops-overview__metric-name">{metric.name}</span>
                        {metric.status === "computed" ? (
                          <span className="ops-overview__metric-value">
                            <strong>{metric.value}</strong>
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
