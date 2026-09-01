"use client";

import { useState } from "react";

import type {
  ConclusionInput,
  EvidenceDecisionInput,
  FindingTransitionInput,
  InvestigationContext,
} from "../../lib/api/client";

const DRIVER_LABELS: Record<string, string> = {
  volume_effect: "规模效应",
  mix_effect: "产品结构",
  price_effect: "价格因素",
  rate_effect: "单价变动",
  efficiency_effect: "运营效率",
  revenue_effect: "收入效应",
  gross_margin_effect: "毛利效应",
  variable_cost: "变动成本",
  fixed_cost: "固定成本",
  opex_effect: "期间费用",
  one_off_effect: "一次性损益",
  aging_1_30: "账龄 1–30 天",
  aging_31_60: "账龄 31–60 天",
  aging_61_90: "账龄 61–90 天",
  aging_90_plus: "账龄 90 天以上",
  collection_shortfall: "回款缺口",
  dso_effect: "DSO 变动",
};

const STATUS_LABELS: Record<string, string> = {
  candidate: "待提交",
  in_review: "复核中",
  approved: "已签发",
  rejected: "已退回",
};

const BLOCKER_LABELS: Record<string, string> = {
  finding_not_submitted: "尚未提交复核",
  finding_rejected: "发现已被退回",
  evidence_pending: "存在待确认证据",
  evidence_rejected: "存在被否定证据",
  conclusion_incomplete: "结论四要素尚未完成",
};

const DECISION_LABELS: Record<string, string> = {
  submitted: "提交复核",
  approved: "批准签发",
  rejected: "否定发现",
  returned: "退回修改",
  evidence_verified: "证据已确认",
  evidence_rejected: "证据被否定",
};

