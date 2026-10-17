"use client";

/** 驾驶舱模块页：真实指标、可视图表、无障碍数据表、期间比较与来源追溯。 */

import Link from "next/link";

import { flowApi } from "../../lib/api/client";
import type { CockpitModuleResponse } from "../../lib/api/client";
import { useApiQuery } from "../../lib/api/use-api-query";
import { ChartBox } from "./charts/echarts-base";
import "./cockpit.css";
import { buildModuleChartOption, normalizeModuleSeries, type ModuleChartData } from "./charts/module-options";
import { formatFinancialValue } from "./number-format";

function asNumber(raw: unknown): number | null {
  if (raw === null || raw === undefined || raw === "") return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

function metricCodeFor(name: string): string {
  if (/订单|包裹|件量|客户数|件数/.test(name)) return "orders";
  if (/资产负债率/.test(name)) return "debt_asset_ratio";
  if (/流动比率/.test(name)) return "current_ratio";
  if (/速动比率/.test(name)) return "quick_ratio";
  if (/现金比率/.test(name)) return "cash_ratio";
  if (/权益乘数/.test(name)) return "equity_multiplier";
  if (/OCF\/流动负债/.test(name)) return "ocf_current_liab_ratio";
  if (/利息保障倍数/.test(name)) return "interest_coverage";
  if (/净现比/.test(name)) return "net_cash_ratio";
  if (/毛利率/.test(name)) return "gross_margin";
  if (/净利率/.test(name)) return "net_margin";
  if (/周转率/.test(name)) return "inventory_turnover";
  if (/DSO|DIO|DPO|CCC|天数/.test(name)) return "dso_days";
  return "";
}

function changeSummary(
  value: unknown,
  prior: unknown,
  unit: string,
  metricCode: string,
  priorPeriod: string,
): string {
  const current = asNumber(value);
  const previous = asNumber(prior);
  if (current === null || previous === null) return "前期不可比";
  if (previous === 0) return current === 0 ? `较 ${priorPeriod} 持平` : `较 ${priorPeriod} 新增`;
  const difference = current - previous;
  const direction = difference > 0 ? "上升" : difference < 0 ? "下降" : "持平";
  if (unit === "ratio" && !["current_ratio", "quick_ratio", "cash_ratio", "equity_multiplier", "ocf_current_liab_ratio", "interest_coverage", "net_cash_ratio"].includes(metricCode)) {
    const points = formatFinancialValue(difference, { metricCode: "", unit: "ratio" });
    return `较 ${priorPeriod} ${direction} ${points} 个百分点`;
  }
  const relative = formatFinancialValue((difference / Math.abs(previous)) * 100, { unit: "%" });
  const absolute = formatFinancialValue(difference, { metricCode, unit });
  return `较 ${priorPeriod} ${direction} ${relative}（${difference > 0 ? "+" : ""}${absolute}）`;
}

export function CockpitModulePage({
  moduleId,
  title,
}: {
  moduleId: "balance-sheet" | "working-capital" | "expenses" | "cashflow" | "risk" | "consolidation";
  title: string;
}) {
  const query = useApiQuery<CockpitModuleResponse>(
    (signal) => flowApi.getCockpitModule(moduleId, signal),
    [moduleId],
  );

  if (query.loading) {
    return <div data-status="loading" aria-busy="true"><h2>{title}</h2><p>加载中…</p></div>;
  }
  if (query.error || !query.data) {
    return <div data-status="error"><h2>{title}</h2><p role="alert">{query.error ?? "模块数据未就绪。"}</p><button type="button" onClick={query.reload}>重试</button></div>;
  }

  const data = query.data;
  const kpis: Record<string, unknown>[] = data.kpis ?? [];
  const unavailable: Record<string, unknown>[] = data.unavailable ?? [];
  const reportId = data.report_ids?.[0];
  const charts = Object.entries((data.charts ?? {}) as Record<string, ModuleChartData>);

  return (
    <div className="module-page" data-status="ready" data-module={data.module}>
      <header className="module-page__header">
        <div><span className="module-page__eyebrow">FLOW · 财务驾驶舱</span><h2>{data.title}</h2></div>
        <span className="module-period">{data.period} · 对比 {data.prior_period}</span>
      </header>
      <p className="module-source-notice">{data.source_notice}</p>
      <section aria-label={`${data.title} KPI`} className="module-kpis">
        <ul className="module-kpi-grid" data-count={kpis.length}>
          {kpis.map((kpi) => {
            const name = String(kpi.name);
            const unit = String(kpi.unit ?? data.unit);
            const metricCode = metricCodeFor(name);
            const available = kpi.status === "available";
            return (
              <li key={name} className="module-kpi-card" data-testid="module-kpi" data-status={kpi.status}>
                <span className="kpi-name">{name}</span>
                {available ? (
                  <strong title={`精确值：${String(kpi.value)}`}>
                    {formatFinancialValue(kpi.value as string | number | null, { metricCode, unit })}
                  </strong>
                ) : <strong data-status="unavailable">{String(kpi.unavailable_code ?? "not_disclosed")}</strong>}
                {kpi.prior_value !== null && kpi.prior_value !== undefined ? (
                  <span className="kpi-prior">前期 {formatFinancialValue(kpi.prior_value as string | number, { metricCode, unit })}</span>
                ) : null}
                {available && kpi.prior_value !== null && kpi.prior_value !== undefined ? (
                  <span className="kpi-change" data-direction={Number(kpi.value) >= Number(kpi.prior_value) ? "up" : "down"}>
                    {changeSummary(kpi.value, kpi.prior_value, unit, metricCode, data.prior_period)}
                  </span>
                ) : null}
                {typeof kpi.rate === "string" ? <span className="kpi-caliber">费用占收入 {formatFinancialValue(kpi.rate, { unit: "ratio" })}</span> : null}
                {kpi.caliber_note ? <span className="kpi-caliber">{String(kpi.caliber_note)}</span> : null}
                {reportId ? <Link href={`/statements?report=${encodeURIComponent(reportId)}`} className="module-source-link">查看来源财报</Link> : null}
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-label={`${data.title} 图表`} className="module-charts">
        <div className="module-section-heading"><h3>经营趋势与结构</h3><span>期间序列 · 可追溯至来源财报</span></div>
        {charts.length ? charts.map(([key, chart]) => {
          const option = buildModuleChartOption(chart, data.unit);
          const seriesEntries = Object.entries(chart.series ?? {});
          const periods = chart.periods ?? [];
          const seriesUnit = chart.unit ?? data.unit;
          const displayUnit =
            seriesUnit === "ratio" ? "%" : seriesUnit === "day" ? "天" : seriesUnit;
          const steps = chart.steps ?? {};
          return (
            <article key={key} data-chart={key} className="module-chart-card">
              <header className="module-chart-heading">
                <h4>{chart.title ?? key}</h4>
                <span>{periods.join(" / ") || data.period} · {displayUnit}</span>
              </header>
              {chart.type === "formula_card" ? (
                <div className="module-formula-card" data-testid={`cockpit-module-chart-${key}`}>
                  <p>{String(chart.identity ?? "公式关系")}</p>
                  <div>{["dso", "dio", "dpo", "ccc"].map((field) => (
                    <span key={field}>{field.toUpperCase()}：{formatFinancialValue((chart as Record<string, unknown>)[field] as string | null, { metricCode: "dso_days", unit: "day" })}</span>
                  ))}</div>
                </div>
              ) : option ? (
                <div className="module-chart-visual"><ChartBox
                    title=""
                    option={option}
                    ariaLabel={`${chart.title ?? key}，${periods.join("、") || data.period}`}
                    testId={`cockpit-module-chart-${key}`}
                    height={260}
                  /></div>
              ) : <p className="chart-empty" data-testid={`cockpit-module-chart-${key}-empty`}>该图表无足够可用事实，未补零或生成趋势。</p>}
              {seriesEntries.length ? (
                <div className="module-table-scroll"><table className="module-chart-table">
                  <thead><tr><th>指标</th>{periods.map((period) => <th key={period}>{period}</th>)}</tr></thead>
                  <tbody>{seriesEntries.map(([name, raw]) => {
                    const values = normalizeModuleSeries(raw);
                    const unit = chart.type === "line" && /率|margin/i.test(name) ? "ratio" : seriesUnit;
                    return <tr key={name}><th>{name}</th>{values.map((value, index) => (
                      <td key={index}>{formatFinancialValue(value as string | number | null, { metricCode: metricCodeFor(name), unit })}</td>
                    ))}</tr>;
                  })}</tbody>
                </table></div>
              ) : null}
              {Object.keys(steps).length ? <dl className="module-waterfall-values">{Object.entries(steps).map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{formatFinancialValue(value as string | number | null, { unit: seriesUnit })}</dd></div>)}</dl> : null}
              {chart.note ? <p className="chart-note">{chart.note}</p> : null}
              {chart.fact_ids || chart.source_fact_ids ? (
                <details className="module-chart-sources">
                  <summary>查看来源登记事实 ID</summary>
                  <p>来源登记：config/damai/source_facts_v1.yaml</p>
                  <ul>
                    {Object.entries((chart.fact_ids ?? chart.source_fact_ids) as Record<string, unknown>).map(([period, factId]) => (
                      <li key={`${period}:${String(factId)}`}>{period} · {String(factId)}</li>
                    ))}
                  </ul>
                </details>
              ) : null}
              {reportId ? <Link href={`/statements?report=${encodeURIComponent(reportId)}`} className="module-source-link">追溯至来源财报</Link> : null}
            </article>
          );
        }) : <p className="chart-empty">当前期间没有可绘制的趋势数据；相关缺口见下方说明。</p>}
      </section>

      {unavailable.length > 0 ? (
        <section aria-label={`${data.title} 不可用块`} className="module-unavailable">
          <div className="module-section-heading"><h3>当前未披露或暂不可计算</h3><span>不补零、不推测</span></div>
          <ul>{unavailable.map((block) => <li key={String(block.code)} data-status="unavailable"><strong>{String(block.block)}</strong>：{String(block.reason)}</li>)}</ul>
        </section>
      ) : null}
    </div>
  );
}
