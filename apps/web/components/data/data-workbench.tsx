"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { FlowApiError, intakeApi } from "../../lib/api/client";
import type {
  IntakeImport,
  IntakeBatchHistoryItem,
  IntakeMapping,
  IntakeSource,
  MappingOverrideInput,
} from "../../lib/api/client";
import "./data-workbench.css";

type Stage = "prepare" | "upload" | "map" | "clean" | "publish";

const STAGES: { id: Stage; label: string }[] = [
  { id: "prepare", label: "准备" },
  { id: "upload", label: "上传与画像" },
  { id: "map", label: "映射确认" },
  { id: "clean", label: "清洗与校验" },
  { id: "publish", label: "发布" },
];


type WorkbenchState =
  | { phase: "prepare" }
  | { phase: "uploading"; filename: string }
  | { phase: "mapping"; batchId: string; source: IntakeSource; mapping: IntakeMapping }
  | { phase: "cleaning"; batchId: string; source: IntakeSource; mapping: IntakeMapping; importVersion: IntakeImport; summary: CleaningSummary }
  | { phase: "published"; importVersion: IntakeImport };

export type CleaningSummary = {
  status: string;
  totals: { raw_values: number; transformed_values: number; records: number };
  transform_rules: {
    rule_id: string;
    rule_version: number;
    applied_count: number;
    samples: Record<string, unknown>[];
  }[];
  quality_issues: { blocking: number; warning: number };
  reconciliation: { passed: number; failed: number };
};

function isFlowApiError(error: unknown): error is FlowApiError {
  return error instanceof FlowApiError;
}

