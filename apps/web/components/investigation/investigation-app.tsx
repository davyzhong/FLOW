"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  FlowApiError,
  flowApi,
} from "../../lib/api/client";
import type {
  ConclusionInput,
  EvidenceDecisionInput,
  FindingTransitionInput,
  InvestigationContext,
  InvestigationQuery,
} from "../../lib/api/client";
import "./investigation.css";
import { CopilotPanel } from "./copilot-panel";
import {
  InvestigationCheckRow,
  InvestigationConclusionEditor,
  InvestigationDriverBridge,
  InvestigationDriverTable,
  InvestigationEvidenceInspector,
  InvestigationHeader,
  InvestigationProcessRail,
  InvestigationReviewActions,
  InvestigationSourceRecordsTable,
} from "./investigation-view";

const ACTION_ERROR_LABELS: Record<string, string> = {
  evidence_pending: "存在待确认证据，批准被拒绝",
  evidence_rejected: "存在被否定证据，批准被拒绝",
  conclusion_incomplete: "结论四要素尚未完成，批准被拒绝",
  invalid_transition: "当前状态不允许该操作",
  investigation_not_found: "未找到该经营发现",
  investigation_identity_mismatch: "数据血缘与驾驶舱上下文不一致",
};

export type InvestigationRequestState =
  | { kind: "loading" }
  | { kind: "error"; message?: string }
  | { kind: "not_found" }
  | { kind: "identity_mismatch"; message: string }
  | { kind: "loaded"; context: InvestigationContext };

export type InvestigationLoad = (
  query: InvestigationQuery,
  signal?: AbortSignal,
) => Promise<InvestigationContext>;

const defaultLoad: InvestigationLoad = (query, signal) =>
  flowApi.getInvestigation(query, signal);

function toMessage(error: unknown): { code: string; message: string } | null {
  if (error instanceof FlowApiError) {
    return { code: error.code, message: error.message };
  }
  return null;
}

