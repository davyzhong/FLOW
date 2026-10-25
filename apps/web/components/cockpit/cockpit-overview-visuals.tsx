"use client";

import Link from "next/link";
import { ArrowUpRight, BadgeCheck, Database, FileText, Landmark, WalletCards } from "lucide-react";

import type {
  CockpitModuleResponse,
  CockpitOverviewResponse,
  CockpitProfitabilityMetric,
  CockpitProfitabilityResponse,
} from "../../lib/api/client";
import { metricFocusHref, reportsSnapshotHref } from "../../lib/deep-links";
import { ChartBox, CHART_THEME } from "./charts/echarts-base";
import { buildCombo, type ComboSeries } from "./charts/builders";
import { buildModuleChartOption } from "./charts/module-options";
import { formatFinancialValue } from "./number-format";

export interface CockpitOverviewSupplements {
  profitability: CockpitProfitabilityResponse | null;
  cashflow: CockpitModuleResponse | null;
  expenses: CockpitModuleResponse | null;
  failures?: string[];
}

function trendOption(overview: CockpitOverviewResponse) {
  const allSeries = (overview.trends ?? []).flatMap((trend) => trend.series ?? []);
  const desired = allSeries.filter((series) => ["revenue", "operating_profit"].includes(series.key));
  const chartSeries: ComboSeries[] = desired.flatMap((series) => {
    const points = (series.points ?? []).map((point) => ({
      period: point.period,
      value: point.value / 100_000_000,
      display: formatFinancialValue(point.value / 100_000_000, { unit: "亿元" }),
      status: point.status,
    }));
    if (!points.some((point) => point.status === "ready" && Number.isFinite(point.value))) return [];
    return [{
      key: series.key,
      title: series.title,
      axis: "line",
      unit: "亿元",
      secondaryAxis: series.key === "operating_profit",
      points,
    }];
  });
  return buildCombo(chartSeries);
}

function available(metric: CockpitProfitabilityMetric | undefined): metric is CockpitProfitabilityMetric & { value: string } {
  return Boolean(metric && metric.status === "available" && metric.value !== null && metric.value !== undefined);
}

function metricText(metric: CockpitProfitabilityMetric | undefined, unit: string) {
  if (!available(metric)) return "未发布";
  return formatFinancialValue(metric.value, { metricCode: metric.metric_code, unit });
}

function factor(period: CockpitProfitabilityResponse["periods"] extends (infer P)[] | undefined ? P : never, code: string) {
  return period?.metrics?.find((metric) => metric.metric_code === code);
}

function sourceLink(reportIds: string[] | undefined) {
  const id = reportIds?.[0];
  return id ? `/statements?report=${encodeURIComponent(id)}` : "/statements";
}

function FactBadge({ label }: { label: string }) {
  const names: Record<string, string> = {
    reported: "披露事实",
    derived: "公式计算",
    synthetic_allocation: "合成分配",
    scenario: "情景数据",
  };
  return <span className="overview-fact-badge">{names[label] ?? label}</span>;
}

