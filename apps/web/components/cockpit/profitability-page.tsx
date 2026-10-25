"use client";

import Link from "next/link";

import { ChartBox, CHART_THEME } from "./charts/echarts-base";
import { buildCombo, buildDupont, type ComboSeries, type DupontNode } from "./charts/builders";
import "./cockpit.css";
import { formatFinancialValue } from "./number-format";
import { flowApi, type CockpitProfitabilityMetric, type CockpitProfitabilityResponse } from "../../lib/api/client";
import { useApiQuery } from "../../lib/api/use-api-query";
import { metricFocusHref, statementReportHref, statementRowId } from "../../lib/deep-links";

const FACTORS = [
  { code: "net_margin", label: "净利率", unit: "ratio", formula: "净利润 ÷ 营业收入" },
  { code: "total_asset_turnover", label: "总资产周转率", unit: "次", formula: "营业收入 ÷ 平均总资产" },
  { code: "equity_multiplier", label: "权益乘数", unit: "倍", formula: "平均总资产 ÷ 平均净资产" },
  { code: "roe", label: "净资产收益率（ROE）", unit: "ratio", formula: "净利润 ÷ 平均净资产" },
] as const;

type ProfitabilityPeriod = NonNullable<CockpitProfitabilityResponse["periods"]>[number];

function metricFor(
  period: ProfitabilityPeriod | undefined,
  code: string,
): CockpitProfitabilityMetric | undefined {
  return period?.metrics?.find((metric) => metric.metric_code === code);
}

function displayMetric(metric: CockpitProfitabilityMetric | undefined, unit: string): string {
  if (!metric || metric.status !== "available" || metric.value === null) return "暂不可用";
  return formatFinancialValue(metric.value, {
    metricCode: metric.metric_code,
    unit,
  });
}

function dupontOption(data: CockpitProfitabilityResponse): ReturnType<typeof buildDupont> {
  const periods = data.periods ?? [];
  const current = periods[periods.length - 1];
  if (!current || current.consistency?.status !== "passed") return undefined;
  const values = Object.fromEntries((current.metrics ?? []).map((metric) => [metric.metric_code, metric]));
  if (FACTORS.some((factor) => values[factor.code]?.status !== "available")) return undefined;
  const node = (name: string, code: string, x: number, y: number, size: number, color: string): DupontNode => {
    const metric = values[code];
    const value = displayMetric(metric, FACTORS.find((factor) => factor.code === code)?.unit ?? "");
    return {
      name: `${name}\n${value}`,
      x,
      y,
      symbolSize: size,
      color,
      formula: `${name}：${metric?.formula ?? "指标定义见指标库"}\n冻结于 ${current.snapshot_id ?? "—"}`,
    };
  };
  return buildDupont(
    node("ROE", "roe", 80, 150, 78, CHART_THEME.blue),
    [
      { node: node("净利率", "net_margin", 300, 45, 68, CHART_THEME.teal), children: [] },
      { node: node("总资产周转率", "total_asset_turnover", 300, 150, 68, CHART_THEME.purple), children: [] },
      { node: node("权益乘数", "equity_multiplier", 300, 255, 68, CHART_THEME.gold), children: [] },
    ],
  );
}

function comparisonOption(
  periods: ProfitabilityPeriod[],
  metrics: { code: string; label: string }[],
  unit: string,
): ReturnType<typeof buildCombo> {
  if (periods.length < 2) return undefined;
  const series: ComboSeries[] = metrics.map(({ code, label }) => ({
    key: code,
    title: label,
    axis: "bar",
    unit: unit === "ratio" ? "%" : unit,
    points: periods.map((period) => {
      const item = metricFor(period, code);
      const value = item?.status === "available" && item.value
        ? Number(item.value) * (unit === "ratio" ? 100 : 1)
        : null;
      return {
        period: period.period,
        value: value ?? Number.NaN,
        display: displayMetric(item, unit === "ratio" ? "ratio" : code === "total_asset_turnover" ? "次" : "倍"),
        status: value === null || !Number.isFinite(value) ? "unavailable" : "ready",
      };
    }),
  }));
  return buildCombo(series);
}

