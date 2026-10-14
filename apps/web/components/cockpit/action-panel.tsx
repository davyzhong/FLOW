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

import { useCallback, useState } from "react";

import { useApiQuery } from "../../lib/api/use-api-query";
import type { CockpitActionItemResponse } from "../../lib/api/client";

interface Acknowledgments {
  [itemId: string]: string;
}

export function ActionItemPanel({
  fetchActionItems,
  acknowledgeActionItem,
  initialItems,
}: {
  fetchActionItems: () => Promise<CockpitActionItemResponse[]>;
  acknowledgeActionItem: (
    itemId: string,
  ) => Promise<{ id: string }>;
  initialItems?: CockpitActionItemResponse[];
}) {
  const query = useApiQuery<CockpitActionItemResponse[]>(
    () => fetchActionItems(),
    [],
  );
  const [acknowledged, setAcknowledged] = useState<Acknowledgments>({});
  const items = initialItems ?? query.data ?? [];

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
        <p>本期无行动项；结论确认后由 CFO 在此建立闭环。</p>
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
      <p className="action-panel__notice">
        确认动作仅写入审计账本（不修改行动项本身）；演示数据不构成公开财报能力证明。
      </p>
    </section>
  );
}
