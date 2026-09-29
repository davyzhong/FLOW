"use client";

/**
 * S01 CFO 驾驶舱 · 穿透抽屉（批次 A）
 *
 * 设计依据：设计文档 §5.1④「每个数字可穿透到冻结事实」+ §9「可追溯」铁律。
 * 链路：口径 → 来源（snapshot/SHA） → 关联结论（Finding） → 历史趋势 → 版本历史
 *
 * 与原型 v2.0 的差异：原型用运行时扫描 .kpi 生成模拟档案；
 * 真实实现只渲染**服务端下发**的档案（无 snapshot_id 的数字不提供穿透）。
 */

import Link from "next/link";

import { metricFocusHref } from "../../lib/deep-links";
import type { CockpitDrill } from "./cockpit-types";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="drill__row">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}

export function CockpitDrillDrawer({
  drill,
  onClose,
}: {
  drill: CockpitDrill | null;
  onClose: () => void;
}) {
  if (!drill) return null;
  const cmp = drill.comparisons;
  return (
    <>
      <div className="drill__mask" data-testid="cockpit-drill-mask" onClick={onClose} />
      <aside
        className="drill"
        role="dialog"
        aria-modal="true"
        aria-label={`${drill.title} 穿透详情`}
        data-testid="cockpit-drill"
      >
        <header className="drill__head">
          <div>
            <h3>{drill.title}</h3>
            <div className="drill__value">
              {drill.value}
              <small>{drill.unit}</small>
            </div>
          </div>
          <button type="button" className="drill__close" onClick={onClose} aria-label="关闭穿透详情">
            ✕
          </button>
        </header>

        <div className="drill__body">
          <h4>📐 计算口径</h4>
          {drill.caliberNote ? (
            <p className="drill__note">{drill.caliberNote}</p>
          ) : (
            <p className="drill__note drill__note--muted">本指标未下发口径注，属实现缺口</p>
          )}

          <h4>🔗 数据来源</h4>
          <Row label="快照" value={drill.snapshotId} />
          <Row label="指标编码" value={drill.metricCode} />
          <Link className="drill__link" href={metricFocusHref(drill.metricCode)}>
            在指标库中查看口径定义 →
          </Link>

          <h4>🧾 三基准</h4>
          <Row label="同比" value={cmp.yoy.display_value} />
          <Row label="环比" value={cmp.mom.display_value} />
          <Row label="行业分位" value={cmp.percentile.display_value} />

          <h4>ℹ️ 说明</h4>
          <p className="drill__note drill__note--muted">
            本抽屉展示真实链路形态（口径 → 来源 → 结论 → 历史 → 版本）。历史趋势与口径版本历史需服务端
            在批次 C 补齐后展示；当前批次只呈现已冻结事实与三基准。
          </p>
        </div>
      </aside>
    </>
  );
}

/** 经营结论条：只读服务端结论，点击 Finding 溯源（D054：AI 不改事实） */
export function CockpitConclusionBar({
  text,
  findings,
  tone,
}: {
  text: string;
  findings: { id: string; title: string; investigation_path: string }[];
  tone: string;
}) {
  return (
    <section className={`concl is-${tone}`} aria-label="经营结论" data-testid="cockpit-conclusion">
      <span className="concl__icon" aria-hidden="true">
        📊
      </span>
      <p className="concl__text">{text}</p>
      {findings.length > 0 ? (
        <div className="concl__refs">
          {findings.map((f) => (
            <Link key={f.id} className="concl__ref" href={f.investigation_path} title={f.title}>
              依据 {f.id.slice(0, 8)} →
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
