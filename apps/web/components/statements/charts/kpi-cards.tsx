"use client";

// KPI 卡片网格：报告风（圆形首字徽章 + 大数字 + 精确原值）。
// data-testid="statement-kpi" 必须保留（既有测试断言）；
// 展示文本保持原样（"X.XX 亿元"），仅在视觉层加徽章。
import type { ReactNode } from "react";

export type KpiCardDatum = { label: string; display: string; exact: string | null };

function sealChar(label: string): string {
  // 优先取第一个汉字；否则第一个字符
  const trimmed = label.trim();
  if (!trimmed) return "·";
  const first = trimmed[0] ?? "·";
  return first;
}

export function KpiCards({ items }: { items: KpiCardDatum[] }): ReactNode {
  return (
    <dl className="stmt-kpi-grid" aria-label="核心财务指标">
      {items.map((item, index) => (
        <div
          className={index % 5 === 1 ? "stmt-kpi stmt-kpi--red" : "stmt-kpi"}
          data-testid="statement-kpi"
          key={item.label}
        >
          <dt>
            <span className="stmt-kpi__seal" aria-hidden="true">{sealChar(item.label)}</span>
            {item.label}
          </dt>
          <dd title={item.exact ?? undefined}>{item.display}</dd>
        </div>
      ))}
    </dl>
  );
}
