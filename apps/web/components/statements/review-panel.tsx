"use client";

// 报表事实复核面板（B05）：更正需原因与操作者，审计链只增不改；
// 发布受勾稽质量门禁约束（关键不平衡 409 阻断），发布后报表锁定。
import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  statementApi,
  type Correction,
  type StatementReportDetail,
} from "../../lib/api/client";

const COLUMN_OPTIONS = [
  ["value_end", "期末余额"],
  ["value_begin", "期初余额"],
  ["value_current", "本期发生额"],
  ["value_prior", "上期发生额"],
] as const;

export function ReviewPanel({
  detail,
  onChanged,
}: {
  detail: StatementReportDetail;
  onChanged: () => void;
}) {
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [statementType, setStatementType] = useState("");
  const [itemName, setItemName] = useState("");
  const [columnKey, setColumnKey] = useState<string>("value_current");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const [operator, setOperator] = useState("finance.bp");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const published = detail.status === "published";

  const reload = useCallback(() => {
    statementApi
      .listCorrections(detail.id)
      .then((list) => setCorrections([...list.corrections]))
      .catch(() => setCorrections([]));
  }, [detail.id]);

  useEffect(() => {
    reload();
  }, [reload]);

  const section = detail.sections.find((s) => s.statement_type === statementType);
  const items = section?.items ?? [];

  const submitCorrection = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      await statementApi.addCorrection(detail.id, {
        statement_type: statementType,
        item_name: itemName,
        column_key: columnKey,
        value,
        reason,
        operator,
      });
      setMessage("更正已记录");
      setValue("");
      setReason("");
      reload();
      onChanged();
    } catch (error) {
      setMessage(
        error instanceof FlowApiError
          ? `更正被拒绝（${error.code}）：${error.message}`
          : "更正失败",
      );
    } finally {
      setBusy(false);
    }
  }, [columnKey, detail.id, itemName, onChanged, operator, reason, reload, statementType, value]);

  const publish = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      await statementApi.publishReport(detail.id);
      setMessage("已发布，报表事实版本已冻结");
      onChanged();
    } catch (error) {
      setMessage(
        error instanceof FlowApiError
          ? `发布被阻断（${error.code}）：${error.message}`
          : "发布失败",
      );
    } finally {
      setBusy(false);
    }
  }, [detail.id, onChanged]);

  return (
    <section className="stmt-review" aria-label="事实复核与更正">
      <header className="stmt-review__head">
        <h3>事实复核</h3>
        <span className={`stmt-review__status is-${detail.status}`}>
          {published ? "已发布（锁定）" : "草稿（可更正）"}
        </span>
      </header>

      {corrections.length > 0 ? (
        <ul className="stmt-review__list">
          {corrections.map((correction) => (
            <li key={correction.id}>
              <code>{correction.statement_type}</code>「{correction.item_name}」
              {COLUMN_OPTIONS.find(([key]) => key === correction.column_key)?.[1]}：
              {correction.old_value ?? "空"} → {correction.new_value ?? "空"}
              <small>（{correction.operator}：{correction.reason}）</small>
            </li>
          ))}
        </ul>
      ) : (
        <p className="stmt-review__empty">暂无更正记录。</p>
      )}

      {!published ? (
        <div className="stmt-review__form">
          <select
            aria-label="报表"
            value={statementType}
            onChange={(event) => {
              setStatementType(event.target.value);
              setItemName("");
            }}
          >
            <option value="">选择报表…</option>
            {detail.sections.map((s) => (
              <option key={s.statement_type} value={s.statement_type}>
                {s.statement_type}
              </option>
            ))}
          </select>
          <select
            aria-label="行项目"
            value={itemName}
            onChange={(event) => setItemName(event.target.value)}
            disabled={!section}
          >
            <option value="">选择行项目…</option>
            {items.map((item) => (
              <option key={item.item_name} value={item.item_name}>
                {item.item_name}
              </option>
            ))}
          </select>
          <select
            aria-label="列"
            value={columnKey}
            onChange={(event) => setColumnKey(event.target.value)}
          >
            {COLUMN_OPTIONS.map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          <input
            aria-label="更正值"
            placeholder="更正值（披露原文单位）"
            value={value}
            onChange={(event) => setValue(event.target.value)}
          />
          <input
            aria-label="更正原因"
            placeholder="更正原因（必填）"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          <input
            aria-label="操作者"
            value={operator}
            onChange={(event) => setOperator(event.target.value)}
          />
          <button
            type="button"
            disabled={busy || !statementType || !itemName || !reason.trim()}
            onClick={() => void submitCorrection()}
          >
            记录更正
          </button>
          <button
            type="button"
            className="stmt-review__publish"
            disabled={busy}
            onClick={() => void publish()}
          >
            复核通过并发布
          </button>
        </div>
      ) : null}

      {message ? (
        <p className="stmt-review__message" role="status">
          {message}
        </p>
      ) : null}
    </section>
  );
}
