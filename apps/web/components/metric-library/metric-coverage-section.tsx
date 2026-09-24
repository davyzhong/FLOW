"use client";

import { useCallback, useEffect, useState } from "react";

import {
  metricLibraryApi,
  type MetricCoverage,
  type MetricCoverageCell,
  type MetricCoverageSnapshot,
} from "../../lib/api/client";
import { PageState } from "../ui/page-state";

const COMPANY_INITIALS: Record<string, string> = {
  alibaba_9988: "阿",
  cainiao: "菜",
  damai_syn: "麦",
  jd_logistics_2618: "京",
  sf_002352: "顺",
  tencent_0700: "腾",
};

const COVERAGE_COMPANY_NAMES: Record<string, string> = {
  alibaba_9988: "阿里巴巴",
  cainiao: "菜鸟",
  damai_syn: "大麦物流",
  jd_logistics_2618: "京东物流",
  sf_002352: "顺丰控股",
  tencent_0700: "腾讯控股",
};

type CoverageDataset = "public" | "damai";

const DATASET_TABS: { key: CoverageDataset; label: string }[] = [
  { key: "public", label: "真实财报" },
  { key: "damai", label: "大麦演示" },
];

function coverageGrade(ratio: number): { label: string; tier: "a-plus" | "a" | "b-plus" | "b" | "c" } {
  if (ratio >= 0.9) return { label: "A+", tier: "a-plus" };
  if (ratio >= 0.75) return { label: "A", tier: "a" };
  if (ratio >= 0.6) return { label: "B+", tier: "b-plus" };
  if (ratio >= 0.4) return { label: "B", tier: "b" };
  return { label: "C", tier: "c" };
}

function coverageCellKey(snapshot: MetricCoverageSnapshot): string {
  return `${snapshot.company} ${snapshot.period}`;
}

type CoverageLoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; coverage: MetricCoverage };

function coverageCellClass(cell: MetricCoverageCell | undefined): string {
  if (!cell || cell.display === null || cell.display === undefined) {
    return "ml-cov__cell ml-cov__cell--miss";
  }
  // 解析 display：纯数字、百分比、负数、比率/倍
  const text = String(cell.display);
  const numeric = Number(text.replace(/[,%]/g, ""));
  if (Number.isFinite(numeric)) {
    if (text.includes("%")) {
      // 百分比（>=10 绿 / >=0 黄 / <0 红）
      if (numeric >= 10) return "ml-cov__cell ml-cov__cell--ok";
      if (numeric >= 0) return "ml-cov__cell ml-cov__cell--warn";
      return "ml-cov__cell ml-cov__cell--bad";
    }
    if (numeric < 0) return "ml-cov__cell ml-cov__cell--bad";
    if (text.length > 4) return "ml-cov__cell ml-cov__cell--money";
  }
  return "ml-cov__cell ml-cov__cell--neutral";
}

