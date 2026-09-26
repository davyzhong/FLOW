"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  analyticsApi,
  FlowApiError,
  statementApi,
  type AnalysisRunDetail,
  type StatementReportList,
  type WorkbenchResponse,
} from "../../lib/api/client";
import { metricFocusHref, reportsSnapshotHref, statementReportHref } from "../../lib/deep-links";
import "./four-question-workbench.css";

const DIRECTION_LABEL: Record<string, string> = {
  negative: "关注",
  warning: "提示复核",
};

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready" }
  | { status: "error"; message: string };

export function FourQuestionWorkbench({
  initialRunId = null,
}: {
  /** ?run_id={analysis_run_id}：定位分析运行身份（批次二 §3.2，经只读详情端点投影） */
  initialRunId?: string | null;
}) {
  const [reports, setReports] = useState<StatementReportList["reports"]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [workbench, setWorkbench] = useState<WorkbenchResponse | null>(null);
  const [state, setState] = useState<LoadState>({ status: "idle" });
  // run_id 深链解析结果按请求 id keyed 存储，loading 态渲染期纯派生（lint set-state-in-effect）
  const [runResult, setRunResult] = useState<
    | { id: string; kind: "found"; detail: AnalysisRunDetail }
    | { id: string; kind: "missing" }
    | null
  >(null);

  useEffect(() => {
    if (!initialRunId) return;
    let cancelled = false;
    analyticsApi.getAnalysisRun(initialRunId).then(
      (detail) => {
        if (!cancelled) setRunResult({ id: initialRunId, kind: "found", detail });
      },
      () => {
        if (!cancelled) setRunResult({ id: initialRunId, kind: "missing" });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [initialRunId]);

  const runDetail =
    initialRunId === null
      ? null
      : runResult && runResult.id === initialRunId
        ? runResult
        : ({ kind: "loading" } as const);

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
      .fetchWorkbench(selectedReportId)
      .then((body) => {
        if (cancelled) return;
        setWorkbench(body);
        setState({ status: "ready" });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message: error instanceof FlowApiError ? error.message : "加载工作台失败",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [selectedReportId]);

  const pending =
    state.status !== "error" &&
    selectedReportId !== "" &&
    (workbench === null || workbench.report.report_id !== selectedReportId);

  return (
    <section aria-labelledby="workbench-heading" className="workbench">
      <h1 id="workbench-heading">四问分析工作台</h1>
      <p className="workbench__intro">
        增长、盈利、资本、现金四问统领；指标缺失时给出解释性状态，不编造数值。
      </p>

      {runDetail?.kind === "found" ? (
        <section
          className="workbench__run"
          aria-label="分析运行身份"
          data-testid="analysis-run-detail"
        >
          <h2>分析运行定位</h2>
          <dl>
            <div>
              <dt>运行 ID</dt>
              <dd>{runDetail.detail.id}</dd>
            </div>
            <div>
              <dt>状态</dt>
              <dd>{runDetail.detail.status}</dd>
            </div>
            <div>
              <dt>策略集</dt>
              <dd>{runDetail.detail.policy_id}</dd>
            </div>
            <div>
              <dt>引擎</dt>
              <dd>{runDetail.detail.engine_version}</dd>
            </div>
            <div>
              <dt>指纹</dt>
              <dd title={runDetail.detail.fingerprint}>
                {runDetail.detail.fingerprint.slice(0, 12)}…
              </dd>
            </div>
            <div>
              <dt>所属指标快照</dt>
              <dd>
                <Link
                  href={reportsSnapshotHref(runDetail.detail.metric_snapshot_id)}
                  title="在报告中心查看该指标快照"
                >
                  {runDetail.detail.metric_snapshot_id}
                </Link>
              </dd>
            </div>
          </dl>
        </section>
      ) : null}
      {runDetail?.kind === "missing" ? (
        <p role="status" className="workbench__hint">
          未找到分析运行「{initialRunId}」（run_id 参数不存在或已下线），已显示默认工作台。
        </p>
      ) : null}

      <div className="workbench__controls flow-field">
        <label htmlFor="workbench-report">选择财报</label>
        <select
          id="workbench-report"
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
      </div>

      {state.status === "error" ? (
        <p role="alert" className="workbench__error flow-error">
          {state.message}
        </p>
      ) : null}
      {pending ? <p role="status" aria-live="polite">加载中…</p> : null}

      {workbench ? (
        <>
          <p className="workbench__identity">
            <Link href={statementReportHref(workbench.report.report_id)} title="在报表分析中查看该财报">
              {workbench.report.company_name} · {workbench.report.period_label} ·{" "}
              {workbench.report.unit_note}
            </Link>
          </p>

          <h2>管理关注（≤3 条，提示复核）</h2>
          {workbench.management_watch.length === 0 ? (
            <p className="workbench__muted">本期无确定性提示信号。</p>
          ) : (
            <ul className="workbench__watch" aria-label="管理关注">
              {workbench.management_watch.map((item) => (
                <li key={item.code} data-direction={item.direction}>
                  <span className="workbench__watch-direction">
                    {DIRECTION_LABEL[item.direction] ?? item.direction}
                  </span>
                  {item.message}
                </li>
              ))}
            </ul>
          )}

          <h2>四问指标</h2>
          <div className="workbench__questions">
            {workbench.questions.map((question) => (
              <section
                key={question.key}
                aria-labelledby={`question-${question.key}`}
                className="workbench__question"
              >
                <h3 id={`question-${question.key}`}>{question.name}</h3>
                <ul>
                  {question.metrics.map((metric) => (
                    <li key={metric.metric_code}>
                      <Link
                        className="workbench__metric-code"
                        href={metricFocusHref(metric.metric_code)}
                        title="在指标库中查看口径定义"
                      >
                        {metric.metric_code}
                      </Link>
                      {metric.available ? (
                        <strong>{metric.value}</strong>
                      ) : (
                        <span className="workbench__muted">暂不可算（缺披露事实）</span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