export function CockpitOverviewVisuals({
  overview,
  supplements,
  loading,
}: {
  overview: CockpitOverviewResponse;
  supplements: CockpitOverviewSupplements | null;
  loading: boolean;
}) {
  const allSeries = (overview.trends ?? []).flatMap((trend) => trend.series ?? []);
  const focusSeries = allSeries.filter((series) => ["revenue", "operating_profit"].includes(series.key));
  const hasFocusFacts = focusSeries.some((series) => series.points?.some((point) => point.status === "ready" && Number.isFinite(point.value)));
  const detailPeriods = [...new Set(allSeries.flatMap((series) => (series.points ?? []).map((point) => point.period)))];
  const snapshotForPeriod = (period: string) => allSeries.flatMap((series) => series.points ?? []).find((point) => point.period === period)?.snapshot_id;
  const chart = trendOption(overview);
  const cashBridge = supplements?.cashflow?.charts?.cash_bridge;
  const expenseStructure = supplements?.expenses?.charts?.expense_structure;
  const expenseComparison = supplements?.expenses?.charts?.expense_comparison;
  const cashOption = cashBridge
    ? buildModuleChartOption(cashBridge, supplements?.cashflow?.unit ?? "百万元")
    : undefined;
  const expenseComparisonPeriods = Array.isArray(expenseComparison?.periods) ? expenseComparison.periods : [];
  const expenseComparisonSeries = expenseComparison?.series && typeof expenseComparison.series === "object"
    ? Object.entries(expenseComparison.series as Record<string, unknown>)
    : [];
  const expenseComparisonReady = expenseComparisonPeriods.length > 0 && expenseComparisonSeries.length > 0;
  const expenseColors: Record<string, string> = {
    销售: CHART_THEME.blue,
    管理: CHART_THEME.gold,
    研发: CHART_THEME.teal,
    财务: CHART_THEME.purple,
  };
  const expenseComparisonOption = expenseComparisonReady ? buildCombo(expenseComparisonSeries.map(([title, values]) => ({
    key: title,
    title,
    axis: "bar" as const,
    stack: "period-expenses",
    color: expenseColors[title],
    unit: expenseComparison?.unit ?? supplements?.expenses?.unit ?? "百万元",
    points: expenseComparisonPeriods.map((period, index) => {
      const rawValue = Array.isArray(values) ? values[index] : null;
      const value = rawValue === null || rawValue === undefined ? Number.NaN : Number(rawValue);
      return {
        period,
        value,
        display: Number.isFinite(value) ? formatFinancialValue(value, { unit: expenseComparison?.unit ?? "百万元" }) : "—",
        status: Number.isFinite(value) ? "ready" : "unavailable",
      };
    }),
  }))) : undefined;
  const expenseOption = expenseComparisonOption ?? (expenseStructure
    ? buildModuleChartOption({ ...expenseStructure, type: "bar" }, supplements?.expenses?.unit ?? "百万元")
    : undefined);
  const profitability = supplements?.profitability;
  const periods = profitability?.periods ?? [];
  const current = periods[periods.length - 1];
  const roe = factor(current, "roe");
  const netMargin = factor(current, "net_margin");
  const turnover = factor(current, "total_asset_turnover");
  const multiplier = factor(current, "equity_multiplier");
  const dupontReady = current?.consistency?.status === "passed"
    && available(roe) && available(netMargin) && available(turnover) && available(multiplier);
  const expenseRows = expenseComparisonReady ? expenseComparisonSeries : Object.entries(expenseStructure?.series ?? {});
  const cashSteps = Object.entries(cashBridge?.steps ?? {});

  return (
    <section className="overview-visuals" aria-label="财务经营分析图表">
      <div className="overview-visuals__primary-grid">
        <article className="overview-panel overview-panel--trend">
          <header className="overview-panel__head">
            <div>
              <span className="overview-kicker">经营表现 · 冻结趋势</span>
              <h2>收入与营业利润</h2>
            </div>
            <span className="overview-period-tag">{focusSeries[0]?.points?.[0]?.period ?? "—"} 至 {focusSeries[0]?.points?.at(-1)?.period ?? "—"}</span>
          </header>
          <p className="overview-panel__note">按 API 已发布期间展示 · 左右轴均为亿元，利润使用独立刻度 · 缺失期间断线，不补零</p>
          {hasFocusFacts ? <ChartBox
            title=""
            sub=""
            option={chart}
            ariaLabel="已发布期间的营业收入与营业利润趋势，单位亿元"
            height={300}
            testId="cockpit-overview-revenue-profit-chart"
            onDataPointClick={({ dataIndex }) => {
              const period = focusSeries[0]?.points?.[dataIndex ?? -1]?.period;
              const snapshotId = period ? snapshotForPeriod(period) : undefined;
              if (snapshotId) window.location.assign(reportsSnapshotHref(snapshotId));
            }}
          /> : null}
          {!hasFocusFacts ? <p className="overview-unavailable">当前筛选期间没有收入与营业利润趋势事实。</p> : null}
          {allSeries.length > 0 ? (
            <details className="overview-data-details">
              <summary>查看全部指标趋势明细与原值</summary>
              <div className="overview-table-scroll"><table aria-label="经营指标趋势原值对照">
                <thead><tr><th>指标</th>{detailPeriods.map((period) => { const snapshotId = snapshotForPeriod(period); return <th key={period}>{snapshotId ? <Link href={reportsSnapshotHref(snapshotId)} aria-label={`${period} 冻结指标快照`}>{period}</Link> : period}</th>; })}</tr></thead>
                <tbody>{allSeries.map((series) => <tr key={series.key} data-testid={`cockpit-overview-trend-row-${series.key}`}>
                  <th scope="row">{series.title}</th>
                  {detailPeriods.map((period) => {
                    const point = series.points?.find((item) => item.period === period);
                    return <td key={period}>{point?.status === "ready" && point.snapshot_id ? <Link href={reportsSnapshotHref(point.snapshot_id)} aria-label={`${period} ${series.title} 冻结指标快照`}>{formatFinancialValue(point.value, { unit: series.unit })}</Link> : point?.status === "ready" ? formatFinancialValue(point.value, { unit: series.unit }) : "—"}</td>;
                  })}
                </tr>)}</tbody>
              </table></div>
            </details>
          ) : null}
        </article>

        <article className="overview-panel overview-panel--cash" data-status={cashOption ? "ready" : loading ? "loading" : "unavailable"}>
          <header className="overview-panel__head">
            <div><span className="overview-kicker">现金流量 · 年度披露</span><h2>经营现金变动桥</h2></div>
            <WalletCards aria-hidden="true" size={20} />
          </header>
          {cashBridge && supplements?.cashflow ? (
            <>
              <p className="overview-panel__note">{supplements.cashflow.period} · {cashBridge.unit} · {cashBridge.identity ?? "现金流披露行逐项勾稽"}</p>
              <ChartBox title="" sub="" option={cashOption} ariaLabel={`${cashBridge.title}，${supplements.cashflow.period}，单位${cashBridge.unit}`} height={246} testId="cockpit-overview-cashflow-chart" />
              <div className="overview-chart-foot">
                {(cashBridge.fact_classes ?? []).map((kind) => <FactBadge key={kind} label={kind} />)}
                <Link href="/cockpit/cashflow">查看现金流明细 <ArrowUpRight size={14} aria-hidden="true" /></Link>
              </div>
              <details className="overview-data-details"><summary>查看现金变动构成</summary>
                <div className="overview-table-scroll"><table aria-label="经营现金变动桥数据明细"><thead><tr><th>现金流项目</th><th>{cashBridge.unit}</th></tr></thead><tbody>
                  {cashSteps.map(([name, value]) => <tr key={name}><th scope="row">{name}</th><td>{formatFinancialValue(value, { unit: cashBridge.unit })}</td></tr>)}
                </tbody></table></div>
              </details>
            </>
          ) : <p className="overview-unavailable">{loading ? "正在读取已发布现金流…" : "尚无可用的已发布现金流披露，暂不绘制现金桥。"}</p>}
        </article>
      </div>

      <div className="overview-visuals__secondary-grid">
        <article className="overview-panel overview-panel--dupont" data-status={dupontReady ? "ready" : loading ? "loading" : "unavailable"}>
          <header className="overview-panel__head">
            <div><span className="overview-kicker">盈利质量 · 数学拆解</span><h2>杜邦分析</h2></div>
            <Landmark aria-hidden="true" size={20} />
          </header>
          <p className="overview-panel__note">{current?.period ?? "—"} · ROE = 净利率 × 总资产周转率 × 权益乘数</p>
          {dupontReady ? (
            <div className="dupont-equation" data-testid="cockpit-overview-dupont">
              <div className="dupont-equation__roe"><span>净资产收益率 ROE</span><strong>{metricText(roe, "ratio")}</strong></div>
              <span className="dupont-equation__operator" aria-hidden="true">=</span>
              <Link className="dupont-equation__factor" href={metricFocusHref("net_margin")}><span>净利率</span><strong>{metricText(netMargin, "ratio")}</strong><small>净利润 ÷ 营业收入</small></Link>
              <span className="dupont-equation__operator" aria-hidden="true">×</span>
              <Link className="dupont-equation__factor" href={metricFocusHref("total_asset_turnover")}><span>总资产周转率</span><strong>{metricText(turnover, "次")}</strong><small>营业收入 ÷ 平均总资产</small></Link>
              <span className="dupont-equation__operator" aria-hidden="true">×</span>
              <Link className="dupont-equation__factor" href={metricFocusHref("equity_multiplier")}><span>权益乘数</span><strong>{metricText(multiplier, "倍")}</strong><small>平均总资产 ÷ 平均净资产</small></Link>
            </div>
          ) : <p className="overview-unavailable">{loading ? "正在读取冻结盈利快照…" : "缺少可勾稽的冻结指标，杜邦因子暂不可用。"}</p>}
          <div className="overview-chart-foot">
            <span className="overview-integrity"><BadgeCheck size={14} aria-hidden="true" />{current?.consistency?.status === "passed" ? "乘积勾稽通过" : "等待已发布口径"}</span>
            <Link href="/cockpit/profitability">查看完整杜邦分析 <ArrowUpRight size={14} aria-hidden="true" /></Link>
          </div>
        </article>

        <article className="overview-panel overview-panel--expenses" data-status={expenseOption ? "ready" : loading ? "loading" : "unavailable"}>
          <header className="overview-panel__head">
            <div><span className="overview-kicker">成本与费用 · 年度披露</span><h2>期间费用结构</h2></div>
            <Database aria-hidden="true" size={20} />
          </header>
          {expenseOption && supplements?.expenses ? (
            <>
          <p className="overview-panel__note">{expenseComparisonReady ? `${expenseComparisonPeriods[0]} 与 ${expenseComparisonPeriods.at(-1)} · ${expenseComparison?.unit ?? supplements?.expenses?.unit ?? "百万元"}` : `${supplements?.expenses?.period ?? "—"} · ${expenseStructure?.unit ?? supplements?.expenses?.unit ?? "百万元"}`} · 仅展示销售、管理、研发、财务四项披露费用，不含营业成本；不推算费用率</p>
              <div className="expense-visual-row">
            <ChartBox title="" sub="" option={expenseOption} ariaLabel={expenseComparisonReady ? `销售、管理、研发、财务四项期间费用年度堆叠对比，${expenseComparisonPeriods.join(" 与 ")}，单位${expenseComparison?.unit ?? supplements?.expenses?.unit ?? "百万元"}` : `${expenseStructure?.title ?? "费用结构"}，${supplements?.expenses?.period ?? "—"}，单位${expenseStructure?.unit ?? supplements?.expenses?.unit ?? "百万元"}`} height={250} testId="cockpit-overview-expense-chart" />
              </div>
          <details className="overview-data-details"><summary>查看费用披露原值</summary>
            <div className="overview-table-scroll"><table aria-label="期间费用披露原值"><thead><tr><th>费用项目</th>{expenseComparisonReady ? expenseComparisonPeriods.map((period) => <th key={period}>{period}（{expenseComparison?.unit ?? supplements?.expenses?.unit ?? "百万元"}）</th>) : <th>{expenseStructure?.unit ?? supplements?.expenses?.unit ?? "百万元"}</th>}</tr></thead><tbody>
              {expenseRows.map(([name, values]) => <tr key={name}><th scope="row">{name}</th>{expenseComparisonReady ? expenseComparisonPeriods.map((period, index) => { const rawValue = Array.isArray(values) ? values[index] : null; return <td key={period}>{formatFinancialValue(rawValue as string | number | null, { unit: expenseComparison?.unit ?? supplements?.expenses?.unit ?? "百万元" })}</td>; }) : <td>{formatFinancialValue(values as string | number | null, { unit: expenseStructure?.unit ?? supplements?.expenses?.unit ?? "百万元" })}</td>}</tr>)}
            </tbody></table></div>
          </details>
              <div className="overview-chart-foot">
                {(expenseStructure?.fact_classes ?? []).map((kind) => <FactBadge key={kind} label={kind} />)}
                <Link href="/cockpit/expenses">查看费用分析 <ArrowUpRight size={14} aria-hidden="true" /></Link>
              </div>
            </>
          ) : <p className="overview-unavailable">{loading ? "正在读取已发布费用数据…" : "尚无可用的已发布费用披露，暂不绘制费用结构。"}</p>}
        </article>
      </div>

      <section className="overview-analysis-entry" aria-label="演示经营分析入口">
        <header><span className="overview-kicker">经营分析 · 演示口径</span><h2>继续查看经营驱动</h2></header>
        <p>以下视图来自大麦物流合成月度经营账套，与上方公开年度披露财报分区呈现；不得将演示分配数据解读为企业真实月度事实。</p>
        <div className="overview-analysis-entry__links">
          <Link href="/" aria-label="查看预算执行、利润桥、产品表现与毛利矩阵">预算执行 · 利润桥 · 产品表现 · 毛利矩阵 <ArrowUpRight size={14} aria-hidden="true" /></Link>
          <Link href="/investigations" aria-label="查看经营调查与账龄相关证据">经营调查 · 账龄相关证据 <ArrowUpRight size={14} aria-hidden="true" /></Link>
          <Link href="/cockpit/working-capital">公开年度营运资金分析 <ArrowUpRight size={14} aria-hidden="true" /></Link>
        </div>
        <small>账龄客户切片尚无独立图表/API；调查页仅展示已有调查与证据，不代表完整账龄明细分析。</small>
      </section>

      {supplements?.failures?.length ? <p className="overview-supplement-warning" role="status">部分披露模块暂不可读取：{supplements.failures.join("、")}。其他可用视图继续展示。</p> : null}
    </section>
  );
}

export function CockpitOverviewSourcePanel({
  overview,
  supplements,
}: {
  overview: CockpitOverviewResponse;
  supplements: CockpitOverviewSupplements | null;
}) {
  return (
    <aside className="overview-source-panel" aria-label="数据来源与口径说明">
      <div className="overview-source-panel__title"><FileText aria-hidden="true" size={18} /><div><strong>数据来源与口径</strong><span>{overview.source_notice ?? "每张图表都保留期间、快照与来源入口"}</span></div></div>
      <div className="overview-source-panel__item"><span>驾驶舱趋势</span><strong>快照 {overview.context.metric_snapshot_id?.slice(0, 8) ?? "—"}</strong><small>{overview.context.as_of_month} · 按当前筛选口径</small></div>
      <div className="overview-source-panel__item"><span>盈利、现金流、费用</span><strong>集团披露口径</strong><small>独立列示各自财报期间，不继承总览筛选条件</small></div>
      <Link href={sourceLink(supplements?.cashflow?.report_ids)}>打开来源财报 <ArrowUpRight size={14} aria-hidden="true" /></Link>
    </aside>
  );
}