function CoverageSection() {
  const [state, setState] = useState<CoverageLoadState>({ kind: "loading" });
  const [dataset, setDataset] = useState<CoverageDataset>("public");

  const load = useCallback((target: CoverageDataset) => {
    const controller = new AbortController();
    metricLibraryApi.getCoverage(controller.signal, target).then(
      (coverage) => setState({ kind: "loaded", coverage }),
      (error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "加载失败",
        });
      },
    );
    return controller;
  }, []);

  useEffect(() => {
    const controller = load(dataset);
    return () => controller.abort();
  }, [load, dataset]);

  const retry = useCallback(() => {
    setState({ kind: "loading" });
    load(dataset);
  }, [load, dataset]);

  const switchDataset = useCallback((target: CoverageDataset) => {
    setDataset((current) => {
      if (current === target) return current;
      setState({ kind: "loading" });
      return target;
    });
  }, []);

  if (state.kind === "loading") {
    return <PageState status="loading" message="正在读取真实财报覆盖矩阵…" />;
  }
  if (state.kind === "error") {
    return (
      <PageState
        status="error"
        message="覆盖矩阵暂时无法加载"
        detail={state.message}
        retry={retry}
      />
    );
  }

  const { coverage } = state;
  const snapshots = coverage.snapshots;
  const totalCells = snapshots.reduce((sum, s) => sum + s.total, 0);
  const totalComputable = snapshots.reduce((sum, s) => sum + s.computable, 0);
  const overallRatio = totalCells > 0 ? totalComputable / totalCells : 0;
  const best = [...snapshots].sort((a, b) => (b.computable / b.total) - (a.computable / a.total))[0];
  const missCount = totalCells - totalComputable;
  const companyCount = new Set(snapshots.map((s) => s.company)).size;
  const isSynthetic = coverage.synthetic === true;
  // 行级平均：用于给指标打覆盖等级
  const rowGrades = coverage.metrics.map((metric) => {
    const filled = snapshots.filter((s) => {
      const c = metric.cells[coverageCellKey(s)];
      return c && c.display !== null && c.display !== undefined;
    }).length;
    const ratio = snapshots.length > 0 ? filled / snapshots.length : 0;
    return { metric, filled, ratio, grade: coverageGrade(ratio) };
  });
  const worstRow = [...rowGrades].sort((a, b) => a.ratio - b.ratio)[0];

  return (
    <section className="ml-coverage" aria-label="指标覆盖矩阵">
      <header className="ml-hero ml-hero--compact">
        <div className="ml-hero__kicker">
          {isSynthetic ? "synthetic 演示 · 大麦物流" : "真实财报 · 反向解析"}
        </div>
        <h1 className="ml-hero__title">
          指标覆盖<em>矩阵</em>
        </h1>
        <div className="ml-coverage__tabs" role="tablist" aria-label="覆盖数据集切换">
          {DATASET_TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={dataset === tab.key}
              className={
                dataset === tab.key
                  ? "ml-coverage__tab ml-coverage__tab--active"
                  : "ml-coverage__tab"
              }
              onClick={() => switchDataset(tab.key)}
            >
              {tab.label}
            </button>
          ))}
          {isSynthetic ? (
            <span className="ml-coverage__synthetic-badge" role="note">
              合成演示数据
            </span>
          ) : null}
        </div>
        <p className="ml-hero__lede">
          {coverage.title}（<code>{coverage.dataset_id}</code>）：
          通用 {coverage.metrics.length} 指标 × {snapshots.length} 个公司期间快照；
          数值来自 {coverage.facts_source}，
          口径映射见 {coverage.alias_map}，由 {coverage.generator} 生成。
        </p>
      </header>

      <ul className="ml-kpis" aria-label="覆盖矩阵速览">
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">快</span>
          <div>
            <p className="ml-kpi__name">覆盖快照</p>
            <p className="ml-kpi__value">
              {snapshots.length}<small> 个</small>
            </p>
            <p className="ml-kpi__foot">{companyCount} 家公司 · {snapshots.length} 个期间</p>
          </div>
        </li>
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">标</span>
          <div>
            <p className="ml-kpi__name">通用指标</p>
            <p className="ml-kpi__value">{coverage.metrics.length}<small> 个</small></p>
            <p className="ml-kpi__foot">指标库 v0 评审集</p>
          </div>
        </li>
        <li className="ml-kpi ml-kpi--red">
          <span className="ml-kpi__seal" aria-hidden="true">率</span>
          <div>
            <p className="ml-kpi__name">覆盖均值</p>
            <p className="ml-kpi__value">
              {Math.round(overallRatio * 100)}<small>%</small>
            </p>
            <p className="ml-kpi__foot">
              {totalComputable}<small>/</small>{totalCells} 单元格
            </p>
          </div>
        </li>
        {best ? (
          <li className="ml-kpi">
            <span className="ml-kpi__seal" aria-hidden="true">优</span>
            <div>
              <p className="ml-kpi__name">最佳快照</p>
              <p className="ml-kpi__value">
                {best.computable}<small>/</small>{best.total}
              </p>
              <p className="ml-kpi__foot">
                {COVERAGE_COMPANY_NAMES[best.company] ?? best.company} · {best.period}
              </p>
            </div>
          </li>
        ) : null}
        <li className="ml-kpi ml-kpi--red">
          <span className="ml-kpi__seal" aria-hidden="true">缺</span>
          <div>
            <p className="ml-kpi__name">缺口格</p>
            <p className="ml-kpi__value">{missCount}<small> 格</small></p>
            <p className="ml-kpi__foot">逐格标注首个缺失科目</p>
          </div>
        </li>
      </ul>

      <ul className="ml-coverage__notes">
        {coverage.caliber_notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>

      <div className="ml-coverage__scroll">
        <table className="ml-cov">
          <thead>
            <tr>
              <th className="ml-cov__metric" scope="col">指标</th>
              {snapshots.map((snapshot) => {
                const ratio = snapshot.total > 0 ? snapshot.computable / snapshot.total : 0;
                const grade = coverageGrade(ratio);
                return (
                  <th key={coverageCellKey(snapshot)} scope="col" className="ml-cov__col">
                    <span className={`ml-cov__seal ml-cov__seal--${grade.tier}`} aria-hidden="true">
                      {COMPANY_INITIALS[snapshot.company] ?? snapshot.company.slice(0, 1).toUpperCase()}
                    </span>
                    <strong className="ml-cov__company">
                      {COVERAGE_COMPANY_NAMES[snapshot.company] ?? snapshot.company}
                    </strong>
                    <span className="ml-cov__period">{snapshot.period}</span>
                    <span className="ml-cov__ratio">
                      {snapshot.computable}/{snapshot.total}
                    </span>
                    <span className={`ml-cov__bar ml-cov__bar--${grade.tier}`} aria-hidden="true">
                      <span style={{ width: `${Math.round(ratio * 100)}%` }} />
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {coverage.metrics.map((metric) => {
              return (
                <tr key={metric.metric_code}>
                  <th className="ml-cov__metric" scope="row">
                    <code>{metric.metric_code}</code> {metric.name}
                    {metric.unit ? <span className="ml-cov__unit">（{metric.unit}）</span> : null}
                  </th>
                  {snapshots.map((snapshot) => {
                    const key = coverageCellKey(snapshot);
                    const cell = metric.cells[key];
                    if (!cell || cell.display === null || cell.display === undefined) {
                      return (
                        <td
                          key={key}
                          className={coverageCellClass(cell)}
                          title={cell?.missing ? `缺口：${cell.missing}` : undefined}
                        >
                          <span className="ml-cov__miss">缺 {cell?.missing ?? "—"}</span>
                        </td>
                      );
                    }
                    return (
                      <td key={key} className={coverageCellClass(cell)} title={cell.missing ? `首个缺失：${cell.missing}` : undefined}>
                        {cell.display}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
            <tr className="ml-cov__grade-row">
              <th scope="row" className="ml-cov__metric">覆盖等级</th>
              {snapshots.map((snapshot) => {
                const ratio = snapshot.total > 0 ? snapshot.computable / snapshot.total : 0;
                const grade = coverageGrade(ratio);
                return (
                  <td key={`grade-${coverageCellKey(snapshot)}`} className="ml-cov__grade-cell">
                    <span className={`ml-grade ml-grade--${grade.tier}`}>{grade.label}</span>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="ml-verdict" role="note">
        <b>覆盖判断：</b>
        {best ? (
          <>
            最佳 {COVERAGE_COMPANY_NAMES[best.company] ?? best.company} {best.period}
            可计算 {best.computable}/{best.total} 居首；整体均值 {Math.round(overallRatio * 100)}%；
            缺口 {missCount} 格已逐格标注首个缺失科目。
            {worstRow ? (
              <>
                {" "}最弱指标 <code>{worstRow.metric.metric_code}</code> 仅{" "}
                {worstRow.filled}/{snapshots.length} 可计算，
                后续可补 {snapshots.length - worstRow.filled} 家公司期间样本。
              </>
            ) : null}
          </>
        ) : (
          "尚无快照数据。"
        )}
      </div>

      <p className="ml-muted">
        {isSynthetic
          ? "本矩阵为 synthetic 演示数据：重新生成 python scripts/build_damai_metric_coverage.py；真实财报矩阵请切换到「真实财报」。"
          : "覆盖详情与逐格取数说明见 docs/implementation/p5/metric_coverage_matrix.md；重新生成：python scripts/p5_query_facts.py。"}
      </p>
    </section>
  );
}


export { CoverageSection };
