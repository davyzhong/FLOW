"use client";

import { useState } from "react";

import { flowApi } from "../../lib/api/client";
import type { InvestigationContext } from "../../lib/api/client";

type CopilotAnswer = {
  interaction_id: string;
  outcome: string;
  answer: {
    facts: Array<{ text: string; citations: readonly string[] }>;
    judgments: Array<{ text: string; citations: readonly string[] }>;
    hypotheses: Array<{ text: string; citations: readonly string[] }>;
    questions: Array<{ text: string; citations: readonly string[] }>;
    degradation: string;
  };
};

const SECTION_LABELS: Record<string, string> = {
  facts: "已验证事实",
  judgments: "分析判断",
  hypotheses: "假设（未验证）",
  questions: "待确认问题",
};

export function CopilotPanel({
  context,
  query,
}: {
  context: InvestigationContext;
  query: {
    finding_id: string;
    batch_id?: string | null;
    metric_snapshot_id?: string | null;
    analysis_run_id?: string | null;
  };
}) {
  const [question, setQuestion] = useState("这个发现的主要原因是什么？");
  const [answer, setAnswer] = useState<CopilotAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ask = async () => {
    setBusy(true);
    setError(null);
    try {
      const response = await flowApi.askCopilot(query.finding_id, {
        question,
        actor: "Finance BP",
        batch_id: query.batch_id ?? null,
        metric_snapshot_id: query.metric_snapshot_id ?? null,
        analysis_run_id: query.analysis_run_id ?? null,
      });
      setAnswer(response as CopilotAnswer);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "AI 助手暂时不可用");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="investigation-inspect-card" aria-label="AI 分析助手">
      <h2>AI 分析助手</h2>
      <p className="investigation-copilot-note">
        AI 仅引用当前批次的对象与数值；事实与假设分开呈现。
      </p>
      <label className="investigation-copilot-question">
        <span>向 AI 追问</span>
        <textarea
          value={question}
          rows={2}
          onChange={(event) => setQuestion(event.target.value)}
        />
      </label>
      <button type="button" disabled={busy} onClick={() => void ask()}>
        {busy ? "分析中…" : "生成结构化解读"}
      </button>
      {error ? (
        <p className="investigation-action-error" role="alert">
          {error}
        </p>
      ) : null}
      {answer ? (
        <div className="investigation-copilot-answer" data-testid="copilot-answer">
          {(
            [
              ["facts", answer.answer.facts],
              ["judgments", answer.answer.judgments],
              ["hypotheses", answer.answer.hypotheses],
              ["questions", answer.answer.questions],
            ] as const
          ).map(([key, sections]) =>
            sections.length > 0 ? (
              <div key={key} className={`investigation-copilot-section is-${key}`}>
                <h3>{SECTION_LABELS[key]}</h3>
                {sections.map((section, index) => (
                  <p key={index}>
                    {section.text}
                    {section.citations.length > 0 ? (
                      <span className="investigation-copilot-citations">
                        {section.citations.map((citation) => (
                          <code key={citation}>{citation}</code>
                        ))}
                      </span>
                    ) : null}
                  </p>
                ))}
              </div>
            ) : null,
          )}
          {answer.answer.degradation === "insufficient_data" ? (
            <p className="investigation-lock" role="status">
              数据不足：以上仅列出待确认问题，不构成事实或判断。
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
