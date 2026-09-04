"use client";

import { useCallback, useMemo, useState } from "react";

import { FlowApiError, intakeApi } from "../../lib/api/client";
import type {
  IntakeImport,
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

const ACTOR = "finance.bp@example.com";

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

export function DataWorkbench() {
  const [stage, setStage] = useState<Stage>("prepare");
  const [state, setState] = useState<WorkbenchState>({ phase: "prepare" });
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [overrides, setOverrides] = useState<Record<string, string>>({});

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
        const source = await intakeApi.uploadSource(batch.id, file);
        const mapping = await intakeApi.proposeMapping(source.id);
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
    [],
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
          ACTOR,
        );
      }
      confirmed = await intakeApi.confirmMapping(confirmed.id, ACTOR);
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
      await intakeApi.acknowledgeWarning(issueId, ACTOR, reasons[issueId].trim());
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
        <button type="button" onClick={() => intakeApi.downloadTemplate()}>
          下载 FLOW 标准模板
        </button>
      </header>

      {error ? (
        <p role="alert" className="data-workbench__error">
          {error}
        </p>
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
          <table>
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
          <button type="button" disabled={busy} onClick={() => void confirmMapping()}>
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
                  <div>
                    <label>确认原因
                      <input aria-label={`警告 ${issue.id} 确认原因`} value={reasons[issue.id] ?? ""}
                        onChange={(event) => setReasons((prev) => ({ ...prev, [issue.id]: event.target.value }))} />
                    </label>
                    <button type="button" aria-label={`确认警告 ${issue.id}`} disabled={busy || !reasons[issue.id]?.trim()}
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
          <button type="button" disabled={busy} onClick={() => {
            setError(null);
            setState({ phase: "mapping", batchId: state.batchId, source: state.source, mapping: state.mapping });
            setStage("map");
          }}>返回修改映射</button>
          <button type="button" disabled={busy || !canPublish} onClick={() => void publish()}>
            发布此导入版本
          </button>
        </div>
      ) : null}

      {state.phase === "published" ? (
        <div role="status" className="data-workbench__published">
          <h2>导入版本已发布</h2>
          <button type="button" onClick={() => void intakeApi.exportStandardizedWorkbook(state.importVersion.id)}>
            下载标准化工作簿
          </button>
        </div>
      ) : null}
    </section>
  );
}

export default DataWorkbench;
