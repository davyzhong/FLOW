"use client";

import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  statementApi,
  type OperationsOverview,
  type StatementReportList,
} from "../../lib/api/client";
import "./operations-overview.css";

const DIRECTION_LABEL: Record<string, string> = {
  negative: "关注",
  warning: "提示复核",
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

export function OperationsOverviewApp() {
  const [reports, setReports] = useState<StatementReportList["reports"]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [overview, setOverview] = useState<OperationsOverview | null>(null);
  const [freezeInfo, setFreezeInfo] = useState<FreezeInfo | null>(null);
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    statementApi
      .listReports()
      .then((list) => {
        if (cancelled) return;
        setReports(list.reports);
        if (list.reports.length > 0) {
          setSelectedReportId((current) => current || list.reports[0].id);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message: error instanceof FlowApiError ? error.message : "加载财报列表失败",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedReportId) return;
    let cancelled = false;
    statementApi
      .fetchOperationsOverview(selectedReportId)
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
    };
  }, [selectedReportId]);

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
        <label htmlFor="operations-report">选择财报</label>
        <select
          id="operations-report"
          value={selectedReportId}
          onChange={(event) => setSelectedReportId(event.target.value)}
        >
          {reports.length === 0 ? <option value="">（暂无可选财报）</option> : null}
          {reports.map((report) => (
            <option key={report.id} value={report.id}>
              {report.company_name} · {report.period_label}
            </option>
          ))}
        </select>
        <button type="button" disabled={busy || !selectedReportId} onClick={freeze}>
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
      </div>

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
