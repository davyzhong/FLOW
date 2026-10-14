"use client";

/**
 * 模块页共享渲染器（批次 C-2）：资产负债 / 营运资金。
 *
 * - KPI 网格（可用值 + 前期值 + 口径注；不可用显式灰态，不补零）；
 * - 图表以「期间 × 系列」表格呈现（数据表即无障碍基线；ECharts 视图由
 *   builders 渐进增强，模块先立数据契约）；
 * - 降级块（unavailable）显式列出原因；
 * - 演示数据源全局标注。
 */

import { flowApi } from "../../lib/api/client";
import type { CockpitModuleResponse } from "../../lib/api/client";
import { useApiQuery } from "../../lib/api/use-api-query";

function formatValue(raw: string | null, unit: string): string {
  if (raw === null) return "—";
  if (unit === "ratio") return `${(Number(raw) * 100).toFixed(1)}%`;
  if (unit === "day") return `${Number(raw).toFixed(1)} 天`;
  const n = Number(raw);
  return `${n.toLocaleString("zh-CN", { maximumFractionDigits: 1 })} ${unit}`;
}

export function CockpitModulePage({
  moduleId,
  title,
}: {
  moduleId: "balance-sheet" | "working-capital" | "expenses" | "cashflow";
  title: string;
}) {
  const query = useApiQuery<CockpitModuleResponse>(
    (signal) => flowApi.getCockpitModule(moduleId, signal),
    [moduleId],
  );

  if (query.loading) {
    return (
      <div data-status="loading" aria-busy="true">
        <h2>{title}</h2>
        <p>加载中…</p>
      </div>
    );
  }
  if (query.error || !query.data) {
    return (
      <div data-status="error">
        <h2>{title}</h2>
        <p role="alert">{query.error ?? "模块数据未就绪。"}</p>
        <button type="button" onClick={query.reload}>
          重试
        </button>
      </div>
    );
  }
  const data = query.data;
  const kpis: Record<string, unknown>[] = data.kpis ?? [];
  const unavailable: Record<string, unknown>[] = data.unavailable ?? [];
  return (
    <div data-status="ready" data-module={data.module}>
      <h2>
        {data.title}
        <span className="module-period">
          （{data.period}，对比 {data.prior_period}）
        </span>
      </h2>
      <p className="module-source-notice">{data.source_notice}</p>

      <section aria-label={`${data.title} KPI`}>
        <ul className="module-kpi-grid">
          {kpis.map((kpi) => (
            <li
              key={String(kpi.name)}
              data-testid="module-kpi"
              data-status={kpi.status}
            >
              <span className="kpi-name">{String(kpi.name)}</span>
              {kpi.status === "available" ? (
                <strong title={`精确值：${String(kpi.value)}`}>
                  {formatValue(
                    String(kpi.value),
                    kpi.unit === "ratio" ? "ratio" : String(data.unit),
                  )}
                </strong>
              ) : (
                <strong data-status="unavailable">
                  {String(kpi.unavailable_code ?? "not_disclosed")}
                </strong>
              )}
              {kpi.prior_value ? (
                <span className="kpi-prior">
                  前期{" "}
                  {formatValue(
                    String(kpi.prior_value),
                    String(data.unit),
                  )}
                </span>
              ) : null}
              {kpi.caliber_note ? (
                <span className="kpi-caliber">
                  {kpi.caliber_note ? String(kpi.caliber_note) : null}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section aria-label={`${data.title} 图表数据`}>
        <h3>图表数据</h3>
        {Object.entries(
          (data.charts ?? {}) as Record<string, Record<string, unknown>>,
        ).map(([key, chartUnknown]) => {
          const typed = chartUnknown as {
            title?: string;
            type?: string;
            periods?: string[];
            series?: Record<string, (string | null)[]>;
            identity?: string;
            note?: string;
          };
          return (
            <div key={key} data-chart={key}>
              <h4>{typed.title ?? key}</h4>
              {typed.identity ? <p>{typed.identity}</p> : null}
              {typed.series ? (
                <table>
                  <thead>
                    <tr>
                      <th>系列</th>
                      {(typed.periods ?? []).map((period) => (
                        <th key={period}>{period}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(typed.series).map(([name, values]) => (
                      <tr key={name}>
                        <th>{name}</th>
                        {(values ?? []).map((value, index) => (
                          <td key={index}>{value === null ? "—" : String(value)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
              {typed.note ? <p className="chart-note">{typed.note}</p> : null}
            </div>
          );
        })}
      </section>

      {unavailable.length > 0 ? (
        <section aria-label={`${data.title} 不可用块`}>
          <h3>不可用块（如实缺省）</h3>
          <ul>
            {unavailable.map((block) => (
              <li key={String(block.code)} data-status="unavailable">
                <strong>{String(block.block)}</strong>：{String(block.reason)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
