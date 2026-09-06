"use client";

// 分析与归因入口：列出全部 Finding 并携带完整身份（D036）进入证据优先工作台。
import { useEffect, useState } from "react";

import { findingApi, type FindingListItem } from "../../lib/api/client";
import "./investigations-index.css";

const STATUS_LABELS: Record<string, string> = {
  candidate: "候选",
  in_review: "复核中",
  approved: "已批准",
  rejected: "已拒绝",
};

function investigationHref(finding: FindingListItem): string {
  const params = new URLSearchParams();
  if (finding.batch_id) params.set("batch_id", finding.batch_id);
  if (finding.metric_snapshot_id) params.set("metric_snapshot_id", finding.metric_snapshot_id);
  if (finding.analysis_run_id) params.set("analysis_run_id", finding.analysis_run_id);
  const query = params.toString();
  return `/investigations/${finding.finding_id}${query ? `?${query}` : ""}`;
}

function formatImpact(value: string): string {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return value;
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(2)} 亿元`;
  if (Math.abs(amount) >= 10_000) return `${(amount / 10_000).toFixed(1)} 万元`;
  return `${amount.toFixed(2)} 元`;
}

export function InvestigationsIndex() {
  const [findings, setFindings] = useState<FindingListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    findingApi.list(controller.signal).then(
      (list) => setFindings(list.findings),
      (cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof Error ? cause.message : "加载失败");
      },
    );
    return () => controller.abort();
  }, []);

  return (
    <div className="investigations-index">
      <header>
        <h1>分析与归因</h1>
        <p>
          全部确定性 Finding 入口。选择一项进入证据优先调查工作台，身份（批次 / 指标快照 /
          分析运行）随链接交接，不会在调查中静默切换。
        </p>
      </header>

      {error ? (
        <p role="alert" className="investigations-index__error">
          {error}
        </p>
      ) : null}
      {findings === null && !error ? <p role="status">正在读取 Finding 列表…</p> : null}
      {findings !== null && findings.length === 0 ? (
        <p className="investigations-index__empty">
          当前没有 Finding：请先完成数据接入、指标计算与分析运行。
        </p>
      ) : null}

      {findings && findings.length > 0 ? (
        <table className="investigations-index__table">
          <thead>
            <tr>
              <th>发现</th>
              <th>类型</th>
              <th>影响金额</th>
              <th>对比口径</th>
              <th>状态</th>
              <th>评分</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((finding) => (
              <tr key={finding.finding_id}>
                <td>{finding.title}</td>
                <td><code>{finding.finding_type ?? "—"}</code></td>
                <td>{formatImpact(finding.impact_amount)}</td>
                <td>{finding.comparison_basis ?? "—"}</td>
                <td>
                  <span className={`investigations-index__status investigations-index__status--${finding.status}`}>
                    {STATUS_LABELS[finding.status] ?? finding.status}
                  </span>
                </td>
                <td>{finding.total_score ? Number(finding.total_score).toFixed(0) : "—"}</td>
                <td>
                  <a href={investigationHref(finding)}>进入调查</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
