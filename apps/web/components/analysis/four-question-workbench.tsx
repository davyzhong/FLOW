"use client";

import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  statementApi,
  type StatementReportList,
  type WorkbenchResponse,
} from "../../lib/api/client";
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

export function FourQuestionWorkbench() {
  const [reports, setReports] = useState<StatementReportList["reports"]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [workbench, setWorkbench] = useState<WorkbenchResponse | null>(null);
  const [state, setState] = useState<LoadState>({ status: "idle" });

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

  const loadWorkbench = useCallback((reportId: string) => {
    if (!reportId) return;
    setState({ status: "loading" });
    statementApi
      .fetchWorkbench(reportId)
      .then((body) => {
        setWorkbench(body);
        setState({ status: "ready" });
      })
      .catch((error: unknown) => {
        setState({
          status: "error",
          message: error instanceof FlowApiError ? error.message : "加载工作台失败",
        });
      });
  }, []);

  useEffect(() => {
    loadWorkbench(selectedReportId);
  }, [selectedReportId, loadWorkbench]);

  return (
    <section aria-labelledby="workbench-heading" className="workbench">
      <h1 id="workbench-heading">四问分析工作台</h1>
      <p className="workbench__intro">
        增长、盈利、资本、现金四问统领；指标缺失时给出解释性状态，不编造数值。
      </p>

      <div className="workbench__controls">
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
        <p role="alert" className="workbench__error">
          {state.message}
        </p>
      ) : null}
      {state.status === "loading" ? <p aria-live="polite">加载中…</p> : null}

      {workbench ? (
        <>
          <p className="workbench__identity">
            {workbench.report.company_name} · {workbench.report.period_label} ·{" "}
            {workbench.report.unit_note}
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
                      <span className="workbench__metric-code">{metric.metric_code}</span>
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