export function CockpitProfitabilityPage() {
  const query = useApiQuery<CockpitProfitabilityResponse>(
    (signal) => flowApi.getCockpitProfitability(signal),
    [],
  );

  if (query.loading) return <div className="module-page" data-status="loading" aria-busy="true"><h1>盈利能力与杜邦分析</h1><p>读取已发布的财报快照…</p></div>;
  if (query.error || !query.data) return <div className="module-page" data-status="error"><h1>盈利能力与杜邦分析</h1><p role="alert">{query.error ?? "盈利分析数据未就绪。"}</p><button type="button" onClick={query.reload}>重试</button></div>;

  const data = query.data;
  const periods = data.periods ?? [];
  const current = periods[periods.length - 1];
  const prior = periods.length > 1 ? periods[periods.length - 2] : undefined;
  const option = dupontOption(data);

  return (
    <div className="module-page profitability-page" data-status="ready" data-module="profitability">
      <header className="module-page__header">
        <div><span className="module-page__eyebrow">FLOW · 财务驾驶舱</span><h1>盈利能力与杜邦分析</h1></div>
        <span className="module-period">{prior?.period ?? "—"} → {current?.period ?? "—"}</span>
      </header>
      <p className="module-source-notice">{data.source_notice} 本页只读取已冻结客观财报快照，不在展示时重算指标。</p>

      <section className="profitability-summary" aria-label="杜邦三因子">
        <div className="module-section-heading"><h2>杜邦三因子</h2><span>ROE = 净利率 × 总资产周转率 × 权益乘数</span></div>
        <div className="profitability-grid">
          {FACTORS.map((factor) => {
            const value = metricFor(current, factor.code);
            const before = metricFor(prior, factor.code);
            return (
              <article key={factor.code} className="profitability-metric" data-status={value?.status ?? "unavailable"}>
                <span>{factor.label}</span>
                <strong>{displayMetric(value, factor.unit)}</strong>
                <small>前期 {displayMetric(before, factor.unit)}</small>
                <small>{factor.formula}</small>
                <Link href={metricFocusHref(factor.code)}>指标口径与关系</Link>
              </article>
            );
          })}
        </div>
      </section>

      <section className="profitability-visuals" aria-label="杜邦图形分析">
        <ChartBox
          title="杜邦驱动关系"
          sub={current?.snapshot_id ? `冻结快照 ${current.snapshot_id}` : "缺少冻结的分析指标"}
          option={option}
          ariaLabel="ROE 由净利率、总资产周转率和权益乘数构成的杜邦关系图"
          testId="cockpit-profitability-dupont"
          height={350}
        />
        <article className="module-chart-card profitability-check" data-status={current?.consistency?.status ?? "unavailable"}>
          <h3>勾稽校验</h3>
          <strong>{current?.consistency?.status === "passed" ? "三因子乘积与 ROE 一致" : current?.consistency?.status === "failed" ? "勾稽未通过" : "数据不足，未校验"}</strong>
          <p>容差 {current?.consistency?.tolerance ?? "—"} · 差异 {current?.consistency?.difference ?? "—"}</p>
          <p>杜邦分解用于数学勾稽，不自动解释经营原因。</p>
        </article>
      </section>

      <section className="profitability-comparisons" aria-label="两期财年比较">
        <div className="module-section-heading"><h2>两期财年比较</h2><span>仅比较已冻结的披露财年，不延伸推断长期趋势</span></div>
        <div className="profitability-comparison-grid">
          <ChartBox
            title="ROE 与净利率"
            sub={periods.map((period) => period.period).join(" / ")}
            option={comparisonOption(periods, [{ code: "roe", label: "ROE" }, { code: "net_margin", label: "净利率" }], "ratio")}
            ariaLabel="ROE 和净利率的两期财年比较图"
            testId="cockpit-profitability-roe-comparison"
            height={280}
          />
          <ChartBox
            title="总资产周转率（次）"
            sub={periods.map((period) => period.period).join(" / ")}
            option={comparisonOption(periods, [{ code: "total_asset_turnover", label: "总资产周转率" }], "次")}
            ariaLabel="总资产周转率的两期财年比较图，单位为次"
            testId="cockpit-profitability-efficiency-comparison"
            height={280}
          />
          <ChartBox
            title="权益乘数（倍）"
            sub={periods.map((period) => period.period).join(" / ")}
            option={comparisonOption(periods, [{ code: "equity_multiplier", label: "权益乘数" }], "倍")}
            ariaLabel="权益乘数的两期财年比较图，单位为倍"
            testId="cockpit-profitability-leverage-comparison"
            height={280}
          />
        </div>
      </section>

      <section className="module-unavailable" aria-label="盈利能力指标明细">
        <div className="module-section-heading"><h2>期间、来源与口径</h2><span>仅显示冻结快照中实际存在的结果</span></div>
        <div className="module-table-scroll" role="region" aria-label="期间来源与口径数据表" tabIndex={0}><table className="module-chart-table">
          <thead><tr><th>期间</th><th>指标</th><th>数值</th><th>状态/口径版本</th><th>来源</th></tr></thead>
          <tbody>{periods.flatMap((period) => (period.metrics ?? []).map((metric) => (
            <tr key={`${period.period}:${metric.metric_code}`}>
              <td>{period.period}</td>
              <th scope="row">{FACTORS.find((factor) => factor.code === metric.metric_code)?.label ?? metric.metric_code}</th>
              <td>{displayMetric(metric, FACTORS.find((factor) => factor.code === metric.metric_code)?.unit ?? "")}</td>
              <td>{metric.status === "available" ? metric.definition_version : metric.reason ?? "不可用"}</td>
              <td>
                <Link href={statementReportHref(period.report_id)}>来源财报</Link>
                {(metric.source_facts ?? []).map((fact, factIndex) => fact.statement_type && fact.item_name ? (
                  <span key={`${fact.statement_type}:${fact.item_name}:${fact.page_number ?? ""}:${factIndex}`}>
                    {" · "}<Link href={`${statementReportHref(period.report_id)}#${statementRowId(fact.statement_type, fact.item_name)}`}>{fact.item_name}行</Link>
                    {fact.page_number ? `（第 ${fact.page_number} 页）` : ""}
                  </span>
                ) : null)}
                {period.snapshot_id ? <span className="profitability-snapshot-id"> · 快照 {period.snapshot_id}</span> : null}
              </td>
            </tr>
          )))}</tbody>
        </table></div>
      </section>
      {(data.unavailable ?? []).length ? <section className="module-unavailable" aria-label="数据缺口"><div className="module-section-heading"><h2>当前不可用项</h2><span>不补零、不推测</span></div><ul>{(data.unavailable ?? []).map((item) => <li key={`${item.period}:${item.metric_code}`}><strong>{item.period} · {item.metric_code}</strong>：{item.reason}</li>)}</ul></section> : null}
      {current ? <p className="profitability-source">报告：<Link href={statementReportHref(current.report_id)}>{current.source_ref}</Link>{current.source_sha256 ? ` · SHA-256 ${current.source_sha256}` : " · 来源指纹未提供"}</p> : null}
    </div>
  );
}
