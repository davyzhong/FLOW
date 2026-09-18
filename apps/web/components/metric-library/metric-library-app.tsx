"use client";

// 指标库（D040）：只读呈现 flow.metric_dictionary.v0-draft 与会计基础数据集。
// 数据全部来自 GET /api/v1/metric-library（版本化 YAML 数据集），页面不修改、不计算口径。
// 视觉走报告风：hero（红顶 + kicker + 大标题）+ KPI 卡带 + 覆盖矩阵热力图 + verdict 条。
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  FlowApiError,
  metricLibraryApi,
  type MetricLibrary,
  type MetricLibraryEntry,
} from "../../lib/api/client";
import { PageState } from "../ui/page-state";
import { CoverageSection } from "./metric-coverage-section";
import { GovernanceSection } from "./metric-governance-section";
import { DependencyGraph } from "./dependency-graph";
import "./metric-library.css";

type Tab =
  | "general"
  | "logistics"
  | "industry"
  | "graph"
  | "relations"
  | "mapping"
  | "accounting"
  | "coverage"
  | "governance";

const TABS: { id: Tab; label: string }[] = [
  { id: "general", label: "通用指标" },
  { id: "logistics", label: "物流行业指标" },
  { id: "industry", label: "行业参考包" },
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

export function coverageGrade(ratio: number): { label: string; tier: "a-plus" | "a" | "b-plus" | "b" | "c" } {
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
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = useCallback(async () => {
    if (!metric.entry_id) return;
    setBusy(true);
    setMessage(null);
    try {
      const draft = await metricLibraryApi.draftChange(metric.entry_id, {
        changes: { [field]: value },
        reason,
      });
      onChanged(`已提交修订草稿 v${draft.version}（待 rule_owner 审批）`);
    } catch (error) {
      setMessage(
        error instanceof FlowApiError
          ? `修订被拒绝（${error.code}）：${error.message}`
          : "修订失败",
      );
    } finally {
      setBusy(false);
    }
  }, [field, metric.entry_id, onChanged, reason, value]);

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
      <button
        type="button"
        className="flow-btn flow-btn--primary"
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
            className="flow-btn"
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

  // 加载/错误态也保留页面 h1（FE-10：错误态缺少稳定页面标题）——统一走 PageState 外壳。
  if (state.kind === "loading") {
    return (
      <div className="metric-library">
        <PageState title="指标库" status="loading" message="正在读取指标库…" />
      </div>
    );
  }
  if (state.kind === "error") {
    return (
      <div className="metric-library">
        <PageState
          title="指标库"
          status="error"
          message="指标库暂时无法加载"
          detail={state.message}
          retry={retry}
        />
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
          通用 {general.length} 指标 + 物流行业 {logistics.length} 指标 +
          {(library.industry_reference_packs ?? []).length} 行业参考包，
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

      {tab === "industry" ? (
        <section className="ml-packs">
          <p className="ml-muted ml-packs__intro">
            行业经营指标目录暂无财报取数源（无经营事实表数据），仅作「该行业看什么」的对标参考与未来行业包 v2
            的提升候选；财务侧基准差异挂接到既有指标的口径与参考基准。
          </p>
          <div className="ml-packs__grid">
            {(library.industry_reference_packs ?? []).map((pack) => (
              <article key={pack.industry_id} className="ml-pack">
                <header className="ml-pack__head">
                  <strong>{pack.name}</strong>
                  <code>{pack.industry_id}</code>
                </header>
                <p className="ml-pack__note">{pack.note}</p>
                {Object.entries(pack.financial_reference ?? {}).length > 0 ? (
                  <dl className="ml-pack__fin">
                    {Object.entries(pack.financial_reference).map(([code, text]) => (
                      <div key={code}>
                        <dt><code>{code}</code></dt>
                        <dd>{text}</dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
                <ul className="ml-pack__ops">
                  {pack.ops_indicators.map((indicator) => (
                    <li key={indicator.code}>
                      <strong>{indicator.name}</strong> <code>{indicator.code}</code>
                      <span>{indicator.meaning}</span>
                    </li>
                  ))}
                </ul>
                <footer className="ml-pack__src">来源：{pack.provenance}</footer>
              </article>
            ))}
          </div>
        </section>
      ) : null}

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
          <table className="flow-table">
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
                <table className="flow-table">
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
