"use client";

import { useCallback, useEffect, useState } from "react";

import { FlowApiError, statementApi, type StatementReportList } from "../../lib/api/client";
import "./reports-center.css";

type SnapshotLine = {
  id: string;
  metric_snapshot_id: string;
  version: number;
  title: string;
  created_at: string | null;
};

type AttemptLine = {
  attempt_id: string;
  sequence: number;
  format: string;
  status: string;
  error_message: string | null;
  size_bytes: number | null;
  content_type: string | null;
  created_at: string | null;
  download_available: boolean;
  stored_sha256: string | null;
};

type FreezeCandidate = {
  metric_snapshot_id: string;
  batch_id: string;
  period_label: string | null;
  version: number;
  approved_findings: number;
  created_at: string | null;
};

const FORMATS = ["pptx", "xlsx", "html", "pdf"] as const;

async function fetchSnapshots(): Promise<SnapshotLine[]> {
  const response = await fetch("/api/v1/publishing/snapshots", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new FlowApiError(response.status, "upstream", "加载失败");
  return ((await response.json()) as { snapshots: SnapshotLine[] }).snapshots;
}

async function fetchFreezeCandidates(): Promise<FreezeCandidate[]> {
  const response = await fetch("/api/v1/publishing/freeze-candidates", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) return [];
  const body = (await response.json()) as { candidates?: FreezeCandidate[] };
  return body.candidates ?? [];
}

async function fetchAttempts(snapshotId: string): Promise<AttemptLine[]> {
  const response = await fetch(`/api/v1/publishing/snapshots/${snapshotId}/attempts`);
  if (!response.ok) return [];
  return ((await response.json()) as { attempts: AttemptLine[] }).attempts;
}

export function ReportsCenter() {
  const [snapshots, setSnapshots] = useState<SnapshotLine[]>([]);
  const [objectiveReports, setObjectiveReports] = useState<StatementReportList["reports"]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [metricSnapshotId, setMetricSnapshotId] = useState("");
  const [candidates, setCandidates] = useState<FreezeCandidate[]>([]);
  const [formats, setFormats] = useState<string[]>(["html"]);
  const [attempts, setAttempts] = useState<AttemptLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/v1/statements", { headers: { Accept: "application/json" } })
      .then((response) => (response.ok ? response.json() : { reports: [] }))
      .then((body: { reports?: StatementReportList["reports"] }) =>
        setObjectiveReports(body.reports ?? []),
      )
      .catch(() => setObjectiveReports([]));
    fetchSnapshots()
      .then((rows) => {
        if (cancelled) return;
        setSnapshots(rows);
        if (rows[0]) setSelected(rows[0].id);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    fetchFreezeCandidates()
      .then((rows) => {
        if (!cancelled) setCandidates(rows);
      })
      .catch(() => {
        if (!cancelled) setCandidates([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const snapshot = snapshots.find((row) => row.id === selected) ?? null;

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    fetchAttempts(selected)
      .then((rows) => {
        if (!cancelled) setAttempts(rows);
      })
      .catch(() => {
        if (!cancelled) setAttempts([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selected]);

  const refreshAttempts = useCallback(async () => {
    if (!selected) return;
    setAttempts(await fetchAttempts(selected));
  }, [selected]);

  const freeze = useCallback(async () => {
    setError(null);
    setBusy(true);
    try {
      const response = await fetch("/api/v1/publishing/snapshots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metric_snapshot_id: metricSnapshotId }),
      });
      if (!response.ok) {
        const body = (await response.json()) as { detail?: { message?: string } };
        throw new Error(body.detail?.message ?? "冻结失败");
      }
      const refreshed = await fetchSnapshots();
      setSnapshots(refreshed);
      if (refreshed[0]) setSelected(refreshed[0].id);
      setCandidates(await fetchFreezeCandidates());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "冻结失败");
    } finally {
      setBusy(false);
    }
  }, [metricSnapshotId]);

  const publish = useCallback(async () => {
    if (!selected) return;
    setError(null);
    setBusy(true);
    try {
      const response = await fetch(`/api/v1/publishing/snapshots/${selected}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ formats, actor: "finance.bp@example.com" }),
      });
      if (!response.ok) throw new Error("产物生成失败");
      await refreshAttempts();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "产物生成失败");
    } finally {
      setBusy(false);
    }
  }, [selected, formats, refreshAttempts]);

  const download = useCallback(async (attemptId: string, format: string) => {
    const response = await fetch(`/api/v1/publishing/attempts/${attemptId}/download`);
    if (!response.ok) {
      setError("下载不可用");
      return;
    }
    const disposition = response.headers.get("content-disposition") ?? "";
    const match = /filename="([^"]+)"/.exec(disposition);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = match?.[1] ?? `flow-report.${FORMATS.find((item) => item === format) ?? "bin"}`;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }, []);

  return (
    <section aria-label="报告中心" className="reports-center">
      <header className="reports-center__header">
        <h1>报告中心</h1>
      </header>

      {error ? (
        <p role="alert" className="reports-center__error">
          {error}
        </p>
      ) : null}

      <div className="reports-center__objective">
        <h2>客观财报分析报告（四表一注）</h2>
        <p className="reports-center__objective-note">
          基于公开财报反向解析的客观分析（D041/D043）：HTML 由冻结载荷渲染，数值与披露原文一致。
        </p>
        {objectiveReports.length === 0 ? (
          <p className="ml-muted">尚无已导入的公开财报。请先在数据接入导入或在 P5 抽取后运行种子脚本。</p>
        ) : (
          <ul className="reports-center__objective-list">
            {objectiveReports.map((report) => (
              <li key={report.id}>
                <a
                  href={statementApi.objectiveSnapshotHtmlUrl(report.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {report.company_name} · {report.period_label} {report.report_kind}
                  （行项目 {report.line_item_count}）
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="reports-center__freeze">
        <h2>冻结新报告快照</h2>
        <label>
          指标快照
          <select
            value={metricSnapshotId}
            onChange={(event) => setMetricSnapshotId(event.target.value)}
          >
            <option value="">选择已发布的指标快照…</option>
            {candidates.map((candidate) => (
              <option
                key={candidate.metric_snapshot_id}
                value={candidate.metric_snapshot_id}
                disabled={candidate.approved_findings === 0}
              >
                {candidate.period_label ?? "未知期间"} · 批次 {candidate.batch_id.slice(0, 8)} · v
                {candidate.version} · 已批准发现 {candidate.approved_findings}
                {candidate.approved_findings === 0 ? "（不可冻结）" : ""}
              </option>
            ))}
          </select>
        </label>
        <button type="button" disabled={busy || !metricSnapshotId} onClick={() => void freeze()}>
          冻结快照
        </button>
        <p className="reports-center__hint">
          冻结要求指标快照已发布且至少一个 finding 已批准；未批准时请先回到 Investigation 流程。
        </p>
      </div>

      {loading ? <p role="status">加载中…</p> : null}

      <div className="reports-center__snapshots">
        <h2>报告快照</h2>
        <ul aria-label="报告快照列表">
          {snapshots.map((row) => (
            <li key={row.id}>
              <label>
                <input
                  type="radio"
                  name="report-snapshot"
                  checked={selected === row.id}
                  onChange={() => setSelected(row.id)}
                />
                v{row.version} · {row.title} · {row.created_at?.slice(0, 10)}
              </label>
            </li>
          ))}
        </ul>
      </div>

      {snapshot ? (
        <div className="reports-center__publish">
          <h2>生成产物</h2>
          {FORMATS.map((format) => (
            <label key={format}>
              <input
                type="checkbox"
                checked={formats.includes(format)}
                onChange={(event) =>
                  setFormats((prev) =>
                    event.target.checked
                      ? [...prev, format]
                      : prev.filter((item) => item !== format),
                  )
                }
              />
              {format.toUpperCase()}
            </label>
          ))}
          <button type="button" disabled={busy || formats.length === 0} onClick={() => void publish()}>
            生成选中格式
          </button>

          <h3>产物历史（append-only）</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">格式</th>
                <th scope="col">状态</th>
                <th scope="col">大小</th>
                <th scope="col">操作</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((attempt) => (
                <tr key={attempt.attempt_id}>
                  <td>{attempt.sequence}</td>
                  <td>{attempt.format}</td>
                  <td>{attempt.status}</td>
                  <td>{attempt.size_bytes ?? "-"}</td>
                  <td>
                    {attempt.download_available ? (
                      <button type="button" onClick={() => void download(attempt.attempt_id, attempt.format)}>
                        下载
                      </button>
                    ) : attempt.status === "failed" ? (
                      <span>失败：{attempt.error_message?.slice(0, 60)}</span>
                    ) : (
                      <span>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

export default ReportsCenter;
