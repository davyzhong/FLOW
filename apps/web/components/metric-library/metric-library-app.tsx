"use client";

// 指标库（D040）：只读呈现 flow.metric_dictionary.v0-draft 与会计基础数据集。
// 数据全部来自 GET /api/v1/metric-library（版本化 YAML 数据集），页面不修改、不计算口径。
// 视觉走报告风：hero（红顶 + kicker + 大标题）+ KPI 卡带 + 覆盖矩阵热力图 + verdict 条。
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  FlowApiError,
  metricLibraryApi,
  type MetricCoverage,
  type MetricCoverageCell,
  type MetricCoverageSnapshot,
  type MetricGovernanceEventLine,
  type MetricLibrary,
  type MetricLibraryEntry,
} from "../../lib/api/client";
import { DependencyGraph } from "./dependency-graph";
import "./metric-library.css";

type Tab =
  | "general"
  | "logistics"
  | "graph"
  | "relations"
  | "mapping"
  | "accounting"
  | "coverage"
  | "governance";

const TABS: { id: Tab; label: string }[] = [
  { id: "general", label: "通用指标" },
  { id: "logistics", label: "物流行业指标" },
  { id: "graph", label: "依赖图谱" },
  { id: "relations", label: "勾稽与分解关系" },
  { id: "mapping", label: "取数映射（CAS↔IFRS）" },
  { id: "accounting", label: "会计基础数据" },
  { id: "coverage", label: "真实财报覆盖" },
  { id: "governance", label: "治理记录" },
];

const EXECUTION_LABELS: Record<string, string> = {
  engine: "引擎执行",
  facts: "事实 AST 执行",
  narrative: "叙述定义",
};

const TIME_BEHAVIOR_LABELS: Record<string, string> = {
  period_flow: "期间流量",
  point_balance: "时点余额",
  average_balance: "平均余额",
};

const COMPANY_INITIALS: Record<string, string> = {
  alibaba_9988: "阿",
  cainiao: "菜",
  jd_logistics_2618: "京",
  sf_002352: "顺",
  tencent_0700: "腾",
};

const COVERAGE_COMPANY_NAMES: Record<string, string> = {
  alibaba_9988: "阿里巴巴",
  cainiao: "菜鸟",
  jd_logistics_2618: "京东物流",
  sf_002352: "顺丰控股",
  tencent_0700: "腾讯控股",
};

// 覆盖等级：A+/A/B+/B/C —— 绿/黄/红三档，对应静态站 widget 的 grade 配色。
function coverageGrade(ratio: number): { label: string; tier: "a-plus" | "a" | "b-plus" | "b" | "c" } {
  if (ratio >= 0.9) return { label: "A+", tier: "a-plus" };
  if (ratio >= 0.75) return { label: "A", tier: "a" };
  if (ratio >= 0.6) return { label: "B+", tier: "b-plus" };
  if (ratio >= 0.4) return { label: "B", tier: "b" };
  return { label: "C", tier: "c" };
}

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; library: MetricLibrary };