export function DataWorkbench({
  initialBatchId = null,
}: {
  /** ?batch={batch_id} 深链：无批次列表端点，仅会话内已有该批次时恢复；否则显式提示 */
  initialBatchId?: string | null;
}) {
  const [stage, setStage] = useState<Stage>("prepare");
  const [state, setState] = useState<WorkbenchState>({ phase: "prepare" });
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  // 会话内最近批次（上传成功后登记；发布态的 WorkbenchState 不再携带 batchId）
  const [sessionBatchId, setSessionBatchId] = useState<string | null>(null);
  const [batchHistory, setBatchHistory] = useState<IntakeBatchHistoryItem[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const batchMiss = initialBatchId !== null && historyLoaded
    && !batchHistory.some((item) => item.id === initialBatchId)
    && sessionBatchId !== initialBatchId;

  const refreshBatchHistory = useCallback(async () => {
    try {
      const result = await intakeApi.listBatches();
      setBatchHistory(result.items);
      setHistoryError(null);
    } catch {
      setHistoryError("批次历史暂时无法加载；你仍可继续上传新数据。");
    } finally {
      setHistoryLoaded(true);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void refreshBatchHistory(), 0);
    return () => window.clearTimeout(timer);
  }, [refreshBatchHistory]);

  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const canPublish = state.phase === "cleaning" && state.importVersion.status === "ready"
    && state.importVersion.next_allowed_actions.includes("publish")
    && state.importVersion.issues.every((issue) => issue.severity !== "blocking" && issue.acknowledged)
    && state.importVersion.reconciliations.every((item) => item.passed);

  const mapping =
    state.phase === "mapping" ? state.mapping : null;

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setStage("upload");
      setState({ phase: "uploading", filename: file.name });
      try {
        const batch = await intakeApi.createBatch(file.name.replace(/\.[^.]+$/, ""));
        void refreshBatchHistory();
        const source = await intakeApi.uploadSource(batch.id, file);
        const mapping = await intakeApi.proposeMapping(source.id);
        setSessionBatchId(batch.id);
        setState({ phase: "mapping", batchId: batch.id, source, mapping });
        setStage("map");
      } catch (cause) {
        setError(
          isFlowApiError(cause) ? cause.message : "上传失败，请检查文件后重试",
        );
        setStage("prepare");
        setState({ phase: "prepare" });
      }
    },
    [refreshBatchHistory],
  );

  const overrideEntries = useMemo<MappingOverrideInput[]>(() => {
    if (!mapping) return [];
    return Object.entries(overrides).flatMap(([key, header]) => {
      const [targetSheetId, targetFieldId] = key.split("|");
      const sheet = mapping.sheets.find((item) => item.target_sheet_id === targetSheetId);
      if (!sheet || !header || header === "") return [];
      const current = sheet.fields.find((field) => field.target_field_id === targetFieldId);
      if (current && current.source_header === header) return [];
      return [
        {
          target_sheet_id: targetSheetId,
          target_field_id: targetFieldId,
          source_sheet: sheet.source_sheet,
          source_header: header,
        },
      ];
    });
  }, [mapping, overrides]);

  const confirmMapping = useCallback(async () => {
    if (!mapping || state.phase !== "mapping" || busy) return;
    setError(null);
    setBusy(true);
    try {
      let confirmed = mapping;
      if (overrideEntries.length > 0) {
        confirmed = await intakeApi.applyOverrides(
          mapping.id,
          state.source.id,
          state.source.sha256,
          overrideEntries,
        );
      }
      confirmed = await intakeApi.confirmMapping(confirmed.id);
      setState({ ...state, mapping: confirmed });
      const importVersion = await intakeApi.validateImport(
        state.source.id,
        confirmed.id,
      );
      const summary = await intakeApi.getCleaningSummary(importVersion.id);
      setState({ ...state, phase: "cleaning", mapping: confirmed, importVersion, summary });
      setReasons({});
      setStage("clean");
    } catch (cause) {
      setError(isFlowApiError(cause) ? cause.message : "映射确认失败");
    } finally {
      setBusy(false);
    }
  }, [mapping, overrideEntries, state, busy]);

  const acknowledge = async (issueId: string) => {
    if (state.phase !== "cleaning" || busy || !reasons[issueId]?.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await intakeApi.acknowledgeWarning(issueId, reasons[issueId].trim());
      const importVersion = await intakeApi.getImportVersion(state.batchId, state.importVersion.id);
      setState({ ...state, importVersion });
    } catch (cause) {
      setError(isFlowApiError(cause) ? cause.message : "警告确认或状态刷新失败，请重试");
    } finally {
      setBusy(false);
    }
  };

  const publish = useCallback(async () => {
    if (state.phase !== "cleaning" || !canPublish || busy) return;
    setError(null);
    try {
      const published = await intakeApi.publishImport(state.importVersion.id);
      setState({ phase: "published", importVersion: published });
      setStage("publish");
    } catch (cause) {
      setError(isFlowApiError(cause) ? cause.message : "发布被阻断，请先处理质量问题");
    }
  }, [state, canPublish, busy]);

  return (
    <section aria-label="数据工作台" className="data-workbench">
      <header className="data-workbench__header">
        <h1>数据工作台</h1>
        <ol aria-label="工作流阶段" className="data-workbench__stages">
          {STAGES.map((item, index) => (
            <li
              key={item.id}
              aria-current={stage === item.id ? "step" : undefined}
              data-active={stage === item.id ? "true" : undefined}
            >
              {index + 1}. {item.label}
            </li>
          ))}
        </ol>
        <button type="button" className="flow-btn" onClick={() => intakeApi.downloadTemplate()}>
          下载 FLOW 标准模板
        </button>
      </header>

      {error ? (
        <p role="alert" className="data-workbench__error flow-error">
          {error}
        </p>
      ) : null}

      {batchMiss ? (
        <p role="status" className="data-workbench__batch-note">
          当前账号下没有可查看的批次 {initialBatchId}。它可能属于其他创建者、其他企业，
          或是尚未迁入新权限模型的历史批次。
        </p>
      ) : null}

      {stage === "prepare" ? (
        <section className="data-workbench__history" aria-label="最近的数据批次">
          <div className="data-workbench__history-heading">
            <div>
              <h2>最近的数据批次</h2>
              <p>仅显示当前企业中由当前账号创建的内部批次，最多 50 条。</p>
            </div>
            <button type="button" className="flow-btn" onClick={() => void refreshBatchHistory()}>
              刷新
            </button>
          </div>
          {historyError ? <p role="status">{historyError}</p> : null}
          {historyLoaded && !historyError && batchHistory.length === 0 ? (
            <p role="status">暂无可见批次。上传并发布工作簿后，批次会显示在这里。</p>
          ) : null}
          {batchHistory.length > 0 ? (
            <div className="flow-table-wrap">
              <table className="flow-table">
                <caption>按创建时间倒序排列的内部数据批次</caption>
                <thead><tr><th scope="col">批次</th><th scope="col">状态</th><th scope="col">版本</th><th scope="col">最新版本</th><th scope="col">创建时间</th></tr></thead>
                <tbody>
                  {batchHistory.map((item) => (
                    <tr key={item.id} data-current={initialBatchId === item.id ? "true" : undefined}>
                      <th scope="row"><Link href={`/data?batch=${encodeURIComponent(item.id)}`}>{item.name}</Link></th>
                      <td>{item.status}</td>
                      <td>{item.version_count}</td>
                      <td>{item.latest_version_sequence === null ? "—" : `v${item.latest_version_sequence} · ${item.latest_version_status}`}</td>
                      <td>{new Date(item.created_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      ) : null}

      {stage === "prepare" ? (
        <div
          className="data-workbench__dropzone"
          data-drag={dragActive ? "true" : undefined}
          onDragOver={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragActive(false);
            const file = event.dataTransfer.files[0];
            if (file) void handleFile(file);
          }}
        >
          <p>将外部工作簿拖入此处，或</p>
          <label>
            选择文件
            <input
              type="file"
              accept=".xlsx"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void handleFile(file);
              }}
            />
          </label>
        </div>
      ) : null}

      {state.phase === "uploading" ? <p role="status">正在上传 {state.filename}…</p> : null}

      {state.phase === "mapping" && mapping ? (
        <div className="data-workbench__mapping">
          <table className="flow-table">
            <caption>字段映射（可修改“源表头”以覆盖自动映射）</caption>
            <thead>
              <tr>
                <th scope="col">目标工作表</th>
                <th scope="col">目标字段</th>
                <th scope="col">自动映射源表头</th>
                <th scope="col">置信度</th>
                <th scope="col">覆盖为</th>
              </tr>
            </thead>
            <tbody>
              {mapping.sheets.flatMap((sheet) =>
                [...sheet.fields, ...sheet.unresolved_required_fields
                  .filter((id) => !sheet.fields.some((field) => field.target_field_id === id))
                  .map((id) => ({ target_field_id: id, source_header: "", confidence: "待映射" }))
                ].map((field) => {
                  const key = `${sheet.target_sheet_id}|${field.target_field_id}`;
                  return (
                    <tr key={key}>
                      <td>{sheet.target_sheet_id}</td>
                      <td>{field.target_field_id}</td>
                      <td>{field.source_header || "（未映射）"}</td>
                      <td>{field.confidence}</td>
                      <td>
                        <input
                          aria-label={`覆盖 ${sheet.target_sheet_id}.${field.target_field_id} 的源表头`}
                          value={overrides[key] ?? ""}
                          placeholder={field.source_header || "源表头"}
                          onChange={(event) =>
                            setOverrides((prev) => ({
                              ...prev,
                              [key]: event.target.value,
                            }))
                          }
                        />
                      </td>
                    </tr>
                  );
                }),
              )}
            </tbody>
          </table>
          <button type="button" className="flow-btn flow-btn--primary" disabled={busy} onClick={() => void confirmMapping()}>
            确认映射并校验
          </button>
        </div>
      ) : null}

      {state.phase === "cleaning" ? (
        <div className="data-workbench__cleaning">
          <h2>清洗与校验结果</h2>
          <p>
            原始值 {state.summary.totals.raw_values} · 转换 {state.summary.totals.transformed_values}{" "}
            · 记录 {state.summary.totals.records}
          </p>
          <p>
            质量问题：阻断 {state.summary.quality_issues.blocking} / 警告{" "}
            {state.summary.quality_issues.warning} · 对账通过{" "}
            {state.summary.reconciliation.passed} / 失败 {state.summary.reconciliation.failed}
          </p>
          <ul>
            {state.summary.transform_rules.map((rule) => (
              <li key={`${rule.rule_id}@${rule.rule_version}`}>
                {rule.rule_id} v{rule.rule_version}：应用 {rule.applied_count} 次
              </li>
            ))}
          </ul>
          <p>导入状态：{state.importVersion.status}</p>
          <p>可执行操作：{state.importVersion.next_allowed_actions.map((action) => ({
            acknowledge_warnings: "确认警告", publish: "发布", create_correction: "修改映射", validate: "重新校验", export: "导出",
          }[action] ?? action)).join("、")}</p>
          <ul aria-label="质量问题详情">
            {state.importVersion.issues.map((issue) => (
              <li key={issue.id}>
                <p>{issue.severity === "blocking" ? "阻断" : "警告"}：{issue.message}（{issue.code}）</p>
                <p>来源：{issue.sheet_name ?? "未知工作表"} · 行 {issue.source_row ?? "—"} · 列 {issue.source_column ?? "—"}</p>
                <p>证据：{issue.evidence}</p>
                <p>修复建议：{issue.repair_suggestion}</p>
                {issue.severity === "warning" ? issue.acknowledged ? <p>已确认</p> : (
                  <div className="data-workbench__warning-reason">
                    <label>确认原因
                      <input aria-label={`警告 ${issue.id} 确认原因`} value={reasons[issue.id] ?? ""}
                        onChange={(event) => setReasons((prev) => ({ ...prev, [issue.id]: event.target.value }))} />
                    </label>
                    <button type="button" className="flow-btn" aria-label={`确认警告 ${issue.id}`} disabled={busy || !reasons[issue.id]?.trim()}
                      onClick={() => void acknowledge(issue.id)}>确认此警告</button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
          <ul aria-label="对账详情">
            {state.importVersion.reconciliations.map((item) => (
              <li key={item.code}>{item.code}：{item.passed ? "通过" : "失败"} · 预期 {item.expected_value ?? "—"} · 实际 {item.actual_value ?? "—"}</li>
            ))}
          </ul>
          <div className="data-workbench__actions">
            <button type="button" className="flow-btn" disabled={busy} onClick={() => {
              setError(null);
              setState({ phase: "mapping", batchId: state.batchId, source: state.source, mapping: state.mapping });
              setStage("map");
            }}>返回修改映射</button>
            <button type="button" className="flow-btn flow-btn--primary" disabled={busy || !canPublish} onClick={() => void publish()}>
              发布此导入版本
            </button>
          </div>
        </div>
      ) : null}

      {state.phase === "published" ? (
        <div role="status" className="data-workbench__published">
          <h2>导入版本已发布</h2>
          <button type="button" className="flow-btn" onClick={() => void intakeApi.exportStandardizedWorkbook(state.importVersion.id)}>
            下载标准化工作簿
          </button>
          <p className="data-workbench__next">
            下一步：
            <Link className="flow-btn" href="/operations">前往经营分析</Link>{" "}
            <Link className="flow-btn" href="/">前往经营驾驶舱</Link>
          </p>
        </div>
      ) : null}
    </section>
  );
}

export default DataWorkbench;
