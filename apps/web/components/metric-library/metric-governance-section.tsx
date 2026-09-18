"use client";

import { useCallback, useEffect, useState } from "react";

import {
  metricLibraryApi,
  type MetricGovernanceEventLine,
  type MetricLibraryEntry,
} from "../../lib/api/client";

function GovernanceSection({ metrics }: { metrics: MetricLibraryEntry[] }) {
  const [events, setEvents] = useState<MetricGovernanceEventLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // entry_id 是库内唯一键；metric_code 跨域可重复（如 general/logistics 各有一条 gross_margin）
  const [entryId, setEntryId] = useState(metrics[0]?.entry_id ?? "");
  const [changesText, setChangesText] = useState("{}");
  const [reason, setReason] = useState("");

  const refreshEvents = useCallback(() => {
    const controller = new AbortController();
    metricLibraryApi
      .listEvents(undefined, controller.signal)
      .then((list) => setEvents([...list.events]))
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof Error ? cause.message : "加载失败");
      });
    return controller;
  }, []);

  useEffect(() => {
    const controller = refreshEvents();
    return () => controller.abort();
  }, [refreshEvents]);

  const selected = metrics.find((m) => m.entry_id === entryId);

  const runAction = async (kind: "draft" | "activate" | "retire") => {
    setActionError(null);
    setNotice(null);
    if (!selected?.entry_id) {
      setActionError("该指标尚无库内条目（请先导入指标库）。");
      return;
    }
    if (!reason.trim()) {
      setActionError("理由为必填（审计要求）。操作者取自当前登录身份。");
      return;
    }
    let changes: Record<string, unknown> | null = null;
    if (kind === "draft") {
      try {
        const parsed: unknown = JSON.parse(changesText);
        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("not an object");
        }
        changes = parsed as Record<string, unknown>;
      } catch {
        setActionError("变更内容必须是合法的 JSON 对象，例如 {\"benchmark\": \"…\"}。");
        return;
      }
    }
    setBusy(true);
    try {
      const input = { reason: reason.trim() };
      if (kind === "draft") {
        await metricLibraryApi.draftChange(selected.entry_id, { ...input, changes: changes! });
        setNotice(`已创建草稿：${selected.metric_code}（待验证与激活）`);
      } else if (kind === "activate") {
        await metricLibraryApi.activateChange(selected.entry_id, input);
        setNotice(`已激活：${selected.metric_code}`);
      } else {
        await metricLibraryApi.retireChange(selected.entry_id, input);
        setNotice(`已退役：${selected.metric_code}`);
      }
      refreshEvents();
    } catch (cause: unknown) {
      const message = cause instanceof Error ? cause.message : "操作失败";
      setActionError(`${message}（草稿需先通过验证才能激活）`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-label="指标治理记录" className="ml-governance">
      <p className="ml-muted">
        指标定义的草稿 / 生效 / 退役审计（持久化事件，只增不改；C04）。
      </p>
      <div className="ml-governance__form">
        <h3>发起治理操作（无需修改 YAML）</h3>
        <label>
          指标
          <select value={entryId} onChange={(e) => setEntryId(e.target.value)}>
            {metrics
              .filter((m): m is MetricLibraryEntry & { entry_id: string } => Boolean(m.entry_id))
              .map((m) => (
                <option key={m.entry_id} value={m.entry_id}>
                  {m.metric_code}（{m.name} ·{" "}
                  {m.collection === "logistics" ? "物流口径" : "通用口径"}）
                </option>
              ))}
          </select>
          {metrics.some((m) => !m.entry_id) ? (
            <p className="ml-muted">
              {metrics.filter((m) => !m.entry_id).length} 个指标尚无库内条目，不能发起治理操作。
            </p>
          ) : null}
        </label>
        <label>
          变更内容（JSON，仅草稿需要）
          <textarea
            rows={3}
            value={changesText}
            onChange={(e) => setChangesText(e.target.value)}
            placeholder='{"benchmark": "国资委 2025 标准值…"}'
            aria-label="变更内容 JSON"
          />
        </label>
        <label>
          理由
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="如：更新基准值来源" />
        </label>
        <div className="ml-governance__actions">
          <button type="button" className="flow-btn flow-btn--primary" disabled={busy} onClick={() => void runAction("draft")}>
            创建草稿
          </button>
          <button type="button" className="flow-btn" disabled={busy} onClick={() => void runAction("activate")}>
            激活
          </button>
          <button type="button" className="flow-btn flow-btn--danger" disabled={busy} onClick={() => void runAction("retire")}>
            退役
          </button>
        </div>
        {actionError ? (
          <p role="alert" className="ml-governance__error">{actionError}</p>
        ) : null}
        {notice ? <p className="ml-governance__notice">{notice}</p> : null}
      </div>
      {error ? <p className="ml-governance__error">{error}</p> : null}
      {events === null ? <p role="status">正在读取治理记录…</p> : null}
      {events !== null && events.length === 0 ? (
        <p className="ml-muted">尚无治理事件。</p>
      ) : null}
      {events && events.length > 0 ? (
        <table className="flow-table">
          <thead>
            <tr>
              <th>时间</th><th>指标</th><th>版本</th><th>动作</th><th>操作者</th><th>理由</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td>{event.created_at?.slice(0, 19).replace("T", " ") ?? "—"}</td>
                <td><code>{event.metric_code}</code></td>
                <td>v{event.version}</td>
                <td>{event.action}</td>
                <td>{event.operator}</td>
                <td>{event.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}


export { GovernanceSection };