function matches(metric: MetricLibraryEntry, query: string): boolean {
  if (!query) return true;
  const haystack = [
    metric.metric_code,
    metric.name,
    metric.formula_text,
    metric.definition,
    ...(metric.aliases ?? []),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

const DRAFT_FIELDS = [
  ["caliber", "口径说明"],
  ["benchmark", "参考基准"],
  ["definition", "定义"],
  ["formula_text", "公式（文本）"],
] as const;

function MetricDraftForm({
  metric,
  onChanged,
}: {
  metric: MetricLibraryEntry;
  onChanged: (message: string) => void;
}) {
  const [field, setField] = useState<string>("caliber");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const [operator, setOperator] = useState("finance.bp");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = useCallback(async () => {
    if (!metric.entry_id) return;
    setBusy(true);
    setMessage(null);
    try {
      const draft = await metricLibraryApi.draftChange(metric.entry_id, {
        changes: { [field]: value },
        operator,
        reason,
      });
      await metricLibraryApi.activateChange(draft.id, { operator, reason });
      onChanged(`已合规修订为 v${draft.version}（草稿→验证→生效，审计留痕）`);
    } catch (error) {
      setMessage(
        error instanceof FlowApiError
          ? `修订被拒绝（${error.code}）：${error.message}`
          : "修订失败",
      );
    } finally {
      setBusy(false);
    }
  }, [field, metric.entry_id, onChanged, operator, reason, value]);

  return (
    <div className="ml-draft">
      <select aria-label="修订字段" value={field} onChange={(e) => setField(e.target.value)}>
        {DRAFT_FIELDS.map(([key, label]) => (
          <option key={key} value={key}>{label}</option>
        ))}
      </select>
      <input
        aria-label="修订内容"
        placeholder="新内容"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <input
        aria-label="修订理由"
        placeholder="理由（必填）"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />
      <input
        aria-label="操作者"
        value={operator}
        onChange={(e) => setOperator(e.target.value)}
      />
      <button
        type="button"
        disabled={busy || !value.trim() || !reason.trim()}
        onClick={() => void submit()}
      >
        提交修订
      </button>
      {message ? <p className="ml-draft__message">{message}</p> : null}
    </div>
  );
}

function MetricCard({ metric, domains, onChanged }: { metric: MetricLibraryEntry; domains: Record<string, string>; onChanged?: (message: string) => void }) {
  const [drafting, setDrafting] = useState(false);
  return (
    <article className="ml-metric">
      <header className="ml-metric__head">
        <strong>{metric.name}</strong>
        <code>{metric.metric_code}</code>
        <span className="ml-chip">{domains[metric.domain] ?? metric.domain}</span>
        <span className="ml-chip ml-chip--tier">
          {metric.tier === "core" ? "常用" : "专业"}
        </span>
        {metric.mpm ? <span className="ml-chip ml-chip--mpm">MPM</span> : null}
      </header>
      <p className="ml-metric__definition">{metric.definition}</p>
      <dl className="ml-metric__grid">
        <div><dt>公式</dt><dd>{metric.formula_text}{metric.unit ? `（${metric.unit}）` : ""}</dd></div>
        <div><dt>时间行为</dt><dd>{metric.time_behavior ? (TIME_BEHAVIOR_LABELS[metric.time_behavior] ?? metric.time_behavior) : "—"}</dd></div>
        <div><dt>CAS 取数</dt><dd>{metric.source_cas?.length ? metric.source_cas.join("、") : "—"}</dd></div>
        <div><dt>IFRS 对照</dt><dd>{metric.source_ifrs ?? "—"}</dd></div>
        {metric.depends_on.length > 0 ? (
          <div><dt>依赖指标</dt><dd>{metric.depends_on.map((d) => <code key={d} className="ml-dep">{d}</code>)}</dd></div>
        ) : null}
        {metric.benchmark ? <div><dt>参考基准</dt><dd>{metric.benchmark}</dd></div> : null}
        {metric.analysis_dimensions && metric.analysis_dimensions.length > 0 ? (
          <div><dt>分析维度</dt><dd>{metric.analysis_dimensions.join(" · ")}</dd></div>
        ) : null}
      </dl>
      {metric.caliber ? <p className="ml-metric__caliber">口径：{metric.caliber}</p> : null}
      {metric.mpm && metric.reconciliation ? (
        <p className="ml-metric__caliber">MPM 调节要求：{metric.reconciliation}</p>
      ) : null}
      {metric.decompositions && metric.decompositions.length > 0 ? (
        <ul className="ml-metric__decomp">
          {metric.decompositions.map((d) => (
            <li key={d.name}>{d.name}：{d.formula_text}</li>
          ))}
        </ul>
      ) : null}
      <footer className="ml-metric__foot">
        {metric.execution_kind ? (
          <span className={`ml-exec ml-exec--${metric.execution_kind}`}>
            {EXECUTION_LABELS[metric.execution_kind] ?? metric.execution_kind}
            {metric.execution_detail ? `：${metric.execution_detail}` : ""}
          </span>
        ) : null}
        {metric.migrates_from ? <span>迁移自 {metric.migrates_from}</span> : null}
        {metric.provenance ? <span>来源：{metric.provenance}</span> : null}
        {metric.entry_id && onChanged ? (
          <button
            type="button"
            className="ml-revise"
            onClick={() => setDrafting((open) => !open)}
          >
            {drafting ? "收起修订" : "修订"}
          </button>
        ) : null}
      </footer>
      {drafting && metric.entry_id && onChanged ? (
        <MetricDraftForm metric={metric} onChanged={onChanged} />
      ) : null}
    </article>
  );
}

function MetricList({ metrics, domains, onChanged }: { metrics: MetricLibraryEntry[]; domains: Record<string, string>; onChanged?: (message: string) => void }) {
  const [query, setQuery] = useState("");
  const [mpmOnly, setMpmOnly] = useState(false);
  const visible = useMemo(
    () => metrics.filter((m) => matches(m, query) && (!mpmOnly || m.mpm)),
    [metrics, query, mpmOnly],
  );
  return (
    <section>
      <div className="ml-toolbar">
        <input
          type="search"
          placeholder="搜索编码 / 名称 / 公式…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="搜索指标"
        />
        <label className="ml-toolbar__mpm">
          <input type="checkbox" checked={mpmOnly} onChange={(e) => setMpmOnly(e.target.checked)} />
          仅看 MPM
        </label>
        <span className="ml-toolbar__count">{visible.length} / {metrics.length} 个指标</span>
      </div>
      <div className="ml-metric-list">
        {visible.map((metric) => (
          <MetricCard key={metric.metric_code} metric={metric} domains={domains} onChanged={onChanged} />
        ))}
      </div>
    </section>
  );
}

function GovernanceSection({ metrics }: { metrics: MetricLibraryEntry[] }) {
  const [events, setEvents] = useState<MetricGovernanceEventLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // entry_id 是库内唯一键；metric_code 跨域可重复（如 general/logistics 各有一条 gross_margin）
  const [entryId, setEntryId] = useState(metrics[0]?.entry_id ?? "");
  const [changesText, setChangesText] = useState("{}");
  const [operator, setOperator] = useState("");
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
    if (!operator.trim() || !reason.trim()) {
      setActionError("操作者与理由均为必填（审计要求）。");
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
      const input = { operator: operator.trim(), reason: reason.trim() };
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
          操作者
          <input value={operator} onChange={(e) => setOperator(e.target.value)} placeholder="如：finance-bp" />
        </label>
        <label>
          理由
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="如：更新基准值来源" />
        </label>
        <div className="ml-governance__actions">
          <button type="button" disabled={busy} onClick={() => void runAction("draft")}>
            创建草稿
          </button>
          <button type="button" disabled={busy} onClick={() => void runAction("activate")}>
            激活
          </button>
          <button type="button" disabled={busy} onClick={() => void runAction("retire")}>
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
        <table className="ml-table">
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

  const load = useCallback(() => {
    const controller = new AbortController();
    metricLibraryApi.getCoverage(controller.signal).then(
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
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const retry = useCallback(() => {
    setState({ kind: "loading" });
    load();
  }, [load]);

  if (state.kind === "loading") {
    return <div className="ml-state" role="status">正在读取真实财报覆盖矩阵…</div>;
  }
  if (state.kind === "error") {
    return (
      <div className="ml-state ml-state--error" role="alert">
        <p>覆盖矩阵暂时无法加载</p>
        <p className="ml-state__detail">{state.message}</p>
        <button type="button" onClick={retry}>重试</button>
      </div>
    );
  }

  const { coverage } = state;
  const snapshots = coverage.snapshots;
  const totalCells = snapshots.reduce((sum, s) => sum + s.total, 0);
  const totalComputable = snapshots.reduce((sum, s) => sum + s.computable, 0);
  const overallRatio = totalCells > 0 ? totalComputable / totalCells : 0;
  const best = [...snapshots].sort((a, b) => (b.computable / b.total) - (a.computable / a.total))[0];
  const missCount = totalCells - totalComputable;
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
    <section className="ml-coverage" aria-label="真实财报指标覆盖矩阵">
      <header className="ml-hero ml-hero--compact">
        <div className="ml-hero__kicker">真实财报 · 反向解析</div>
        <h1 className="ml-hero__title">
          指标覆盖<em>矩阵</em>
        </h1>
        <p className="ml-hero__lede">
          {coverage.title}（<code>{coverage.dataset_id}</code>）：
          通用 {coverage.metrics.length} 指标 × {snapshots.length} 个公司期间快照；
          数值来自 P5 反向解析事实库（{coverage.facts_source}），
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
            <p className="ml-kpi__foot">5 家公司 · 15 个期间</p>
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
        覆盖详情与逐格取数说明见 docs/implementation/p5/metric_coverage_matrix.md；
        重新生成：python scripts/p5_query_facts.py。
      </p>
    </section>
  );
}

export function MetricLibraryApp() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [notice, setNotice] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("general");
  const [accountQuery, setAccountQuery] = useState("");

  const load = useCallback(() => {
    const controller = new AbortController();
    metricLibraryApi.get(controller.signal).then(
      (library) => setState({ kind: "loaded", library }),
      (error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ kind: "error", message: error instanceof Error ? error.message : "加载失败" });
      },
    );
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const revised = useCallback((message: string) => {
    setNotice(message);
    setState({ kind: "loading" });
    load();
  }, [load]);

  const retry = useCallback(() => {
    setState({ kind: "loading" });
    load();
  }, [load]);

  if (state.kind === "loading") {
    return <div className="ml-state" role="status">正在读取指标库…</div>;
  }
  if (state.kind === "error") {
    return (
      <div className="ml-state ml-state--error" role="alert">
        <p>指标库暂时无法加载</p>
        <p className="ml-state__detail">{state.message}</p>
        <button type="button" onClick={retry}>重试</button>
      </div>
    );
  }

  const { library } = state;
  const general = library.metrics.filter((m) => m.collection === "general");
  const logistics = library.metrics.filter((m) => m.collection === "logistics");
  const accounts = library.accounting.accounts.filter(
    (a) =>
      !accountQuery ||
      a.code.includes(accountQuery) ||
      a.name.toLowerCase().includes(accountQuery.toLowerCase()),
  );
  const mpmCount = library.metrics.filter((m) => m.mpm).length;

  return (
    <div className="metric-library">
      <header className="ml-hero">
        <div className="ml-hero__kicker">指标库 · 数据驱动决策 ｜ 财务创造价值</div>
        <h1 className="ml-hero__title">
          FLOW 指标体系与<em>真实财报</em>
        </h1>
        <p className="ml-hero__lede">
          {library.dictionary_id}（{library.status} · {library.decision_ref}）——
          通用 {general.length} 指标 + 物流行业 {logistics.length} 指标，
          {library.report_items.length} 项 CAS↔IFRS 取数映射，
          会计基础 {library.accounting.accounts.length} 科目 / {library.accounting.entry_templates.length} 套分录模板。
        </p>
        <p className="ml-hero__note">
          数据集为版本化 YAML（config/metrics/），口径变更以新版本进入、旧版本保留；本页只读，评审取舍在评审台完成。
        </p>
      </header>

      <ul className="ml-kpis" aria-label="指标库速览">
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">通</span>
          <div>
            <p className="ml-kpi__name">通用指标</p>
            <p className="ml-kpi__value">{general.length}<small> 项</small></p>
            <p className="ml-kpi__foot">跨行业可用</p>
          </div>
        </li>
        <li className="ml-kpi ml-kpi--red">
          <span className="ml-kpi__seal" aria-hidden="true">物</span>
          <div>
            <p className="ml-kpi__name">物流行业指标</p>
            <p className="ml-kpi__value">{logistics.length}<small> 项</small></p>
            <p className="ml-kpi__foot">物流口径专属</p>
          </div>
        </li>
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">月</span>
          <div>
            <p className="ml-kpi__name">MPM 月度必备</p>
            <p className="ml-kpi__value">{mpmCount}<small> 项</small></p>
            <p className="ml-kpi__foot">经营分析必看</p>
          </div>
        </li>
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">科</span>
          <div>
            <p className="ml-kpi__name">会计科目</p>
            <p className="ml-kpi__value">{library.accounting.accounts.length}<small> 个</small></p>
            <p className="ml-kpi__foot">{library.accounting.entry_templates.length} 套分录模板</p>
          </div>
        </li>
        <li className="ml-kpi">
          <span className="ml-kpi__seal" aria-hidden="true">映</span>
          <div>
            <p className="ml-kpi__name">CAS↔IFRS 映射</p>
            <p className="ml-kpi__value">{library.report_items.length}<small> 项</small></p>
            <p className="ml-kpi__foot">取数口径留痕</p>
          </div>
        </li>
      </ul>

      {notice ? (
        <p className="ml-notice" role="status">{notice}</p>
      ) : null}

      <nav className="ml-tabs" aria-label="指标库分区">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "is-active" : undefined}
            aria-current={tab === t.id ? "page" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "general" ? <MetricList metrics={general} domains={library.domains} onChanged={revised} /> : null}
      {tab === "logistics" ? <MetricList metrics={logistics} domains={library.domains} onChanged={revised} /> : null}
      {tab === "coverage" ? <CoverageSection /> : null}
      {tab === "governance" && state.kind === "loaded" ? (
        <GovernanceSection metrics={state.library.metrics} />
      ) : null}

      {tab === "graph" ? <DependencyGraph metrics={library.metrics} domains={library.domains} /> : null}

      {tab === "relations" ? (
        <section className="ml-relations">
          {library.relations.map((relation) => (
            <article key={relation.relation} className="ml-relation">
              <header>
                <strong>{relation.name}</strong>
                <code>{relation.relation}</code>
              </header>
              <p className="ml-relation__expr">{relation.expression}</p>
              <p>{relation.note}</p>
              {relation.provenance ? <footer>来源：{relation.provenance}</footer> : null}
            </article>
          ))}
        </section>
      ) : null}

      {tab === "mapping" ? (
        <section>
          <table className="ml-table">
            <thead>
              <tr><th>报表项目</th><th>CAS 行项目</th><th>IFRS 对照</th></tr>
            </thead>
            <tbody>
              {library.report_items.map((item) => (
                <tr key={item.item_id}>
                  <td><code>{item.item_id}</code></td>
                  <td>{item.cas}</td>
                  <td>{item.ifrs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {tab === "accounting" ? (
        <section className="ml-accounting">
          <div className="ml-toolbar">
            <input
              type="search"
              placeholder="搜索科目编号 / 名称…"
              value={accountQuery}
              onChange={(event) => setAccountQuery(event.target.value)}
              aria-label="搜索会计科目"
            />
            <span className="ml-toolbar__count">{accounts.length} / {library.accounting.accounts.length} 个科目</span>
          </div>
          <div className="ml-accounts-grid" role="list" aria-label="会计科目列表">
            {accounts.map((account) => (
              <div key={account.code} className="ml-account" role="listitem">
                <code>{account.code}</code>
                <strong>{account.name}</strong>
                <span className="ml-account__tags">
                  <span className="ml-account__tag">{account.category}</span>
                  <span className="ml-account__tag">{account.balance_side}</span>
                  {account.status !== "current" ? (
                    <span className="ml-account__tag">{account.status}</span>
                  ) : null}
                </span>
              </div>
            ))}
          </div>

          <h2>准则登记册</h2>
          <ul className="ml-standards">
            {library.accounting.standards.map((standard) => (
              <li key={standard.id}>
                <code>{standard.id}</code> {standard.name}
                {standard.issuer ? `（${standard.issuer}）` : ""}
                {standard.note ? <span className="ml-muted"> — {standard.note}</span> : null}
              </li>
            ))}
          </ul>

          <h2>分录模板</h2>
          <div className="ml-entries">
            {library.accounting.entry_templates.map((template) => (
              <details key={template.template_id} className="ml-entry">
                <summary>
                  <strong>{template.scenario}</strong>
                  <code>{template.template_id}</code>
                </summary>
                {template.business_context ? <p className="ml-muted">{template.business_context}</p> : null}
                <table className="ml-table">
                  <tbody>
                    {template.lines.map((line, index) => (
                      <tr key={index}>
                        <td>{line.direction}</td>
                        <td>{line.account}</td>
                        <td>{line.amount_rule}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="ml-muted">
                  {template.standard_ref ? `依据：${template.standard_ref}　` : ""}
                  关联指标：{template.related_metrics.join("、") || "—"}
                </p>
              </details>
            ))}
          </div>

          {library.accounting.known_gaps.length > 0 ? (
            <>
              <h2>已知缺口</h2>
              <ul className="ml-gaps">
                {library.accounting.known_gaps.map((gap) => (
                  <li key={gap}>{gap}</li>
                ))}
              </ul>
            </>
          ) : null}

          {library.accounting.superseded_notes.length > 0 ? (
            <>
              <h2>已取代科目说明</h2>
              <ul className="ml-gaps">
                {library.accounting.superseded_notes.map((note) => (
                  <li key={note.code}><code>{note.code}</code> {note.note}</li>
                ))}
              </ul>
            </>
          ) : null}
        </section>
      ) : null}

      <div className="ml-verdict" role="note">
        <b>核心判断：</b>
        指标字典已完成 {general.length + logistics.length} 项通用与物流指标的版本化沉淀
        （{library.dictionary_id}，{library.status}），
        会计基础 {library.accounting.accounts.length} 科目 / {library.accounting.entry_templates.length} 套分录模板已就绪；
        真实财报侧已打通「抽取 → 勾稽 → 事实库 → 覆盖矩阵」全链路（{library.report_items.length} 项 CAS↔IFRS 取数映射）。
        评审与口径变更走「修订」按钮，留痕至治理记录页。
      </div>
    </div>
  );
}
