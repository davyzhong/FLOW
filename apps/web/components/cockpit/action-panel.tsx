"use client";

/**
 * 行动项面板（批次 B4）：财务结论闭环的最小载体。
 *
 * - 只读展示行动项列表（GET /api/v1/cockpit/action-items）；
 * - 确认动作（POST …/acknowledge）：后端只写 durable AuditEvent，
 *   不改业务行（安全规格 V1.1.1 §14 裁决 2）——回执后以客户端态标注，
 *   审计账本为持久真源；
 * - 不做通用任务管理（无指派/排期/通知，D001 边界）。
 */

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { useApiQuery } from "../../lib/api/use-api-query";
import type {
  CockpitActionItemCreate,
  CockpitActionItemResponse,
  CockpitConclusionFinding,
} from "../../lib/api/client";

interface Acknowledgments {
  [itemId: string]: string;
}

export function ActionItemPanel({
  fetchActionItems,
  acknowledgeActionItem,
  initialItems,
  createActionItem,
  findings = [],
  snapshotId,
}: {
  fetchActionItems: () => Promise<CockpitActionItemResponse[]>;
  acknowledgeActionItem: (
    itemId: string,
  ) => Promise<{ id: string }>;
  initialItems?: CockpitActionItemResponse[];
  createActionItem?: (payload: CockpitActionItemCreate) => Promise<CockpitActionItemResponse>;
  findings?: CockpitConclusionFinding[];
  snapshotId?: string;
}) {
  const query = useApiQuery<CockpitActionItemResponse[]>(
    () => fetchActionItems(),
    [],
  );
  const [acknowledged, setAcknowledged] = useState<Acknowledgments>({});
  const [creatingFindingId, setCreatingFindingId] = useState<string | null>(null);
  const [createdFindingIds, setCreatedFindingIds] = useState<string[]>([]);
  const [creationError, setCreationError] = useState<string | null>(null);
  const items = initialItems ?? query.data ?? [];
  const pendingFindings = useMemo(() => {
    const existing = new Set([...items.map((item) => item.finding_id), ...createdFindingIds]);
    return findings.filter((finding) => !existing.has(finding.id));
  }, [createdFindingIds, findings, items]);

  const onAcknowledge = useCallback(
    async (itemId: string) => {
      try {
        const receipt = await acknowledgeActionItem(itemId);
        setAcknowledged((prev) => ({ ...prev, [itemId]: receipt.id }));
      } catch {
        setAcknowledged((prev) => ({ ...prev, [itemId]: "failed" }));
      }
    },
    [acknowledgeActionItem],
  );

  const onCreate = useCallback(async (finding: CockpitConclusionFinding) => {
    if (!createActionItem || !snapshotId) return;
    setCreatingFindingId(finding.id);
    setCreationError(null);
    try {
      await createActionItem({
        finding_id: finding.id,
        snapshot_id: snapshotId,
        title: `跟进：${finding.title}`,
        detail: "基于驾驶舱分析发现创建；请进入调查详情补充处理方案。",
      });
      setCreatedFindingIds((previous) => [...previous, finding.id]);
      query.reload();
    } catch (error) {
      setCreationError(error instanceof Error ? error.message : "创建行动项失败");
    } finally {
      setCreatingFindingId(null);
    }
  }, [createActionItem, query.reload, snapshotId]);

  if (query.loading) {
    return (
      <section
        aria-label="行动项"
        data-status="loading"
        className="action-panel"
      >
        <h3>行动项</h3>
        <p>加载中…</p>
      </section>
    );
  }
  if (query.error) {
    return (
      <section aria-label="行动项" data-status="error" className="action-panel">
        <h3>行动项</h3>
        <p role="alert">{query.error}</p>
        <button type="button" onClick={query.reload}>
          重试
        </button>
      </section>
    );
  }
  return (
    <section aria-label="行动项" data-status="ready" className="action-panel">
      <h3>行动项</h3>
      {items.length === 0 ? (
        pendingFindings.length === 0 ? (
          <p>本期无行动项；结论确认后由 CFO 在此建立闭环。</p>
        ) : (
          <div className="action-panel__suggestions">
            <p>以下分析发现可转为行动项，由 CFO 确认创建：</p>
            <ul>
              {pendingFindings.map((finding) => (
                <li key={finding.id}>
                  <div>
                    <strong>{finding.title}</strong>
                    <Link href={finding.investigation_path}>查看调查详情</Link>
                  </div>
                  <button
                    type="button"
                    disabled={!createActionItem || !snapshotId || creatingFindingId !== null}
                    onClick={() => void onCreate(finding)}
                  >
                    {creatingFindingId === finding.id ? "创建中…" : `创建行动项：${finding.title}`}
                  </button>
                </li>
              ))}
            </ul>
            {creationError ? <p role="alert">{creationError}</p> : null}
          </div>
        )
      ) : (
        <ul>
          {items.map((item) => {
            const done = Boolean(acknowledged[item.id]);
            return (
              <li key={item.id} data-testid="action-item">
                <div>
                  <strong>{item.title}</strong>
                  {item.detail ? <span>：{item.detail}</span> : null}
                </div>
                {done ? (
                  <span data-status="acknowledged">
                    已确认（凭证入审计账本）
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => void onAcknowledge(item.id)}
                  >
                    确认
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {createdFindingIds.length > 0 ? <p role="status">行动项已创建，列表已刷新。</p> : null}
      <p className="action-panel__notice">
        确认动作仅写入审计账本（不修改行动项本身）；演示数据不构成公开财报能力证明。
      </p>
    </section>
  );
}