export function InvestigationApp({
  query,
  loadInvestigation = defaultLoad,
  editorName = "Finance BP",
}: {
  query: InvestigationQuery;
  loadInvestigation?: InvestigationLoad;
  editorName?: string;
}) {
  const [request, setRequest] = useState<InvestigationRequestState>({ kind: "loading" });
  const [requestKey, setRequestKey] = useState(0);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    loadInvestigation(query, controller.signal).then(
      (context) => {
        if (!controller.signal.aborted) setRequest({ kind: "loaded", context });
      },
      (error: unknown) => {
        if (controller.signal.aborted) return;
        const typed = toMessage(error);
        if (typed?.code === "investigation_not_found") {
          setRequest({ kind: "not_found" });
        } else if (typed?.code === "investigation_identity_mismatch") {
          setRequest({ kind: "identity_mismatch", message: typed.message });
        } else {
          setRequest({ kind: "error", message: typed?.message });
        }
      },
    );
    return () => controller.abort();
  }, [loadInvestigation, query, requestKey]);

  const refresh = useCallback(() => {
    setRequestKey((value) => value + 1);
  }, []);

  const act = useCallback(
    async (operation: () => Promise<unknown>) => {
      setBusy(true);
      setActionError(null);
      try {
        await operation();
        refresh();
      } catch (error) {
        const typed = toMessage(error);
        setActionError(
          typed
            ? (ACTION_ERROR_LABELS[typed.code] ?? typed.message)
            : "操作失败，请稍后重试",
        );
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const onEvidenceDecision = useCallback(
    (input: EvidenceDecisionInput, evidenceId: string) =>
      act(() => flowApi.decideEvidence(query.finding_id, evidenceId, input)),
    [act, query.finding_id],
  );

  const onTransition = useCallback(
    (input: FindingTransitionInput) =>
      act(() => flowApi.transitionFinding(query.finding_id, input)),
    [act, query.finding_id],
  );

  const onConclusionSave = useCallback(
    (input: ConclusionInput) => act(() => flowApi.saveConclusion(query.finding_id, input)),
    [act, query.finding_id],
  );

  return (
    <main className="investigation-app">
      {request.kind === "loading" ? (
        <section className="investigation-state" role="status">
          <h1>经营调查</h1>
          <p>正在加载证据与复核上下文…</p>
        </section>
      ) : null}
      {request.kind === "error" ? (
        <section className="investigation-state" role="alert">
          <h1>经营调查</h1>
          <p>{request.message ?? "调查上下文暂时无法加载"}</p>
          <button type="button" onClick={refresh}>重试</button>
        </section>
      ) : null}
      {request.kind === "not_found" ? (
        <section className="investigation-state" role="alert">
          <h1>经营调查</h1>
          <p>未找到该经营发现，可能已被修订或不存在。</p>
          <Link className="investigation-state__back" href="/">返回经营驾驶舱</Link>
        </section>
      ) : null}
      {request.kind === "identity_mismatch" ? (
        <section className="investigation-state" role="alert">
          <h1>经营调查</h1>
          <p>{request.message}</p>
          <p>请从经营驾驶舱重新进入，以确保在正确的批次、快照和分析运行上复核证据。</p>
          <Link className="investigation-state__back" href="/">返回经营驾驶舱</Link>
        </section>
      ) : null}
      {request.kind === "loaded" ? (
        <InvestigationWorkspace
          context={request.context}
          query={query}
          busy={busy}
          actionError={actionError}
          editorName={editorName}
          onEvidenceDecision={onEvidenceDecision}
          onTransition={onTransition}
          onConclusionSave={onConclusionSave}
        />
      ) : null}
    </main>
  );
}

function InvestigationWorkspace({
  context,
  query,
  busy,
  actionError,
  editorName,
  onEvidenceDecision,
  onTransition,
  onConclusionSave,
}: {
  context: InvestigationContext;
  query: InvestigationQuery;
  busy: boolean;
  actionError: string | null;
  editorName: string;
  onEvidenceDecision: (input: EvidenceDecisionInput, evidenceId: string) => Promise<void>;
  onTransition: (input: FindingTransitionInput) => Promise<void>;
  onConclusionSave: (input: ConclusionInput) => Promise<void>;
}) {
  return (
    <>
      <header className="investigation-topbar">
        <Link className="investigation-topbar__back" href="/" aria-label="返回经营驾驶舱">
          ← 返回经营驾驶舱
        </Link>
        <span>FLOW · FINANCE INTELLIGENCE</span>
      </header>
      <div className="investigation-frame">
        <InvestigationProcessRail context={context} />
        <section className="investigation-main">
          <InvestigationHeader context={context} />
          <InvestigationDriverTable drivers={context.drivers} result={context.result} />
          <InvestigationDriverBridge drivers={context.drivers} result={context.result} />
          <InvestigationCheckRow context={context} />
          <InvestigationSourceRecordsTable records={context.source_records} />
          <InvestigationConclusionEditor
            conclusion={context.conclusion}
            blocked={context.eligibility_blockers.length > 0}
            blockers={context.eligibility_blockers}
            busy={busy}
            editorName={editorName}
            onSave={onConclusionSave}
          />
          {actionError ? (
            <p className="investigation-action-error" role="alert">{actionError}</p>
          ) : null}
        </section>
        <aside className="investigation-inspector">
          <InvestigationEvidenceInspector
            context={context}
            busy={busy}
            onDecision={onEvidenceDecision}
          />
          <InvestigationReviewActions
            context={context}
            busy={busy}
            onTransition={onTransition}
          />
          <CopilotPanel context={context} query={query} />
        </aside>
      </div>
      <dl
        className="investigation-identity-note"
        role="region"
        aria-label="不可变分析上下文"
        data-testid="investigation-identity"
      >
        <div>
          <dt>Finding ID</dt>
          <dd>{context.identity.finding_id}</dd>
        </div>
        <div>
          <dt>数据批次 ID</dt>
          <dd>{query.batch_id ?? context.identity.batch_id}</dd>
        </div>
        <div>
          <dt>指标快照 ID</dt>
          <dd>{query.metric_snapshot_id ?? context.identity.metric_snapshot_id}</dd>
        </div>
        <div>
          <dt>分析运行 ID</dt>
          <dd>{query.analysis_run_id ?? context.identity.analysis_run_id}</dd>
        </div>
      </dl>
    </>
  );
}