export function driverLabel(code: string): string {
  return DRIVER_LABELS[code] ?? code;
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function decimal(value: string): number {
  return Number(value);
}

function formatWan(value: string): string {
  const number = decimal(value);
  if (!Number.isFinite(number)) return value;
  const wan = number / 10000;
  const sign = wan > 0 ? "+" : "";
  return `${sign}${wan.toLocaleString("zh-CN", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  })} 万`;
}

function formatRatio(value: string | null | undefined): string {
  if (!value) return "—";
  const number = decimal(value);
  if (!Number.isFinite(number)) return value;
  return `${(number * 100).toFixed(1)}%`;
}

function driverDirection(amount: string): "is-positive" | "is-negative" | "is-neutral" {
  const number = decimal(amount);
  if (number > 0) return "is-positive";
  if (number < 0) return "is-negative";
  return "is-neutral";
}

export function InvestigationHeader({ context }: { context: InvestigationContext }) {
  const { finding, result } = context;
  const explained = result
    ? formatRatio(
        ((): string => {
          const total = context.drivers.reduce(
            (sum, driver) => sum + Math.abs(decimal(driver.contribution_amount)),
            0,
          );
          const impact = Math.abs(decimal(result.impact_amount));
          return impact > 0 ? String(Math.min(total / impact, 1)) : "0";
        })(),
      )
    : "—";
  const verified = context.evidence.filter((item) => item.status === "verified").length;
  return (
    <section className="investigation-head" aria-label="异常定义与影响">
      <div className="investigation-head__text">
        <h1>{finding.title}</h1>
        <p>
          {finding.fact_statement ?? finding.business_meaning ?? "该发现尚未填写业务解释。"}
        </p>
        <ol className="investigation-review-flow" aria-label="复核流程">
          <li className="is-done">数据通过对账</li>
          <li className="is-done">指标口径锁定</li>
          <li className="is-done">驱动计算完成</li>
          <li className={verified === context.evidence.length ? "is-done" : "is-active"}>
            {context.evidence.length - verified} 项证据待确认
          </li>
          <li className={finding.status === "approved" ? "is-done" : undefined}>
            Finance BP 签发
          </li>
        </ol>
      </div>
      <div className="investigation-head__side">
        <span className={`investigation-badge is-${finding.status}`} data-testid="finding-status">
          {statusLabel(finding.status)}
        </span>
        <dl className="investigation-head-metrics">
          <div>
            <dt>影响金额</dt>
            <dd>{formatWan(finding.impact_amount)}</dd>
          </div>
          <div>
            <dt>已解释比例</dt>
            <dd>{explained}</dd>
          </div>
          <div>
            <dt>证据覆盖</dt>
            <dd>
              {verified} / {context.evidence.length}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

export function InvestigationProcessRail({ context }: { context: InvestigationContext }) {
  const pending = context.evidence.filter((item) => item.status === "pending").length;
  const rejected = context.evidence.filter((item) => item.status === "rejected").length;
  const steps: Array<{ label: string; state: "done" | "active" | "todo" }> = [
    { label: "确认异常", state: "done" },
    { label: "量化影响", state: "done" },
    { label: "驱动拆解", state: "done" },
    {
      label: "证据与复核",
      state: pending + rejected > 0 ? "active" : "done",
    },
    {
      label: "形成结论",
      state: context.conclusion.exists ? "done" : "todo",
    },
    { label: "发布到报告", state: "todo" },
  ];
  return (
    <aside className="investigation-rail" aria-label="调查流程">
      <div className="investigation-rail__brand">
        FL<i>O</i>W
      </div>
      <nav aria-label="调查阶段">
        <p className="investigation-rail__group">调查流程</p>
        {steps.map((step, index) => (
          <p key={step.label} className={`investigation-rail__step is-${step.state}`}>
            <b>{step.state === "done" ? "✓" : index + 1}</b>
            <span>{step.label}</span>
          </p>
        ))}
      </nav>
      <p className="investigation-rail__group">证据状态</p>
      <p className="investigation-rail__step is-done">
        <b>{context.evidence.length - pending - rejected}</b>
        <span>已核验</span>
      </p>
      <p className={`investigation-rail__step ${pending > 0 ? "is-active" : ""}`}>
        <b>{pending}</b>
        <span>待业务确认</span>
      </p>
      <p className={`investigation-rail__step ${rejected > 0 ? "is-active" : ""}`}>
        <b>{rejected}</b>
        <span>被否定</span>
      </p>
    </aside>
  );
}

export function InvestigationDriverTable({
  drivers,
  result,
}: {
  drivers: InvestigationContext["drivers"];
  result: InvestigationContext["result"];
}) {
  return (
    <section className="investigation-panel" aria-label="驱动计算明细">
      <div className="investigation-panel__head">
        <h2>驱动计算明细</h2>
        <small>
          {result
            ? `${result.playbook_code} · ${result.comparison_basis === "budget" ? "对比预算" : "对比上年"}`
            : "无关联分析结果"}
        </small>
      </div>
      {drivers.length > 0 ? (
        <div className="investigation-table-scroll" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th scope="col">驱动</th>
                <th scope="col">计算方法</th>
                <th scope="col">影响金额</th>
                <th scope="col">贡献占比</th>
              </tr>
            </thead>
            <tbody>
              {drivers.map((driver) => (
                <tr key={driver.driver_code}>
                  <th scope="row">{driverLabel(driver.driver_code)}</th>
                  <td>{driver.calculation_method ?? "—"}</td>
                  <td className={driverDirection(driver.contribution_amount)}>
                    {formatWan(driver.contribution_amount)}
                  </td>
                  <td>{formatRatio(driver.contribution_ratio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="investigation-empty">该发现没有可展示的驱动拆解。</p>
      )}
    </section>
  );
}

export function InvestigationDriverBridge({
  drivers,
  result,
}: {
  drivers: InvestigationContext["drivers"];
  result: InvestigationContext["result"];
}) {
  if (!result || drivers.length === 0) {
    return (
      <section className="investigation-panel" aria-label="影响桥">
        <div className="investigation-panel__head">
          <h2>影响桥</h2>
        </div>
        <p className="investigation-empty">分析结果缺失或已降级，无法绘制影响桥。</p>
      </section>
    );
  }
  const max = Math.max(
    ...drivers.map((driver) => Math.abs(decimal(driver.contribution_amount))),
    1,
  );
  return (
    <section className="investigation-panel" aria-label="影响桥">
      <div className="investigation-panel__head">
        <h2>影响桥</h2>
        <small>
          影响合计 {formatWan(result.impact_amount)} · 对账差异{" "}
          {result.reconciliation_difference}（容差 {result.reconciliation_tolerance}）
        </small>
      </div>
      <div className="investigation-bridge">
        {drivers.map((driver) => {
          const height = Math.max(
            Math.round((Math.abs(decimal(driver.contribution_amount)) / max) * 88),
            4,
          );
          return (
            <div className="investigation-bridge__col" key={driver.driver_code}>
              <div
                className={`investigation-bridge__bar ${driverDirection(driver.contribution_amount)}`}
                style={{ height }}
              />
              <small>{driverLabel(driver.driver_code)}</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function InvestigationCheckRow({ context }: { context: InvestigationContext }) {
  const failedReconciliations = context.reconciliations.filter((item) => !item.passed);
  const blockingIssues = context.quality_issues.filter(
    (item) => item.severity === "blocking",
  );
  const warnings = context.quality_issues.filter((item) => item.severity === "warning");
  return (
    <section className="investigation-checks" aria-label="口径与数据检查">
      <div className={`investigation-check ${failedReconciliations.length === 0 ? "is-good" : "is-warn"}`}>
        <strong>{failedReconciliations.length === 0 ? "✓ 对账全部通过" : "! 存在未通过对账"}</strong>
        <span>
          {failedReconciliations.length === 0
            ? `${context.reconciliations.length} 项对账校验通过`
            : failedReconciliations.map((item) => item.reconciliation_code).join("、")}
        </span>
      </div>
      <div className={`investigation-check ${blockingIssues.length === 0 ? "is-good" : "is-warn"}`}>
        <strong>{blockingIssues.length === 0 ? "✓ 无阻断质量问题" : "! 存在阻断质量问题"}</strong>
        <span>
          警告 {warnings.length} 项
          {warnings.length > 0 ? "（已在导入时确认）" : ""}
        </span>
      </div>
      <div
        className={`investigation-check ${
          context.eligibility_blockers.length === 0 ? "is-good" : "is-warn"
        }`}
      >
        <strong>
          {context.eligibility_blockers.length === 0 ? "✓ 具备报告资格" : "! 尚不可进入正式报告"}
        </strong>
        <span>
          {context.eligibility_blockers.length === 0
            ? "全部证据已核验，结论已完成"
            : context.eligibility_blockers
                .map((blocker) => BLOCKER_LABELS[blocker] ?? blocker)
                .join("；")}
        </span>
      </div>
    </section>
  );
}

export function InvestigationSourceRecordsTable({
  records,
}: {
  records: InvestigationContext["source_records"];
}) {
  return (
    <section className="investigation-panel" aria-label="关键源记录">
      <div className="investigation-panel__head">
        <h2>贡献最大的源记录</h2>
        <small>{records.length} 条 · 点击来源查看原始单元格</small>
      </div>
      {records.length > 0 ? (
        <div className="investigation-table-scroll" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th scope="col">期间</th>
                <th scope="col">维度</th>
                <th scope="col">数值（精确）</th>
                <th scope="col">来源</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.fact_id}>
                  <th scope="row">{String(record.month_key).replace(/(\d{4})(\d{2})/, "$1-$2")}</th>
                  <td className="investigation-source-labels">
                    {Object.entries(record.labels).map(([label, value]) => (
                      <span key={label}>
                        {label} {value}
                      </span>
                    ))}
                  </td>
                  <td>
                    {Object.entries(record.values)
                      .filter(([, value]) => value !== "0.0000")
                      .map(([label, value]) => `${label} ${value}`)
                      .join(" · ")}
                  </td>
                  <td>
                    <span className="investigation-source-link" title={record.source_file_name}>
                      {record.sheet_name}!R{record.source_row}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="investigation-empty">暂无可追溯的源记录。</p>
      )}
    </section>
  );
}

export function InvestigationConclusionEditor({
  conclusion,
  blocked,
  blockers,
  busy,
  editorName,
  onSave,
}: {
  conclusion: InvestigationContext["conclusion"];
  blocked: boolean;
  blockers: readonly string[];
  busy: boolean;
  editorName: string;
  onSave: (input: ConclusionInput) => Promise<void>;
}) {
  const [verifiedFacts, setVerifiedFacts] = useState(conclusion.verified_facts);
  const [judgment, setJudgment] = useState(conclusion.analysis_judgment);
  const [openQuestions, setOpenQuestions] = useState(conclusion.open_questions);
  const [recommendation, setRecommendation] = useState(conclusion.recommendation);
  const [saved, setSaved] = useState(false);

  const complete = [verifiedFacts, judgment, openQuestions, recommendation].every(
    (value) => value.trim().length > 0,
  );

  return (
    <section className="investigation-panel investigation-conclusion" aria-label="结构化结论">
      <div className="investigation-panel__head">
        <h2>Finance BP 结论</h2>
        <small>已验证事实 / 分析判断 / 待确认事项 / 建议 · 事实与假设必须分开</small>
      </div>
      <div className="investigation-fields">
        <label>
          <span>已验证事实</span>
          <textarea
            value={verifiedFacts}
            onChange={(event) => {
              setVerifiedFacts(event.target.value);
              setSaved(false);
            }}
            rows={2}
          />
        </label>
        <label>
          <span>分析判断</span>
          <textarea
            value={judgment}
            onChange={(event) => {
              setJudgment(event.target.value);
              setSaved(false);
            }}
            rows={2}
          />
        </label>
        <label>
          <span>仍待确认</span>
          <textarea
            value={openQuestions}
            onChange={(event) => {
              setOpenQuestions(event.target.value);
              setSaved(false);
            }}
            rows={2}
          />
        </label>
        <label>
          <span>管理建议</span>
          <textarea
            value={recommendation}
            onChange={(event) => {
              setRecommendation(event.target.value);
              setSaved(false);
            }}
            rows={2}
          />
        </label>
      </div>
      {blocked ? (
        <p className="investigation-lock" role="status">
          当前 Finding 尚不可进入正式报告：
          {blockers.map((blocker) => BLOCKER_LABELS[blocker] ?? blocker).join("；")}。
        </p>
      ) : (
        <p className="investigation-lock is-ready" role="status">
          全部证据已核验，结论已完整，可提交签发并进入正式报告。
        </p>
      )}
      <button
        type="button"
        disabled={busy || !complete}
        onClick={() => {
          setSaved(false);
          void onSave({
            verified_facts: verifiedFacts,
            analysis_judgment: judgment,
            open_questions: openQuestions,
            recommendation: recommendation,
            editor: editorName,
          }).then(() => setSaved(true));
        }}
      >
        {saved ? "已保存 ✓" : "保存结论"}
      </button>
    </section>
  );
}

export function InvestigationEvidenceInspector({
  context,
  busy,
  onDecision,
}: {
  context: InvestigationContext;
  busy: boolean;
  onDecision: (input: EvidenceDecisionInput, evidenceId: string) => Promise<void>;
}) {
  return (
    <section className="investigation-inspect-card" aria-label="证据复核">
      <h2>证据复核</h2>
      {context.evidence.map((item) => (
        <article key={item.evidence_id} className="investigation-evidence">
          <p className="investigation-evidence__type">
            {item.evidence_type}
            <span className={`investigation-evidence__status is-${item.status}`}>
              {item.status === "verified" ? "已核验" : item.status === "pending" ? "待确认" : "被否定"}
            </span>
          </p>
          <dl>
            <div>
              <dt>对象</dt>
              <dd>{item.object_id}</dd>
            </div>
            {item.evidence_digest ? (
              <div>
                <dt>摘要</dt>
                <dd title={item.evidence_digest}>{item.evidence_digest.slice(0, 12)}…</dd>
              </div>
            ) : null}
          </dl>
          <div className="investigation-evidence__actions">
            {item.status !== "verified" ? (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void onDecision(
                    { decision: "verified", reviewer: "Finance BP", comment: "确认此证据" },
                    item.evidence_id,
                  )
                }
              >
                确认此证据
              </button>
            ) : null}
            {item.status !== "rejected" ? (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void onDecision(
                    { decision: "rejected", reviewer: "Finance BP", comment: "否定此证据" },
                    item.evidence_id,
                  )
                }
              >
                否定
              </button>
            ) : null}
          </div>
        </article>
      ))}
    </section>
  );
}

export function InvestigationReviewActions({
  context,
  busy,
  onTransition,
}: {
  context: InvestigationContext;
  busy: boolean;
  onTransition: (input: FindingTransitionInput) => Promise<void>;
}) {
  const { finding } = context;
  const actions: Array<{ decision: FindingTransitionInput["decision"]; label: string; primary?: boolean }> =
    [];
  if (finding.status === "candidate") {
    actions.push({ decision: "submitted", label: "提交复核", primary: true });
  }
  if (finding.status === "in_review") {
    actions.push({ decision: "approved", label: "批准签发", primary: true });
    actions.push({ decision: "returned", label: "退回修改" });
    actions.push({ decision: "rejected", label: "否定发现" });
  }
  if (finding.status === "approved") {
    actions.push({ decision: "returned", label: "撤回签发" });
  }
  return (
    <section className="investigation-inspect-card" aria-label="审阅操作">
      <h2>审阅操作</h2>
      <div className="investigation-actions">
        {actions.map((action) => (
          <button
            key={action.decision}
            type="button"
            className={action.primary ? "is-primary" : undefined}
            disabled={busy}
            onClick={() =>
              void onTransition({ decision: action.decision, reviewer: "Finance BP" })
            }
          >
            {action.label}
          </button>
        ))}
        {actions.length === 0 ? <p>当前状态无可执行操作。</p> : null}
      </div>
      <div className="investigation-history" aria-label="审阅记录">
        <h3>审阅记录</h3>
        {context.reviews.length === 0 ? (
          <p>暂无审阅记录。</p>
        ) : (
          context.reviews.map((review) => (
            <p key={review.sequence} className="investigation-history__item">
              <b>
                #{review.sequence} {DECISION_LABELS[review.decision] ?? review.decision}
              </b>
              <span>
                {review.reviewer}
                {review.comment ? ` · ${review.comment}` : ""}
              </span>
            </p>
          ))
        )}
      </div>
    </section>
  );
}
