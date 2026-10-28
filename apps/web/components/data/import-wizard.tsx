"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  flowApi,
  ImporterCockpitView,
  ImporterDatasetSummary,
  ImporterUploadResult,
} from "../../lib/api/client";

type Phase = "idle" | "uploading" | "ok" | "rejected" | "error";

// R3 导入向导：模板下载 → 上传 → 逐行错误 → 成功出概览 KPI。
// 五态：idle/uploading/ok/rejected/error；空态=无数据集列表。
export function ImportWizard() {
  const [datasets, setDatasets] = useState<ImporterDatasetSummary[] | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [uploadResult, setUploadResult] = useState<ImporterUploadResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cockpit, setCockpit] = useState<ImporterCockpitView | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const refreshDatasets = useCallback(() => {
    flowApi
      .listImporterDatasets()
      .then((response) => setDatasets(response.datasets))
      .catch(() => setDatasets([]));
  }, []);

  useEffect(refreshDatasets, [refreshDatasets]);

  const submit = useCallback(async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setErrorMessage("请先选择 .xlsx 文件");
      return;
    }
    setPhase("uploading");
    setErrorMessage(null);
    setUploadResult(null);
    setCockpit(null);
    try {
      const result: ImporterUploadResult = await flowApi.uploadImporterDataset(
        file,
        datasetName,
      );
      setUploadResult(result);
      if (result.ok) {
        setPhase("ok");
        refreshDatasets();
        const view = await flowApi.importerCockpit(result.dataset_id);
        setCockpit(view);
      } else {
        setPhase("rejected");
      }
    } catch {
      setPhase("error");
      setErrorMessage("导入请求失败，请确认服务已启动后重试");
    }
  }, [datasetName, refreshDatasets]);

  const remove = useCallback(
    async (datasetId: string) => {
      await flowApi.deleteImporterDataset(datasetId);
      refreshDatasets();
    },
    [refreshDatasets],
  );

  return (
    <section aria-label="真实数据导入">
      <h2>真实数据导入</h2>
      <p>
        第一步：下载模板并按中文列名填入数据。第二步：上传 .xlsx，校验通过后自动生成
        概览驾驶舱。校验失败会逐行列出原因，整批拒绝、不会写入半成品数据。
      </p>

      <fieldset>
        <legend>第一步 · 下载模板</legend>
        {/* 文件下载而非页面跳转，next/link 不适用 */}
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a href="/api/v1/importer/template/trial_balance">下载科目余额表模板</a>
        {" · "}
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a href="/api/v1/importer/template/income_statement">下载利润表模板（可选）</a>
      </fieldset>

      <fieldset>
        <legend>第二步 · 上传</legend>
        <label>
          账套名称（可选）
          <input
            type="text"
            value={datasetName}
            onChange={(event) => setDatasetName(event.target.value)}
            placeholder="如：2025 年账套"
          />
        </label>
        <label>
          模板文件
          <input ref={fileRef} type="file" accept=".xlsx" />
        </label>
        <button type="button" onClick={submit} disabled={phase === "uploading"}>
          {phase === "uploading" ? "校验并导入中…" : "校验并导入"}
        </button>
      </fieldset>

      {phase === "rejected" && uploadResult && !uploadResult.ok && (
        <div role="alert">
          <h3>校验未通过（整批拒绝）</h3>
          <ul>
            {uploadResult.errors.map((error, index) => (
              <li key={index}>
                {error.row !== "0" ? `第 ${error.row} 行 · ` : ""}
                {error.message}
              </li>
            ))}
          </ul>
        </div>
      )}
      {phase === "error" && errorMessage && (
        <div role="alert">
          <p>{errorMessage}</p>
        </div>
      )}
      {phase === "uploading" && <p role="status">正在校验并导入…</p>}

      {phase === "ok" && cockpit && uploadResult && uploadResult.ok && (
        <div role="status">
          <h3>导入成功</h3>
          <p>
            科目余额 {uploadResult.trial_balance_rows} 行
            {uploadResult.income_statement_rows > 0
              ? ` · 利润表 ${uploadResult.income_statement_rows} 行`
              : ""}
            ；期间 {cockpit.periods.join("、")}
          </p>
          <table>
            <caption>概览驾驶舱</caption>
            <thead>
              <tr>
                <th scope="col">指标</th>
                <th scope="col">数值</th>
              </tr>
            </thead>
            <tbody>
              {cockpit.kpi.map((kpi) => (
                <tr key={kpi.code}>
                  <td>{kpi.label}</td>
                  <td>{kpi.value ?? "—"}</td>
                </tr>
              ))}
              <tr>
                <td>勾稽校验（{cockpit.identity_check.formula}）</td>
                <td>
                  {cockpit.identity_check.passed
                    ? "通过"
                    : `差异 ${cockpit.identity_check.value}`}
                </td>
              </tr>
            </tbody>
          </table>
          <p>{cockpit.source_note}</p>
        </div>
      )}

      <h3>已导入数据集</h3>
      {datasets === null ? (
        <p role="status">加载中…</p>
      ) : datasets.length === 0 ? (
        <p>暂无导入数据集。</p>
      ) : (
        <ul>
          {datasets.map((dataset) => (
            <li key={dataset.id}>
              {dataset.name}（{dataset.source_filename}，{dataset.created_at}）
              <button type="button" onClick={() => remove(dataset.id)}>
                删除
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
