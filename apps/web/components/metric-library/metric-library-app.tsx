"use client";

// 指标库（D040）：只读呈现 flow.metric_dictionary.v0-draft 与会计基础数据集。
// 数据全部来自 GET /api/v1/metric-library（版本化 YAML 数据集），页面不修改、不计算口径。
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  metricLibraryApi,
  type MetricLibrary,
  type MetricLibraryEntry,
} from "../../lib/api/client";
import "./metric-library.css";

type Tab = "general" | "logistics" | "relations" | "mapping" | "accounting";

const TABS: { id: Tab; label: string }[] = [
  { id: "general", label: "通用指标" },
  { id: "logistics", label: "物流行业指标" },
  { id: "relations", label: "勾稽与分解关系" },
  { id: "mapping", label: "取数映射（CAS↔IFRS）" },
  { id: "accounting", label: "会计基础数据" },
];

const TIME_BEHAVIOR_LABELS: Record<string, string> = {
  period_flow: "期间流量",
  point_balance: "时点余额",
  average_balance: "平均余额",
};

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

function MetricCard({ metric, domains }: { metric: MetricLibraryEntry; domains: Record<string, string> }) {
  return (
    <article className="ml-metric">
      <header className="ml-metric__head">
        <strong>{metric.name}</strong>
        <code>{metric.metric_code}</code>
        <span className="ml-chip">{domains[metric.domain] ?? metric.domain}</span>
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
        {metric.migrates_from ? <span>迁移自 {metric.migrates_from}</span> : null}
        {metric.provenance ? <span>来源：{metric.provenance}</span> : null}
      </footer>
    </article>
  );
}

function MetricList({ metrics, domains }: { metrics: MetricLibraryEntry[]; domains: Record<string, string> }) {
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
          <MetricCard key={metric.metric_code} metric={metric} domains={domains} />
        ))}
      </div>
    </section>
  );
}

export function MetricLibraryApp() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
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

  return (
    <div className="metric-library">
      <header className="ml-header">
        <h1>指标库</h1>
        <p>
          {library.dictionary_id}（{library.status} · {library.decision_ref}）：
          通用 {general.length} 指标 + 物流行业 {logistics.length} 指标，
          {library.report_items.length} 项 CAS↔IFRS 取数映射，
          会计基础 {library.accounting.accounts.length} 科目 / {library.accounting.entry_templates.length} 分录模板。
        </p>
        <p className="ml-header__note">
          数据集为版本化 YAML（config/metrics/），口径变更以新版本进入、旧版本保留；本页只读，评审取舍在评审台完成。
        </p>
      </header>

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

      {tab === "general" ? <MetricList metrics={general} domains={library.domains} /> : null}
      {tab === "logistics" ? <MetricList metrics={logistics} domains={library.domains} /> : null}

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
          <table className="ml-table">
            <thead>
              <tr><th>编号</th><th>科目名称</th><th>类别</th><th>余额方向</th><th>状态</th></tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.code}>
                  <td><code>{account.code}</code></td>
                  <td>{account.name}</td>
                  <td>{account.category}</td>
                  <td>{account.balance_side}</td>
                  <td>{account.status}</td>
                </tr>
              ))}
            </tbody>
          </table>

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
    </div>
  );
}
